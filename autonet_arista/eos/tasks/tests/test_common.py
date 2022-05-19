import pytest

from autonet_arista.eos.tasks import common as common_task


def test_parse_bgp_evpn_vxlan_config(test_bgp_text_config, test_bgp_config):
    cfg = common_task.parse_bgp_evpn_vxlan_config(test_bgp_text_config)
    assert cfg == test_bgp_config
