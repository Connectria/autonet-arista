from autonet_ng.core.objects import vxlan as an_vxlan

from autonet_arista.eos.tasks import common as common_task


def get_vxlans(show_int_vxlan: dict, show_bgp_config: str,
               vnid: int = None) -> [an_vxlan.VXLAN]:
    """
    Parse VXLAN interface and BGP configuration to return a list
    of `VXLAN` objects.
    :param show_int_vxlan: Output from "show interfaces vxlan"
    :param show_bgp_config: Textural BGP configuration.
    :param vnid: When set only the VXLAN for the requested VNID is returned.
    :return:
    """
    vxlans = []
    vtep_address = show_int_vxlan['interfaces']['Vxlan1']['srcIpAddr']
    l2_vnis = show_int_vxlan['interfaces']['Vxlan1']['vlanToVniMap']
    l3_vnis = show_int_vxlan['interfaces']['Vxlan1']['vrfToVniMap']
    bgp_config = common_task.parse_bgp_evpn_vxlan_config(show_bgp_config)
    # parse l2 VNIS
    for vlan_id, l2_vni in l2_vnis.items():
        # If a VNID is requested, we check to see if this is it, otherwise
        # we skip.
        if vnid and int(l2_vni['vni']) != vnid:
            continue
        # We also ignore VNIs that are not explicitly set since Arista will add
        # "observed" L3 VNIs from EVPN.
        if l2_vni['source'] == 'evpn':
            continue
        bgp_config_node = bgp_config['vlans'].get(vlan_id, {})
        vxlans.append(an_vxlan.VXLAN(
            id=int(l2_vni['vni']),
            source_address=vtep_address,
            layer=2,
            export_targets=bgp_config_node.get('export_targets', []),
            import_targets=bgp_config_node.get('import_targets', []),
            route_distinguisher=bgp_config_node.get('rd', None),
            bound_object_id=int(vlan_id)
        ))
    for vrf_name, l3_vni in l3_vnis.items():
        # Same skip mechanism as above.
        if vnid and int(l3_vni) != vnid:
            continue
        bgp_config_node = bgp_config['vrfs'].get(vrf_name, {})
        vxlans.append(an_vxlan.VXLAN(
            id=int(l3_vni),
            source_address=vtep_address,
            layer=3,
            export_targets=bgp_config_node.get('export_targets', []),
            import_targets=bgp_config_node.get('import_targets', []),
            route_distinguisher=bgp_config_node.get('rd', None),
            bound_object_id=vrf_name
        ))

    return vxlans
