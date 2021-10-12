#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import itertools

from neutron.conf.services import provider_configuration
from oslo_config import cfg


BGPVPN_CONFIG_OPTS = [
    cfg.StrOpt('region_asn',
               default=None,
               help='The unique region 4-byte ASn identifier for'
                    'import/export/route targets. Should be in dotted notation'
                    ' <ASN>.<Number>'),
    cfg.StrOpt('target_id_range',
               default='300-1000',
               help='The range of unique numbers for import/export/route '
                    'targets'),
    cfg.BoolOpt('import_target_auto_allocation',
                default=False,
                help='This option enables auto-allocation for import targets'
                     'for a new bgpvpns created with empty import_targets '
                     'field.'),
    cfg.BoolOpt('export_target_auto_allocation',
                default=False,
                help='This option enables auto-allocation for export targets'
                     'for a new bgpvpns created with empty export_targets '
                     'field.'),
    cfg.BoolOpt('route_target_auto_allocation',
                default=False,
                help='This option enables auto-allocation for route targets'
                     'for a new bgpvpns created with empty route_targets '
                     'field.'),
]


def register_bgpvpn_options(cfg=cfg.CONF):
    cfg.register_opts(BGPVPN_CONFIG_OPTS, group='bgpvpn')


def list_bgpvpn_opts():
    return [
        ('bgpvpn', itertools.chain(
            BGPVPN_CONFIG_OPTS)),
    ]


def list_service_provider():
    return [
        ('service_providers', provider_configuration.serviceprovider_opts),
    ]


_dummy_bgpvpn_provider = ':'.join([
    'BGPVPN', 'Dummy',
    'networking_bgpvpn.neutron.services.service_drivers.driver_api.'
    'BGPVPNDriver',
    'default'
])


# Set reasonable example for BGPVPN as a default value
def set_service_provider_default():
    cfg.set_defaults(provider_configuration.serviceprovider_opts,
                     service_provider=[_dummy_bgpvpn_provider])
