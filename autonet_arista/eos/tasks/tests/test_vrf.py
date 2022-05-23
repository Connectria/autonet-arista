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
