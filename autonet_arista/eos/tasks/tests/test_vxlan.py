import pytest

from autonet.core.objects import vxlan as an_vxlan

from autonet_arista.eos.tasks import vxlan as vxlan_task


@pytest.mark.parametrize('vnid, expected', [
    (None, [
        an_vxlan.VXLAN(id=70002, source_address='192.168.0.101', layer=2, import_targets=['65002:70002'],
                       export_targets=['65002:70002'], route_distinguisher='198.18.0.101:72', bound_object_id=72),
        an_vxlan.VXLAN(id=70001, source_address='192.168.0.101', layer=2, import_targets=['65002:70001'],
                       export_targets=['65002:70001', '65002:10000'], route_distinguisher='198.18.0.101:71',
                       bound_object_id=71),
        an_vxlan.VXLAN(id=20000, source_address='192.168.0.101', layer=3,
                       import_targets=['65002:20000', '65002:255555'],
                       export_targets=['65002:20000', '65002:255555'],
                       route_distinguisher='198.18.0.101:4094',
                       bound_object_id='red'),
        an_vxlan.VXLAN(id=20001, source_address='192.168.0.101', layer=3, import_targets=['65002:20001'],
                       export_targets=['65002:20001'], route_distinguisher='198.18.0.101:4091',
                       bound_object_id='blue')
    ]),
    (20000, [
        an_vxlan.VXLAN(id=20000, source_address='192.168.0.101', layer=3,
                       import_targets=['65002:20000', '65002:255555'],
                       export_targets=['65002:20000', '65002:255555'],
                       route_distinguisher='198.18.0.101:4094',
                       bound_object_id='red')
    ])
])
def test_get_vxlans(vnid, expected, test_show_int_vxlan, test_bgp_text_config):
    assert vxlan_task.get_vxlans(
        test_show_int_vxlan,
        test_bgp_text_config,
        vnid) == expected


def test_generate_l2_vxlan_create_commands():
    test_vxlan = an_vxlan.VXLAN(
        id=70002, layer=2, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='auto', bound_object_id=72)
    expected = [
        'interface vxlan1',
        'vxlan vlan 72 vni 70002'
    ]
    commands = vxlan_task.generate_l2_vxlan_create_commands(test_vxlan)
    assert commands == expected


def test_generate_l3_vxlan_create_commands():
    test_vxlan = an_vxlan.VXLAN(
        id=20000, layer=3, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='198.18.0.101:4094', bound_object_id='red')
    expected = [
        'interface vxlan1',
        'vxlan vrf red vni 20000'
    ]
    commands = vxlan_task.generate_l3_vxlan_create_commands(test_vxlan)
    assert commands == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(
        id=70002, layer=2, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='auto', bound_object_id=72),
     [
         'interface vxlan1',
         'vxlan vlan 72 vni 70002'
     ]),
    (an_vxlan.VXLAN(
        id=20000, layer=3, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='198.18.0.101:4094', bound_object_id='red'),
     [
         'interface vxlan1',
         'vxlan vrf red vni 20000'
     ])
])
def test_generate_vxlan_commands(test_vxlan, expected):
    assert vxlan_task.generate_vxlan_commands(test_vxlan) == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(
        id=70002, layer=2, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='auto', bound_object_id=72),
     [
         'router bgp 65002',
         'vlan 72',
         'redistribute learned',
         'rd 198.18.0.101:72',
         'route-target import evpn 65002:70002',
         'route-target export evpn 65002:70002'
     ]),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', '65002:70001'],
        export_targets=['65002:70005'], route_distinguisher='198.18.0.1:5',
        bound_object_id=71),
     [
         'router bgp 65002',
         'vlan 71',
         'redistribute learned',
         'rd 198.18.0.1:5',
         'route-target import evpn 65002:70005',
         'route-target import evpn 65002:70001',
         'route-target export evpn 65002:70005'
     ]),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', 'auto'],
        export_targets=['65002:70005', 'auto'],
        route_distinguisher='198.18.0.1:5', bound_object_id=71),
     [
         'router bgp 65002',
         'vlan 71',
         'redistribute learned',
         'rd 198.18.0.1:5',
         'route-target import evpn 65002:70005',
         'route-target import evpn 65002:70001',
         'route-target export evpn 65002:70005',
         'route-target export evpn 65002:70001'
     ])
])
def test_generate_l2_vxlan_evpn_commands(
        test_vxlan, expected, test_show_int_vxlan, test_bgp_config):
    commands = vxlan_task.generate_l2_vxlan_evpn_commands(
        test_vxlan, test_show_int_vxlan, test_bgp_config)
    assert commands == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(
        id=20000, layer=3, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='198.18.0.101:4094', bound_object_id='red'),
     [
         'router bgp 65002',
         'vrf red',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4094',
         'route-target import evpn 65002:20000',
         'route-target export evpn 65002:20000'
     ]),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['65002:20001', '65002:20010', '65000:50'],
        export_targets=['65002:20001', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     [
         'router bgp 65002',
         'vrf blue',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4093',
         'route-target import evpn 65002:20001',
         'route-target import evpn 65002:20010',
         'route-target import evpn 65000:50',
         'route-target export evpn 65002:20001',
         'route-target export evpn 65002:20010'
     ]),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['auto', '65000:50'],
        export_targets=['auto', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     [
         'router bgp 65002',
         'vrf blue',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4093',
         'route-target import evpn 65000:50',
         'route-target import evpn 65002:20001',
         'route-target export evpn 65002:20010',
         'route-target export evpn 65002:20001'
     ])
])
def test_generate_l3_vxlan_evpn_commands(
        test_vxlan, expected, test_show_int_vxlan, test_bgp_config):
    commands = vxlan_task.generate_l3_vxlan_evpn_commands(
        test_vxlan, test_show_int_vxlan, test_bgp_config)
    assert commands == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(
        id=70002, layer=2, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='auto', bound_object_id=72),
     [
         'router bgp 65002',
         'vlan 72',
         'redistribute learned',
         'rd 198.18.0.101:72',
         'route-target import evpn 65002:70002',
         'route-target export evpn 65002:70002'
     ]),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', '65002:70002'],
        export_targets=['65002:70005'], route_distinguisher='198.18.0.1:5',
        bound_object_id=71),
     [
         'router bgp 65002',
         'vlan 71',
         'redistribute learned',
         'rd 198.18.0.1:5',
         'route-target import evpn 65002:70005',
         'route-target import evpn 65002:70002',
         'route-target export evpn 65002:70005'
     ]),
    (an_vxlan.VXLAN(
        id=70001, layer=2, import_targets=['65002:70005', 'auto'],
        export_targets=['65002:70005', 'auto'],
        route_distinguisher='198.18.0.1:5', bound_object_id=71),
     [
         'router bgp 65002',
         'vlan 71',
         'redistribute learned',
         'rd 198.18.0.1:5',
         'route-target import evpn 65002:70005',
         'route-target import evpn 65002:70001',
         'route-target export evpn 65002:70005',
         'route-target export evpn 65002:70001'
     ]),
    (an_vxlan.VXLAN(
        id=20000, layer=3, import_targets=['auto'], export_targets=['auto'],
        route_distinguisher='198.18.0.101:4094', bound_object_id='red'),
     [
         'router bgp 65002',
         'vrf red',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4094',
         'route-target import evpn 65002:20000',
         'route-target export evpn 65002:20000'
     ]),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['65002:20001', '65002:20010', '65000:50'],
        export_targets=['65002:20001', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     [
         'router bgp 65002',
         'vrf blue',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4093',
         'route-target import evpn 65002:20001',
         'route-target import evpn 65002:20010',
         'route-target import evpn 65000:50',
         'route-target export evpn 65002:20001',
         'route-target export evpn 65002:20010'
     ]),
    (an_vxlan.VXLAN(
        id=20001, layer=3, import_targets=['auto', '65000:50'],
        export_targets=['auto', '65002:20010'],
        route_distinguisher='auto', bound_object_id='blue'),
     [
         'router bgp 65002',
         'vrf blue',
         'redistribute connected',
         'redistribute attached-host',
         'redistribute static',
         'rd 198.18.0.101:4093',
         'route-target import evpn 65000:50',
         'route-target import evpn 65002:20001',
         'route-target export evpn 65002:20010',
         'route-target export evpn 65002:20001'
     ])
])
def test_generate_vxlan_evpn_commands(
        test_vxlan, expected, test_show_int_vxlan, test_bgp_text_config):
    commands = vxlan_task.generate_vxlan_evpn_commands(
        test_vxlan, test_show_int_vxlan, test_bgp_text_config)
    assert commands == expected


@pytest.mark.parametrize('test_vxlan, expected', [
    (an_vxlan.VXLAN(id=70002, source_address='192.168.0.101', layer=2,
                    import_targets=['65002:70002'], export_targets=['65002:70002'],
                    route_distinguisher='198.18.0.101:72', bound_object_id=72),
     [
         'interface vxlan1',
         'no vxlan vlan 72 vni 70002',
         'router bgp 65002',
         'no vlan 72'
     ]),
    (an_vxlan.VXLAN(id=20000, source_address='192.168.0.101', layer=3,
                    import_targets=['65002:20000', '65002:255555'],
                    export_targets=['65002:20000', '65002:255555'],
                    route_distinguisher='198.18.0.101:4094',
                    bound_object_id='red'),
     [
         'interface vxlan1',
         'no vxlan vrf red vni 20000',
         'router bgp 65002',
         'vrf red',
         'no redistribute attached-host'
     ])
])
def test_generate_vxlan_delete_commands(test_vxlan, expected, test_bgp_text_config):
    commands = vxlan_task.generate_vxlan_delete_commands(
        test_vxlan, test_bgp_text_config)
    assert commands == expected
