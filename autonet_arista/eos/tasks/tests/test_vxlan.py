import pytest

from autonet_ng.core.objects import vxlan as an_vxlan

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
