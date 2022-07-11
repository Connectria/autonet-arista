import pytest

from autonet.core.objects import vxlan as an_vxlan

from autonet_arista.eos.tasks import common as common_task


@pytest.mark.parametrize('test_name, expected', [
    ('Port-c22', 'Port-Channel22'),
    ('e52/1', 'Ethernet52/1'),
    ('vl101', 'Vlan101'),
    ('ma1', 'Management1'),
    ('Tun55', 'Tunnel55')
])
def test_get_fq_if_name(test_name, expected):
    assert common_task.get_fq_if_name(test_name) == expected


@pytest.mark.parametrize('test_name, expected', [
    ('Po22', ('Port-Channel', '22')),
    ('Ethernet55/1', ('Ethernet', '55/1')),
    ('vl88', ('Vlan', '88')),
    ('Tun10', ('Tunnel', '10'))
])
def test_get_if_parts(test_name, expected):
    assert common_task.get_if_parts(test_name) == expected


@pytest.mark.parametrize('test_name', ['v55', 'fake22'])
def test_get_fq_if_name_error(test_name):
    with pytest.raises(ValueError) as exc:
        common_task.get_fq_if_name(test_name)


def test_parse_bgp_evpn_vxlan_config(test_bgp_text_config, test_bgp_config):
    cfg = common_task.parse_bgp_vpn_config(test_bgp_text_config)
    assert cfg == test_bgp_config


@pytest.mark.parametrize('test_vxlan, expected_imports, expected_exports', [
    (an_vxlan.VXLAN(
        id=70002, layer=2, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='auto', bound_object_id=72),
     ['route-target import evpn 65002:70002'],
     ['route-target export evpn 65002:70002']),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', '65002:70002'],
        export_targets=['65002:70005'], route_distinguisher='198.18.0.1:5',
        bound_object_id=71),
     ['route-target import evpn 65002:70005', 'route-target import evpn 65002:70002'],
     ['route-target export evpn 65002:70005']),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', 'auto'],
        export_targets=['65002:70005', 'auto'],
        route_distinguisher='198.18.0.1:5', bound_object_id=71),
     ['route-target import evpn 65002:70005', 'route-target import evpn 65002:70001'],
     ['route-target export evpn 65002:70005', 'route-target export evpn 65002:70001']),
    (an_vxlan.VXLAN(
        id=20000, layer=3, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='198.18.0.101:4094', bound_object_id='red'),
     ['route-target import evpn 65002:20000'],
     ['route-target export evpn 65002:20000']),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['65002:20001', '65002:20010', '65000:50'],
        export_targets=['65002:20001', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     ['route-target import evpn 65002:20001', 'route-target import evpn 65002:20010',
      'route-target import evpn 65000:50'],
     ['route-target export evpn 65002:20001', 'route-target export evpn 65002:20010']),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['auto', '65000:50'],
        export_targets=['auto', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     ['route-target import evpn 65000:50', 'route-target import evpn 65002:20001'],
     ['route-target export evpn 65002:20010', 'route-target export evpn 65002:20001'])
])
def test_generate_rt_commands(test_vxlan, expected_imports, expected_exports):
    assert common_task.generate_rt_commands(
        test_vxlan, 65002) == (expected_imports, expected_exports)
