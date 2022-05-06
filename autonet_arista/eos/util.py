import re

from autonet.core import objects as obj

from autonet_arista.eos.const import VIRTUAL_INTERFACE_TYPES


def get_v6_mask_length(addr: str) -> str:
    """
    Returns the prefix length of an IPv6 prefix or address.
    :param addr:
    :return:
    """
    regex = r".*/([0-9]*)"
    result = re.search(pattern=regex, string=addr)
    try:
        return result.group(1)
    except:
        raise ValueError(f"Could not parse prefix length from {addr}")


def get_ipv4_addresses(addr_list: list) \
        -> list[obj.interfaces.InterfaceAddress]:
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

        addresses.append(obj.interfaces.InterfaceAddress(
            family='ipv4',
            address=ip_addr,
            virtual=True if addr_type else False,
            virtual_type=addr_type
        ))
    return addresses


def get_ipv6_addresses(addr_list: list, virtual: False) \
        -> list[obj.interfaces.InterfaceAddress]:
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
        addresses.append(obj.interfaces.InterfaceAddress(
            family='ipv6',
            address=v6_addr_string,
            virtual=True if addr_type else False,
            virtual_type=addr_type
        ))
    return addresses


def get_route_attributes(interface) \
        -> obj.interfaces.InterfaceRouteAttributes:
    """
    Builds the `InterfaceRouteAttributes` object for an interface
    :param interface:
    :return:
    """
    addresses = get_ipv4_addresses(interface['interfaceAddress'])
    if 'interfaceAddressIp6' in interface:
        addresses += get_ipv6_addresses(
            interface['interfaceAddressIp6']['globalUnicastIp6s'],
            interface['interfaceAddressIp6']['globalAddressesAreVirtual'])

    return obj.interfaces.InterfaceRouteAttributes(
        vrf=None,
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
        -> obj.interfaces.InterfaceBridgeAttributes:
    """
    Builds the InterfaceBridgeAttributes object for an interface.
    :param interface:
    :param eos_interfaces_vlans:
    :return:
    """
    untagged, tagged = get_interface_vlan_info(interface['name'], eos_interfaces_vlans)

    return obj.interfaces.InterfaceBridgeAttributes(
        dot1q_enabled=True if tagged else False,
        dot1q_vids=tagged,
        dot1q_pvid=untagged
    )


def get_attributes(interface: dict, eos_interfaces_vlans: dict):
    """
    Get the attributes object appropriate to the interface.
    :param interface:
    :param eos_interfaces_vlans:
    :return:
    """
    return get_route_attributes(interface) if \
        interface['forwardingModel'] == 'routed' \
        else get_bridge_attributes(interface, eos_interfaces_vlans)


def get_interface_object(eos_interface: dict, eos_interfaces_vlans: dict) -> obj.interfaces.Interface:
    """
    Parses outputs of `show interfaces` and `show interfaces vlans` to build
    an Interface instance.
    :param eos_interface:
    :param eos_interfaces_vlans:
    :return:
    """
    # Determine if duplex is applicable, and then format it accordingly.
    duplex = eos_interface['duplex'] if 'duplex' in eos_interface else None
    duplex = 'full' if duplex and duplex == 'duplexFull' else 'half'
    # Determine if speed is applicable, and then format it accordingly.
    speed = eos_interface['bandwidth'] / 1000000 if 'bandwidth' in eos_interface and eos_interface[
        'bandwidth'] else None
    # Determine physical address, if applicable.
    physical_address = eos_interface['physicalAddress'] \
        if 'physicalAddress' in eos_interface \
        else '00:00:00:00:00:00'
    return obj.interfaces.Interface(
        name=eos_interface['name'],
        mode=eos_interface['forwardingModel'],
        description=eos_interface['description'],
        virtual=True if eos_interface['hardware'] in VIRTUAL_INTERFACE_TYPES else False,
        attributes=get_attributes(eos_interface, eos_interfaces_vlans),
        admin_enabled=True if eos_interface['interfaceStatus'] != 'disabled' else False,
        physical_address=physical_address,
        child=False,
        parent=None,
        speed=int(speed) if speed else None,
        duplex=duplex,
        mtu=eos_interface['mtu'] if 'mtu' in eos_interface else 65535
    )
