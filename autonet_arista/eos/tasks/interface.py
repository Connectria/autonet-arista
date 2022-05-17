import re
from typing import Union

from autonet_ng.core.objects import interfaces as an_if
from autonet_ng.util import config_string

from autonet_arista.eos.const import DESCRIPTION_TAG, SPEED_DUPLEX_MAP, VIRTUAL_INTERFACE_TYPES
from autonet_arista.eos.exceptions import MixedAnycastUnicastError, NotSwitchport
from autonet_arista.eos.util import get_v6_mask_length, is_switchport, is_virtual


def get_interface_vrf_map(eos_vrfs) -> dict:
    """
    Uses the output of `show vrfs` to build a map of
    interfaces to vrf, for easier parsing by functions
    that build interface data.
    :param eos_vrfs:  Output of `show vrf` command
    :return:
    """
    vrf_map = {}
    for vrf_name, vrf_data in eos_vrfs['vrfs'].items():
        for interface in vrf_data['interfaces']:
            # Autonet views the GRT or "default" vrf as None.
            vrf_map[interface] = vrf_name if vrf_name != 'default' else None
    return vrf_map


def get_lag_map(eos_lags: dict) -> dict:
    """
    Generates a map of LAG member interfaces to their parent LAG
    interfaces
    :param eos_lags:
    :return:
    """
    lag_map = {}
    for pc, pc_data in eos_lags['portChannels'].items():
        pc_ports = {**pc_data['activePorts'], **pc_data['inactivePorts']}
        for pc_port in pc_ports:
            lag_map[pc_port] = pc
    return lag_map


def get_ipv4_addresses(addr_list: list) \
        -> list[an_if.InterfaceAddress]:
    """
    Parse the list of Autonet Address objects from the EOS
    `interface['interfaceAddress']` field.
    :param addr_list:
    :return:
    """
    addresses = []
    for if_addr in addr_list:
        # Determine if an address is assigned, and what type if so.
        if if_addr['primaryIp']['maskLen'] != 0:
            addr_key = 'primaryIp'
        elif if_addr['virtualIp']['maskLen'] != 0:
            addr_key = 'virtualIp'
        else:
            continue
        addr_type = 'anycast' if addr_key == 'virtualIp' else None
        ip_addr = f"{if_addr[addr_key]['address']}/{if_addr[addr_key]['maskLen']}"

        addresses.append(an_if.InterfaceAddress(
            family='ipv4',
            address=ip_addr,
            virtual=True if addr_type else False,
            virtual_type=addr_type
        ))
        for _, secondary in if_addr['secondaryIps'].items():
            ip_addr = f"{secondary['address']}/{secondary['maskLen']}"
            addresses.append(an_if.InterfaceAddress(
                family='ipv4',
                address=ip_addr,
                virtual=False,
                virtual_type=None
            ))

    return addresses


def get_ipv6_addresses(addr_list: list, virtual: False) \
        -> list[an_if.InterfaceAddress]:
    """
    Parse the list of Autonet Address objects from the EOS
    `interface['interfaceAddressIp6']['globalUnicastIp6s']` field.
    :param addr_list:
    :param virtual: Value of `interface['globalAddressesAreVirtual']`
    :return:
    """
    addresses = []
    addr_type = 'anycast' if virtual else None
    for if_addr in addr_list:
        v6_mask = get_v6_mask_length(if_addr['subnet'])
        v6_addr_string = f"{if_addr['address']}/{v6_mask}"
        addresses.append(an_if.InterfaceAddress(
            family='ipv6',
            address=v6_addr_string,
            virtual=True if addr_type else False,
            virtual_type=addr_type
        ))
    return addresses


def get_route_attributes(interface: dict, eos_vrfs: dict) \
        -> an_if.InterfaceRouteAttributes:
    """
    Builds the `InterfaceRouteAttributes` object for an interface.
    :param interface: Interface object from `show interfaces` command.
    :param eos_vrfs: Output of `show vrf` command.
    :return:
    """
    addresses = get_ipv4_addresses(interface['interfaceAddress'])
    if 'interfaceAddressIp6' in interface:
        addresses += get_ipv6_addresses(
            interface['interfaceAddressIp6']['globalUnicastIp6s'],
            interface['interfaceAddressIp6']['globalAddressesAreVirtual'])

    vrf_map = get_interface_vrf_map(eos_vrfs)

    return an_if.InterfaceRouteAttributes(
        vrf=vrf_map[interface['name']] if interface['name'] in vrf_map else None,
        addresses=addresses
    )


def get_interface_vlan_info(if_name: str, eos_interfaces_vlans: dict) -> (int, [int]):
    """
    Returns a tuple of untagged and tagged vlan information.
    :param if_name: The interface name.
    :param eos_interfaces_vlans:
    :return:
    """
    if_info = eos_interfaces_vlans['interfaces'][if_name] \
        if if_name in eos_interfaces_vlans['interfaces'] else None
    if not if_info:
        return None, []
    else:
        untagged = if_info['untaggedVlan'] if 'untaggedVlan' in if_info else None
        tagged = if_info['taggedVlans'] if 'taggedVlans' in if_info else []
        return untagged, tagged


def get_bridge_attributes(interface: dict, eos_interfaces_vlans: dict) \
        -> an_if.InterfaceBridgeAttributes:
    """
    Builds the InterfaceBridgeAttributes object for an interface.
    :param interface:
    :param eos_interfaces_vlans:
    :return:
    """
    untagged, tagged = get_interface_vlan_info(interface['name'], eos_interfaces_vlans)

    return an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True if tagged else False,
        dot1q_vids=tagged,
        dot1q_pvid=untagged
    )


def get_attributes(interface: dict, eos_interfaces_vlans: dict, eos_vrfs: dict) \
        -> Union[an_if.InterfaceRouteAttributes,
                 an_if.InterfaceBridgeAttributes]:
    """
    Get the attributes object appropriate to the interface.
    :param interface: Single interface from `show interfaces` output.
    :param eos_interfaces_vlans: Output from `show interfaces vlans`
    :param eos_vrfs: Output from `show vrf`
    :return:
    """
    return get_route_attributes(interface, eos_vrfs) if \
        interface['forwardingModel'] == 'routed' \
        else get_bridge_attributes(interface, eos_interfaces_vlans)


def get_parent_interface_name(interface_name: str) -> str:
    """
    Parses `interface_name` and returns the name of the parent interface.
    :param interface_name: Name of the child interface.
    :return:
    """
    parent = re.findall(r"^([\w-]*)\.\d*$", interface_name)
    return parent[0] if len(parent) == 1 else None


def get_interface_object(eos_interface: dict, eos_interfaces_vlans: dict,
                         eos_vrfs: dict, eos_lags: dict) -> an_if.Interface:
    """
    Parses outputs of `show interfaces` and `show interfaces vlans` to build
    an Interface instance.  Also uses the output of `show vrfs` to find VRF
    configuration for "routed" interfaces.
    :param eos_interface: The output from `show interfaces`
    :param eos_interfaces_vlans: The output from `show interfaces vlan`
    :param eos_vrfs: The output from `show vrf`
    :param eos_lags: The output from `show port-channel detailed`
    :return:
    """
    # Determine if duplex is applicable, and then format it accordingly.
    duplex = eos_interface['duplex'] if 'duplex' in eos_interface else 'duplexFull'
    duplex = 'full' if duplex and duplex == 'duplexFull' else 'half'
    # Determine if speed is applicable, and then format it accordingly.
    speed = eos_interface['bandwidth'] / 1000000 if 'bandwidth' in eos_interface and eos_interface[
        'bandwidth'] else None
    # Determine physical address, if applicable.
    physical_address = eos_interface['physicalAddress'] \
        if 'physicalAddress' in eos_interface \
        else '00:00:00:00:00:00'
    # Attempt to infer parent name.
    parent = get_parent_interface_name(eos_interface['name'])
    # The forwarding model for a LAG member is "dataLink".  We detect here
    # and set the mode appropriately.  Also, we set parent to the name of
    # the LAG interface.
    if eos_interface['forwardingModel'] == 'dataLink':
        mode = 'aggregated'
        lag_map = get_lag_map(eos_lags)
        parent = lag_map[eos_interface['name']]
    else:
        mode = eos_interface['forwardingModel']
    # Process attributes for 'routed' and 'bridged' interfaces.  Otherwise,
    # Set to none.
    if mode == 'aggregated':
        attributes = None
    else:
        attributes = get_attributes(eos_interface, eos_interfaces_vlans, eos_vrfs)
    return an_if.Interface(
        name=eos_interface['name'],
        mode=mode,
        description=eos_interface['description'].removesuffix(DESCRIPTION_TAG),
        virtual=True if eos_interface['hardware'] in VIRTUAL_INTERFACE_TYPES else False,
        attributes=attributes,
        admin_enabled=True if eos_interface['interfaceStatus'] != 'disabled' else False,
        physical_address=physical_address,
        child=True if parent else False,
        parent=parent,
        speed=int(speed) if speed else None,
        duplex=duplex,
        mtu=eos_interface['mtu'] if 'mtu' in eos_interface else 65535
    )


def generate_common_interface_commands(interface: an_if.Interface,
                                       update: bool = False) -> [str]:
    """
    Parse `Interface` object and return any config commands that are common to
    all interfaces.
    :param interface: An Autonet Interface object.
    :param update: Indicate if None values are to be interpreted as unset (`update=False`)
                   or to be ignored (`update=True`)
    :return:
    """
    commands = [f'interface {interface.name}']
    if not update and not interface.description:
        commands.append(f'no description')
    elif interface.description:
        commands.append(f'description {interface.description} {DESCRIPTION_TAG}')

    if interface.admin_enabled is not None:
        commands.append('no shutdown' if interface.admin_enabled else 'shutdown')

    if not update and interface.mtu is None:
        commands.append('no mtu')
    elif interface.mtu:
        commands.append(f'mtu {interface.mtu}')

    return commands


def generate_physical_interface_commands(interface: an_if.Interface,
                                         update: bool = False) -> [str]:
    """
    Generate the appropriate speed and duplex based on user inputs.
    :param interface: An Autonet Interface object.
    :param update: Indicate if None values are to be interpreted as unset (`update=False`)
                   or to be ignored (`update=True`)
    :return:
    """
    if not update and not interface.speed:
        return [f'no speed']

    for command, (speed, duplex) in SPEED_DUPLEX_MAP.items():
        if interface.speed == speed:
            # If the duplex in the map is None, then it means
            # we ignore the requested duplex, because it's meaningless.
            # Otherwise, we match against the requested duplex.
            if not duplex or (interface.duplex == duplex):
                return [f'speed {command}']
    # If we didn't find it, then we ignore it.
    return []


def generate_bridged_mode_commands(interface: an_if.Interface,
                                   update: bool = False) -> [str]:
    """
    Generate commands to configure attributes passed via an
    `InterfaceBridgeAttributes` object.
    :param interface: An Autonet Interface object.
    :param update: Indicate if None values are to be interpreted as unset (`update=False`)
                   or to be ignored (`update=True`)
    :return:
    """
    commands = ['switchport']
    attributes: an_if.InterfaceBridgeAttributes = interface.attributes
    if attributes.dot1q_enabled is not None:
        switchport_mode = 'trunk' if attributes.dot1q_enabled else 'access'
        commands.append(f'switchport mode {switchport_mode}')
    else:
        commands.append('no switchport mode')
    # If we have a pvid, we use different commands depending on the port mode.
    if attributes.dot1q_pvid:
        if attributes.dot1q_enabled:
            commands.append(f'switchport trunk native vlan {attributes.dot1q_pvid}')
        else:
            commands.append(f'switchport access vlan {attributes.dot1q_pvid}')
    # Special case, if dot1q and dot1q_pvid is set to None, then we clear native VLAN
    if not update and attributes.dot1q_pvid is None and attributes.dot1q_enabled:
        commands.append('no switchport trunk native vlan')
    # Clear vlan allowed list for None, set to disallow all on empty set, otherwise
    # apply glob.
    if not update and attributes.dot1q_vids is None:
        commands.append('switchport trunk allowed vlan all')
    elif not attributes.dot1q_vids:
        commands.append('switchport trunk allowed vlan none')
    else:
        vlan_glob = config_string.vlan_list_to_glob(attributes.dot1q_vids)
        commands.append(f'switchport trunk allowed vlan {vlan_glob}')

    return commands


def generate_routed_mode_commands(interface: an_if.Interface,
                                  update: bool = False) -> [str]:
    """
    Generate commands to configure attributes passed via an
    `InterfaceRouteAttributes` object.
    :param interface: An Autonet Interface object.
    :param update: Indicate if None values are to be interpreted as unset (`update=False`)
                   or to be ignored (`update=True`)
    :return:
    """
    attributes: an_if.InterfaceRouteAttributes = interface.attributes
    # Special error check specific to this platform.  Anycast and Unicast
    # addresses cannot be mixed on an interface.
    switchport = is_switchport(interface.name)
    has_anycast = False
    has_unicast = False
    for address in attributes.addresses:
        if address.virtual and address.virtual_type == 'anycast':
            has_anycast = True
        else:
            has_unicast = True
    if has_anycast and has_unicast:
        raise MixedAnycastUnicastError()

    # Handle basic setup and vrf command.
    commands = ['no switchport'] if switchport else []
    if attributes.vrf is None and not update:
        commands.append('no vrf')
    if attributes.vrf:
        commands.append(f'vrf {attributes.vrf}')
    if not update or attributes.addresses == []:
        commands += ['no ip address', 'no ipv6 address', 'no ipv6 enable']

    # set the command based on type of addresses being programmed.
    ipv4_command = 'ip address virtual ' if has_anycast else 'ip address '
    ipv6_command = 'ipv6 address virtual ' if has_anycast else 'ipv6 address '
    ipv4_secondaries = False
    for address in attributes.addresses:
        if address.family == 'ipv4':
            # Apply "secondary" to command after first.
            secondary = ' secondary' if ipv4_secondaries else ''
            commands.append(f'{ipv4_command}{address.address}{secondary}')
            ipv4_secondaries = True
        if address.family == 'ipv6':
            # Apply "ipv6 enable" on first encounter of an IPv6 address.
            if 'ipv6 enable' not in commands:
                commands.append('ipv6 enable')
            commands.append(f'{ipv6_command}{address.address}')

    return commands


def generate_interface_commands(interface: an_if.Interface,
                                update: bool = False) -> [str]:
    """
    Generate a list of config mode commands that will create
    the interface object.
    :param interface: An Autonet Interface object.
    :param update: Indicate if None values are to be interpreted as unset (`update=False`)
                   or to be ignored (`update=True`)
    :return:
    """
    switchport = is_switchport(interface.name)
    virtual = is_virtual(interface.name)
    # Do some interface specific error checking.
    if interface.mode == 'bridged' and not switchport:
        raise NotSwitchport

    # All interfaces will start with these.
    commands = generate_common_interface_commands(interface, update)

    # If the user has specified a physical interface attribute, we'll generate
    # it and raise an exception later if the network device doesn't care
    # to silently ignore them.
    if (interface.speed or interface.duplex) and not virtual:
        commands += generate_physical_interface_commands(interface, update)
    if interface.mode == 'bridged' and switchport:
        commands += generate_bridged_mode_commands(interface, update)
    if interface.mode == 'routed':
        commands += generate_routed_mode_commands(interface, update)

    return commands
