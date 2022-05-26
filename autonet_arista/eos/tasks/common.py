import re

from autonet_ng.core.objects import vxlan as an_vxlan
from autonet_ng.core.objects import vrf as an_vrf
from typing import Union


def get_fq_if_name(if_name: str) -> str:
    """
    Returns the fully qualified interface name for the provided
    shorthand name. For example, "Po22" would evaluate to
    "Port-Channel22"
    :param if_name:
    :return:
    """
    match = re.search(r'(?P<if_type>[A-z-]*)(?P<if_id>[\d/]*)', if_name)
    if_type = match.group('if_type')
    if_id = match.group('if_id')
    fq_names = ['Ethernet', 'Loopback', 'Management', 'Port-Channel',
                'Tunnel', 'Vlan', 'Vxlan']
    result = None
    for fq_name in fq_names:
        # we track if we've matched the entry before to see if the string
        # passed in is too ambiguous.  EOS does the same thing.
        matched = fq_name.lower().startswith(if_type.lower())
        if matched and result:
            raise ValueError("Provided shorthand name is ambiguous.")
        if matched:
            result = f'{fq_name}{if_id}'
    if result:
        return result
    raise ValueError("Could not parse fully qualified interface name.")


def parse_bgp_vpn_config(text_config: str) -> dict:
    """
    Parses the textual BGP configuration block into a structured
    dictionary.

    .. code-block::
        {
            'asn': 65500,
            'rid': 198.18.0.1
            'vrfs': {
                'vrf-name': {
                    'rid': 198.18.0.1
                    'import_targets': {
                        'evpn': [],
                        'vpn-ipv4: [],
                        'vpn-ipv6: [],
                    },
                    'export_targets': {
                        'evpn': [],
                        'vpn-ipv4: [],
                        'vpn-ipv6: [],
                    },
                    'route-distinguisher': 198.18.0.1:2
                }
            },
            'vlans': {
                'vlan-id': {
                    'import_targets': [],
                    'export_targets': [],
                    'route-distinguisher': 198.18.0.1:100
                }
            }
        }


    :param text_config: The text configuration block.
    :return:
    """
    # TODO: (kvondersaar) This function is hilariously cumbersome and
    #  needs to be split into more discrete parts.
    asn_regex = r'router bgp (?P<asn>[0-9]*$)'
    rid_regex = r'router-id (?P<rid>[0-9\.]*)$'
    vlan_regex = r'vlan (?P<vlan_id>[0-9]*$)'
    vrf_regex = r'vrf (?P<vrf_name>[\S]*$)'
    rt_regex = r'route-target (?P<direction>[\S]*) ?(?P<afi>evpn|vpn-ipv4|vpn-ipv6|) (?P<rt>[\d\.]*\:[\d]*)$'
    rd_regex = r'rd (?P<rd>[\d\.]*\:[\d]*)$'

    config_lines = text_config.split('\n')
    bgp_config = {}
    node = {}
    context = None
    for config_line in config_lines:
        if match := re.search(asn_regex, config_line):
            bgp_config['asn'] = match.group('asn')
        if match := re.search(vlan_regex, config_line):
            node = bgp_config.setdefault('vlans', {}).setdefault(match.group('vlan_id'), {})
            context = 'vlan'
        if match := re.search(vrf_regex, config_line):
            node = bgp_config.setdefault('vrfs', {}).setdefault(match.group('vrf_name'), {})
            context = 'vrf'
        # Once we have a node we can parse out the things that may belong to it.
        if match := re.search(rid_regex, config_line):
            if node:
                node['rid'] = match.group('rid')
            else:
                bgp_config['rid'] = match.group('rid')
        if match := re.search(rt_regex, config_line):
            # when we match up on an RT we place it only in the AFI for which
            # it is defined.  If no AFI exists in the config, then it's explicitly
            # all AFIs.
            if context == 'vrf':
                all_afis = ['evpn', 'vpn-ipv4', 'vpn-ipv6']
                # Initialize the node data structure if not already done.

                if 'import_targets' not in node or not isinstance(node['import_targets'], dict):
                    node['import_targets'] = {'evpn': [], 'vpn-ipv4': [], 'vpn-ipv6': []}
                if 'export_targets' not in node or not isinstance(node['export_targets'], dict):
                    node['export_targets'] = {'evpn': [], 'vpn-ipv4': [], 'vpn-ipv6': []}
                if match.group('afi'):
                    afis = [match.group('afi')]
                else:
                    afis = all_afis
                for afi in afis:
                    if match.group('direction') == 'both':
                        node.setdefault('import_targets', {}).setdefault(afi, []).append(match.group('rt'))
                        node.setdefault('export_targets', {}).setdefault(afi, []).append(match.group('rt'))
                    else:
                        targets = f"{match.group('direction')}_targets"
                        node.setdefault(targets, {}).setdefault(afi, []).append(match.group('rt'))
            elif context == 'vlan':
                if match.group('direction') == 'both':
                    node.setdefault('import_targets', []).append(match.group('rt'))
                    node.setdefault('export_targets', []).append(match.group('rt'))
                else:
                    targets = f"{match.group('direction')}_targets"
                    node.setdefault(targets, []).append(match.group('rt'))

        if match := re.search(rd_regex, config_line):
            node['rd'] = match.group('rd')

    return bgp_config


def generate_rt_commands(conf_obj: Union[an_vxlan.VXLAN, an_vrf.VRF],
                         bgp_asn: Union[str, int] = None) -> ([str], [str]):
    """
    Generate the import and export commands for a list of RTs.  BGP ASN
    is used for the generation of auto-derived RTs and is only needed if 'auto'
    is present in the list of RTs.  Auto RT generation is for VXLAN only.
    :param conf_obj: The configuration object containing RT information in its
           attributes named `import_targets` and `export_targets`. May be VXLAN,
           VRF, or possibly others.
    :param bgp_asn: The BGP ASN to use for auto-derived RTs.
    :return:
    """
    valid_conf_obj = (an_vxlan.VXLAN, an_vrf.VRF)
    if not isinstance(conf_obj, valid_conf_obj):
        raise Exception(f"`conf_obj` must be one of {valid_conf_obj}")
    afis = []
    if isinstance(conf_obj, an_vxlan.VXLAN):
        afis.append('evpn')
    if isinstance(conf_obj, an_vrf.VRF):
        afis = []
        if conf_obj.ipv4:
            afis.append('ipv4')
        if conf_obj.ipv6:
            afis.append('ipv6')
    import_targets = conf_obj.import_targets or []
    export_targets = conf_obj.export_targets or []

    # Do some input validation.
    if 'auto' in import_targets or 'auto' in export_targets:
        auto = True
    else:
        auto = False
    if auto and not bgp_asn:
        raise Exception('"bgp_asn" must be set when RT value is "auto".')
    if auto and not isinstance(conf_obj, an_vxlan.VXLAN):
        raise Exception(f'Auto RT is only supported with {an_vxlan.VXLAN} objects.')

    auto_rt = f'{bgp_asn}:{conf_obj.id}'
    if 'auto' in import_targets:
        import_targets = [rt for rt in import_targets if rt != 'auto']
        import_targets.append(auto_rt)
    if 'auto' in export_targets:
        export_targets = [rt for rt in export_targets if rt != 'auto']
        export_targets.append(auto_rt)

    import_commands = []
    export_commands = []
    for afi in afis:
        import_commands += [f'route-target import {afi} {rt}'
                            for rt in import_targets]
        export_commands += [f'route-target export {afi} {rt}'
                            for rt in export_targets]
    return import_commands, export_commands
