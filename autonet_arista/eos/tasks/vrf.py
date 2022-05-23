from autonet_ng.core.objects import vrf as an_vrf
from autonet_arista.eos.tasks import common as common_task


def get_vrfs(show_vrf: dict, bgp_text_config: str,
             vrf: str = None) -> [an_vrf.VRF]:
    """
    Generate a list of configured VRFs and associated VPN data
    from the output of "show vrf" and the BGP text config.
    :param show_vrf: Output of the "show vrf" command.
    :param bgp_text_config: The textual BGP configuration.
    :param vrf: A VRF name.  If specified only the named VRF is
                returned.
    :return:
    """
    excluded_vrfs = ['default', 'mgmt-if']
    bgp_config = common_task.parse_bgp_vpn_config(bgp_text_config)
    vrfs = []
    for vrf_name, vrf_data in show_vrf['vrfs'].items():
        if vrf_name in excluded_vrfs:
            continue
        if vrf and vrf != vrf_name:
            continue
        ipv4 = True if vrf_data['protocols']['ipv4']['routingState'] == 'up' else False
        ipv6 = True if vrf_data['protocols']['ipv6']['routingState'] == 'up' else False
        import_targets = []
        export_targets = []
        # While the platform does support discrete targets for IPv4 and
        # IPv6, Autonet doesn't care, so we mash it all together.  If
        # you're driving an Arista device with Autonet you should be
        # aware of this limitation anyway.
        if ipv4:
            import_targets += bgp_config['vrfs'][vrf_name]['import_targets']['vpn-ipv4']
            export_targets += bgp_config['vrfs'][vrf_name]['export_targets']['vpn-ipv4']
        if ipv6:
            import_targets += bgp_config['vrfs'][vrf_name]['import_targets']['vpn-ipv6']
            export_targets += bgp_config['vrfs'][vrf_name]['export_targets']['vpn-ipv6']
        # we clean up duplicates by casting to a set and back to a list.
        import_targets = list(set(import_targets))
        export_targets = list(set(export_targets))
        # RD may or may not be set, depending.
        rd = vrf_data['routeDistinguisher'] \
            if vrf_data['routeDistinguisher'] != '' else None
        vrfs.append(an_vrf.VRF(
            name=vrf_name,
            ipv4=ipv4,
            ipv6=ipv6,
            import_targets=import_targets,
            export_targets=export_targets,
            route_distinguisher=rd
        ))

    return vrfs


def generate_create_vrf_commands(vrf: an_vrf.VRF, show_bgp_config: str):
    """
    Generate the commands needed to create a VRF.
    :param vrf: A `VRF` object.
    :param show_bgp_config: The textual BGP configuration.
    :return:
    """
    commands = [
        f'vrf instance {vrf.name}'
    ]
    active_afis = []
    if vrf.ipv4:
        commands.append(f'ip routing vrf {vrf.name}')
        active_afis.append('vpn-ipv4')
    if vrf.ipv6:
        commands.append(f'ipv6 unicast-routing vrf {vrf.name}')
        active_afis.append('vpn-ipv6')
    # If there's no RD there's no point in RTs either, so we
    # ignore the RTs if RD is not set.
    if vrf.route_distinguisher:
        bgp_config = common_task.parse_bgp_vpn_config(show_bgp_config)
        commands += [
            f'router bgp {bgp_config["asn"]}',
            f'vrf {vrf.name}',
            f'rd {vrf.route_distinguisher}'
        ]
        # And now RTs.
        for direction in ['import', 'export']:
            for afi in active_afis:
                rt_set = f'{direction}_targets'
                commands += [f'route-target {direction} {afi} {rt}'
                             for rt in getattr(vrf, rt_set)]

    return commands


def generate_delete_vrf_commands(vrf: an_vrf.VRF, show_bgp_config: str):
    """
    Generate the commands needed to delete a VRF.
    :param vrf: A `VRF` object.
    :param show_bgp_config: The textual BGP configuration.
    :return:
    """
    bgp_config = common_task.parse_bgp_vpn_config(show_bgp_config)
    return [
        f'no ip routing vrf {vrf.name}',
        f'no ipv6 unicast-routing vrf {vrf.name}',
        f'no vrf instance {vrf.name}',
        f'router bgp {bgp_config["asn"]}',
        f'no vrf {vrf.name}',
    ]
