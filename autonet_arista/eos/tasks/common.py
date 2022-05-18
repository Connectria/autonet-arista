import re


def parse_bgp_evpn_vxlan_config(text_config: str) -> dict:
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
                    'import_targets': [],
                    'export_targets': [],
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

    asn_regex = r'router bgp (?P<asn>[0-9]*$)'
    rid_regex = r'router-id (?P<rid>[0-9\.]*)$'
    vlan_regex = r'vlan (?P<vlan_id>[0-9]*$)'
    vrf_regex = r'vrf (?P<vrf_name>[\S]*$)'
    rt_regex = r'route-target (?P<direction>[\S]*) (?P<rt>[\d\.]*\:[\d]*)$'
    rd_regex = r'rd (?P<rd>[\d\.]*\:[\d]*)$'

    config_lines = text_config.split('\n')
    bgp_config = {}
    node = None
    sub_node = None
    for config_line in config_lines:
        if match := re.search(asn_regex, config_line):
            bgp_config['asn'] = match.group('asn')
        if match := re.search(vlan_regex, config_line):
            node = bgp_config.setdefault('vlans', {}).setdefault(match.group('vlan_id'), {})
        if match := re.search(vrf_regex, config_line):
            node = bgp_config.setdefault('vrfs', {}).setdefault(match.group('vrf_name'), {})
        # Once we have a node we can parse out the things that may belong to it.
        if match := re.search(rid_regex, config_line):
            if node:
                node['rid'] = match.group('rid')
            else:
                bgp_config['rid'] = match.group('rid')
        if match := re.search(rt_regex, config_line):
            if match.group('direction') == 'both':
                node.setdefault('import_targets', []).append(match.group('rt'))
                node.setdefault('export_targets', []).append(match.group('rt'))
            else:
                targets = f"{match.group('direction')}_targets"
                node.setdefault(targets, []).append(match.group('rt'))
        if match := re.search(rd_regex, config_line):
            node['rd'] = match.group('rd')

    return bgp_config
