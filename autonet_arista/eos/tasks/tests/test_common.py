import pytest

from autonet_arista.eos.tasks import common as common_task


def test_parse_bgp_evpn_vxlan_config(test_bgp_text_config):
    cfg = common_task.parse_bgp_evpn_vxlan_config(test_bgp_text_config)
    assert cfg == {
        'asn': '65002',
        'rid': '198.18.0.101',
        'vlans': {
            '71': {
                'export_targets': ['65002:70001', '65002:10000'],
                'import_targets': ['65002:70001'],
                'rd': '198.18.0.101:71'
            },
            '72': {
                'export_targets': ['65002:70002'],
                'import_targets': ['65002:70002'],
                'rd': '198.18.0.101:72'
            }
        },
        'vrfs': {
            'blue': {
                'export_targets': ['65002:20001'],
                'import_targets': ['65002:20001'],
                'rd': '198.18.0.101:4091',
                'rid': '198.18.0.101'
            },
            'red': {
                'export_targets': ['65002:20000', '65002:255555'],
                'import_targets': ['65002:20000', '65002:255555'],
                'rd': '198.18.0.101:4094'
            }
        }
    }
