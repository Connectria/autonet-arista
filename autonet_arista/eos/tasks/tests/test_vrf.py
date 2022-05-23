import pytest

from autonet_ng.core.objects import vrf as an_vrf

from autonet_arista.eos.tasks import vrf as vrf_task


@pytest.mark.parametrize('vrf, expected', [
    (
            None,
            [
                an_vrf.VRF(
                    name='blue',
                    ipv4=True,
                    ipv6=False,
                    import_targets=['65002:20001'],
                    export_targets=['65002:20001'],
                    route_distinguisher='198.18.0.101:4091'
                ),
                an_vrf.VRF(
                    name='red',
                    ipv4=True,
                    ipv6=True,
                    import_targets=['65002:255555'],
                    export_targets=['65002:255555'],
                    route_distinguisher='198.18.0.101:4094'
                )
            ]
    ),
    (
            'blue',
            [
                an_vrf.VRF(
                    name='blue',
                    ipv4=True,
                    ipv6=False,
                    import_targets=['65002:20001'],
                    export_targets=['65002:20001'],
                    route_distinguisher='198.18.0.101:4091'
                )
            ]
    )
])
def test_get_vrfs(test_show_vrf, test_bgp_text_config, vrf, expected):
    vrfs = vrf_task.get_vrfs(test_show_vrf, test_bgp_text_config, vrf)
    assert vrfs == expected


@pytest.mark.parametrize('vrf, expected', [
    (an_vrf.VRF(
        name='blue', ipv4=True, ipv6=False, import_targets=['65002:20001'],
        export_targets=['65002:20001'], route_distinguisher='198.18.0.101:4091'
    ), [
         'vrf instance blue',
         'ip routing vrf blue',
         'router bgp 65002',
         'vrf blue',
         'rd 198.18.0.101:4091',
         'route-target import vpn-ipv4 65002:20001',
         'route-target export vpn-ipv4 65002:20001'
     ]),
    (an_vrf.VRF(
        name='blue', ipv4=False, ipv6=True, import_targets=['65002:20001'],
        export_targets=['65002:20001', '65002:10000', '65000:10'],
        route_distinguisher='198.18.0.101:8101'
    ), [
         'vrf instance blue',
         'ipv6 unicast-routing vrf blue',
         'router bgp 65002',
         'vrf blue',
         'rd 198.18.0.101:8101',
         'route-target import vpn-ipv6 65002:20001',
         'route-target export vpn-ipv6 65002:20001',
         'route-target export vpn-ipv6 65002:10000',
         'route-target export vpn-ipv6 65000:10'
     ]),
    (an_vrf.VRF(
        name='red', ipv4=True, ipv6=True,
        import_targets=['65002:20000', '65002:10000', '65000:10'],
        export_targets=['65002:20000'],
        route_distinguisher=None
    ), [
        'vrf instance red',
        'ip routing vrf red',
        'ipv6 unicast-routing vrf red'
    ])
])
def test_generate_vrf_create_commands(vrf, expected, test_bgp_text_config):
    commands = vrf_task.generate_create_vrf_commands(vrf, test_bgp_text_config)
    assert commands == expected


@pytest.mark.parametrize('vrf, expected', [
    (an_vrf.VRF(
        name='blue', ipv4=True, ipv6=False, import_targets=['65002:20001'],
        export_targets=['65002:20001'], route_distinguisher='198.18.0.101:4091'
    ), [
        f'no ip routing vrf blue',
        f'no ipv6 unicast-routing vrf blue',
        f'no vrf instance blue',
        f'router bgp 65002',
        f'no vrf blue',
     ]),
    (an_vrf.VRF(
        name='blue', ipv4=False, ipv6=True, import_targets=['65002:20001'],
        export_targets=['65002:20001', '65002:10000', '65000:10'],
        route_distinguisher='198.18.0.101:8101'
    ), [
        f'no ip routing vrf blue',
        f'no ipv6 unicast-routing vrf blue',
        f'no vrf instance blue',
        f'router bgp 65002',
        f'no vrf blue',
     ]),
    (an_vrf.VRF(
        name='red', ipv4=True, ipv6=True,
        import_targets=['65002:20000', '65002:10000', '65000:10'],
        export_targets=['65002:20000'],
        route_distinguisher=None
    ), [
        f'no ip routing vrf red',
        f'no ipv6 unicast-routing vrf red',
        f'no vrf instance red',
        f'router bgp 65002',
        f'no vrf red',
     ])
])
def test_generate_vrf_delete_commands(vrf, expected, test_bgp_text_config):
    commands = vrf_task.generate_delete_vrf_commands(vrf, test_bgp_text_config)
    assert commands == expected
