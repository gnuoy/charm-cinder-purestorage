#!/usr/bin/env python3

# Copyright 2019 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Encapsulate cinder-purestorage testing."""

import logging
import uuid

import zaza.model
import zaza.charm_tests.test_utils as test_utils
import zaza.utilities.openstack as openstack_utils


class CinderpurestorageTest(test_utils.OpenStackBaseTest):
    """Encapsulate purestorage tests."""

    @classmethod
    def setUpClass(cls):
        """Run class setup for running tests."""
        super(CinderpurestorageTest, cls).setUpClass()
        cls.keystone_session = openstack_utils.get_overcloud_keystone_session()
        cls.model_name = zaza.model.get_juju_model()
        cls.cinder_client = openstack_utils.get_cinder_session_client(
            cls.keystone_session)

    def test_cinder_config(self):
        logging.info('purestorage')
        expected_contents = {
            'cinder-purestorage': {
                'san_ip': ['10.243.19.250'],
                'pure_api_token': ['ac0a534f-b682-777a-45a4-15a02e0d5c7e'],
                'volume_driver':
                    ['cinder.volume.drivers.pure.PureISCSIDriver'],
                'volume_backend_name': ['cinder-pure']
            }
        }

        zaza.model.run_on_leader(
            'cinder',
            'sudo cp /etc/cinder/cinder.conf /tmp/',
            model_name=self.model_name)
        zaza.model.block_until_oslo_config_entries_match(
            'cinder',
            '/tmp/cinder.conf',
            expected_contents,
            model_name=self.model_name,
            timeout=2)

    def test_create_volume(self):
        test_vol_name = "zaza{}".format(uuid.uuid1().fields[0])
        vol_new = self.cinder_client.volumes.create(
            name=test_vol_name,
            size=2)
        openstack_utils.resource_reaches_status(
            self.cinder_client.volumes,
            vol_new.id,
            expected_status='available')
        test_vol = self.cinder_client.volumes.find(name=test_vol_name)
        self.assertEqual(
            getattr(test_vol, 'os-vol-host-attr:host').split('#')[0],
            'cinder@cinder-purestorage')
        self.cinder_client.volumes.delete(vol_new)
