from autonet_ng.core import exceptions as exc
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
    bgp_config = common_task.parse_bgp_vpn_config(show_bgp_config)
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
            export_targets=bgp_config_node.get('export_targets', {}).get('evpn', []),
            import_targets=bgp_config_node.get('import_targets', {}).get('evpn', []),
            route_distinguisher=bgp_config_node.get('rd', None),
            bound_object_id=vrf_name
        ))

    return vxlans


def generate_l2_vxlan_create_commands(vxlan: an_vxlan.VXLAN) -> [str]:
    """
    Generate the commands required to create a l2 vxlan as
    appropriate.
    :param vxlan: A `VXLAN` object.
    :return:
    """
    return [
        'interface vxlan1',
        f'vxlan vlan {vxlan.bound_object_id} vni {vxlan.id}'
    ]


def generate_l3_vxlan_create_commands(vxlan: an_vxlan.VXLAN) -> [str]:
    """
    Generate the commands required to create a l3 vxlan as
    appropriate.
    :param vxlan: A `VXLAN` object.
    :return:
    """
    return [
        'interface vxlan1',
        f'vxlan vrf {vxlan.bound_object_id} vni {vxlan.id}'
    ]


def generate_vxlan_commands(vxlan: an_vxlan.VXLAN) -> [str]:
    """
    Generate the commands required to create given vxlan as
    appropriate.
    :param vxlan: A `VXLAN` object.
    :return:
    """
    if vxlan.layer == 2:
        return generate_l2_vxlan_create_commands(vxlan)
    if vxlan.layer == 3:
        return generate_l3_vxlan_create_commands(vxlan)


def generate_l2_vxlan_evpn_commands(vxlan: an_vxlan.VXLAN, show_int_vxlan: dict,
                                    bgp_config: dict) -> [str]:
    """
    Generate the commands to advertise an L2 VNI + VLAN in EVPN.
    :param vxlan: A `VXLAN` object.
    :param show_int_vxlan: The output of 'show interfaces vxlan1'.
    :param bgp_config: The parsed output of the textual BGP config.
    :return:
    """
    if vxlan.route_distinguisher == 'auto':
        vxlan.route_distinguisher = f'{bgp_config["rid"]}:{vxlan.bound_object_id}'
    import_rt_cmds, export_rt_cmds = common_task.generate_rt_commands(vxlan, bgp_config['asn'])
    return [
               f'router bgp {bgp_config["asn"]}',
               f'vlan {vxlan.bound_object_id}',
               'redistribute learned',
               f'rd {vxlan.route_distinguisher}'
           ] + import_rt_cmds + export_rt_cmds


def generate_l3_vxlan_evpn_commands(vxlan: an_vxlan.VXLAN, show_int_vxlan: dict,
                                    bgp_config: dict) -> [str]:
    """
    Generate the commands to advertise an L3 VNI + VRF in EVPN.
    :param vxlan: A `VXLAN` object.
    :param show_int_vxlan: The output of 'show interfaces vxlan1'.
    :param bgp_config: The parsed output of the textual BGP config.
    :return:
    """
    if vxlan.route_distinguisher == 'auto':
        auto_vlan = None
        vni_map = show_int_vxlan['interfaces']['Vxlan1']['vlanToVniMap']
        for vlan_id in vni_map:
            if vni_map[vlan_id]['vni'] == vxlan.id:
                auto_vlan = vlan_id
                break
        if not auto_vlan:
            raise exc.AutonetException('Could not auto-derive RD')
        vxlan.route_distinguisher = f'{bgp_config["rid"]}:{auto_vlan}'
    import_rt_cmds, export_rt_cmds = common_task.generate_rt_commands(vxlan, bgp_config['asn'])
    return [
               f'router bgp {bgp_config["asn"]}',
               f'vrf {vxlan.bound_object_id}',
               'redistribute connected',
               'redistribute attached-host',
               'redistribute static',
               f'rd {vxlan.route_distinguisher}'
           ] + import_rt_cmds + export_rt_cmds


def generate_vxlan_evpn_commands(vxlan: an_vxlan.VXLAN, show_int_vxlan: dict,
                                 show_bgp_config: str) -> [str]:
    """
    Generate BGP_EVPN commands to advertise a given VNI.
    :param vxlan: A `VXLAN` object.
    :param show_int_vxlan: Output from "show interfaces vxlan"
    :param show_bgp_config: Textural BGP configuration.
    :return:
    """
    bgp_config = common_task.parse_bgp_vpn_config(show_bgp_config)
    if vxlan.layer == 2:
        return generate_l2_vxlan_evpn_commands(
            vxlan, show_int_vxlan, bgp_config)
    if vxlan.layer == 3:
        return generate_l3_vxlan_evpn_commands(
            vxlan, show_int_vxlan, bgp_config)


def generate_vxlan_delete_commands(vxlan: an_vxlan.VXLAN, show_bgp_config: str) -> [str]:
    """
    Generates a set of commands to remove a VXLAN tunnel from a device.
    For L2 VNIs, we will remove the vlan from the BGP EVPN configuration.
    For L3 VNIs, we will remove only the tunnel definition and
    redistribution of attached hosts, but not any of the BGP configuration
    as it's shared with other address families. Subsequent calls to remove
    the VRF itself would need to be made and are generally expected in
    teardown use cases.
    :param vxlan: A `VXLAN` object.
    :param show_bgp_config: The active textual BGP configuration.
    :return:
    """
    bgp_config = common_task.parse_bgp_vpn_config(show_bgp_config)
    if vxlan.layer == 2:
        return [
            'interface vxlan1',
            f'no vxlan vlan {vxlan.bound_object_id} vni {vxlan.id}',
            f'router bgp {bgp_config["asn"]}',
            f'no vlan {vxlan.bound_object_id}',
        ]
    if vxlan.layer == 3:
        return [
            'interface vxlan1',
            f'no vxlan vrf {vxlan.bound_object_id} vni {vxlan.id}',
            f'router bgp {bgp_config["asn"]}',
            f'vrf {vxlan.bound_object_id}',
            'no redistribute attached-host'
        ]
