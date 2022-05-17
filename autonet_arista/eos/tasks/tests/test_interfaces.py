import pytest

from autonet_ng.core.objects import interfaces as an_if

from autonet_arista.eos.const import DESCRIPTION_TAG
from autonet_arista.eos.tasks import interface as if_tasks


def test_get_interface_vrf_map(test_eos_vrfs):
    vrf_map = if_tasks.get_interface_vrf_map(test_eos_vrfs)
    for if_name in ["Ethernet10", "Ethernet11", "Ethernet12", "Loopback0",
                    "Loopback5", "Vlan4091", "Vlan4092", "Vlan4093"]:
        assert vrf_map[if_name] is None
    for if_name in ['Ethernet1', 'Vlan71', 'Vlan72', 'Vlan4094']:
        assert vrf_map[if_name] == 'TestCust1-Prod'


def test_get_lag_map(test_eos_lags):
    lag_map = if_tasks.get_lag_map(test_eos_lags)
    for if_name in ['Ethernet5', 'Ethernet6']:
        assert lag_map[if_name] == 'Port-Channel1'


def test_get_ipv4_address_unicast(test_addr_list):
    """
    Test that `get_ipv4_addresses` returns an appropriate
    list of addresses with unicast configuration.
    """
    addresses = if_tasks.get_ipv4_addresses(test_addr_list)
    assert len(addresses) == 3
    for address in addresses:
        assert address.family == 'ipv4'
        assert not address.virtual
        assert not address.virtual_type
    assert addresses[0].address == '198.18.0.1/24'
    assert addresses[1].address == '198.18.100.8/32'
    assert addresses[2].address == '198.18.101.8/32'


def test_get_ipv4_address_anycast(test_anycast_addr_list):
    """
    Test that `get_ipv4_addresses` returns an appropriate
    list of addresses with an anycast configuration.
    """
    addresses = if_tasks.get_ipv4_addresses(test_anycast_addr_list)
    assert len(addresses) == 1
    assert addresses[0].family == 'ipv4'
    assert addresses[0].address == '10.0.0.1/24'
    assert addresses[0].virtual
    assert addresses[0].virtual_type == 'anycast'


@pytest.mark.parametrize('test_v6_addr_list, virtual, expected', [
    (['ea0e:a6b2:68d4:7b21::1/64'], False, ['ea0e:a6b2:68d4:7b21::1/64']),
    (['ea0e:a6b2:68d4:7b21::1/64'], True, ['ea0e:a6b2:68d4:7b21::1/64']),
    (['d427:2654:4337:bd50:ac5c:b28b:48bc:b9c7/128',
      'ea0e:a6b2:68d4:7b21::1/48'],
     False,
     ['d427:2654:4337:bd50:ac5c:b28b:48bc:b9c7/128',
      'ea0e:a6b2:68d4:7b21::1/48'])
], indirect=['test_v6_addr_list'])
def test_get_ipv6_addresses_unicast(test_v6_addr_list, virtual, expected):
    """
    Test that `get_ipv6_addresses` returns an appropriate
    list of addresses.
    """
    addresses = if_tasks.get_ipv6_addresses(test_v6_addr_list, virtual)
    assert len(addresses) == len(test_v6_addr_list)
    for i, address in enumerate(addresses):
        virtual_type = 'anycast' if virtual else None
        assert address.family == 'ipv6'
        assert address.address == expected[i]
        assert address.virtual == virtual
        assert address.virtual_type == virtual_type


def test_get_route_attributes(test_routed_interface, test_eos_vrfs):
    ra = if_tasks.get_route_attributes(test_routed_interface, test_eos_vrfs)
    assert ra.vrf == 'TestCust1-Prod'
    assert len(ra.addresses) == 2
    for address in ra.addresses:
        assert isinstance(address, an_if.InterfaceAddress)


@pytest.mark.parametrize('if_name, expected', [
    ('Ethernet2', (71, None)),
    ('Ethernet3', (71, [72, 88])),
    ('Ethernet4', (1, None))
])
def test_get_interface_vlan_info(if_name, test_eos_interfaces_vlans, expected):
    untagged, tagged = if_tasks.get_interface_vlan_info(if_name, test_eos_interfaces_vlans)
    assert untagged, tagged == expected


def test_get_bridge_attributes(test_bridge_interface, test_eos_interfaces_vlans):
    ba = if_tasks.get_bridge_attributes(test_bridge_interface, test_eos_interfaces_vlans)
    assert ba.dot1q_enabled
    assert ba.dot1q_vids == [88, 72]
    assert ba.dot1q_pvid == 71


@pytest.mark.parametrize('test_interface, expected', [
    ('routed', an_if.InterfaceRouteAttributes),
    ('bridged', an_if.InterfaceBridgeAttributes)
], indirect=['test_interface'])
def test_get_attributes(test_interface, test_eos_interfaces_vlans, test_eos_vrfs, expected):
    a = if_tasks.get_attributes(test_interface, test_eos_interfaces_vlans, test_eos_vrfs)
    assert isinstance(a, expected)


@pytest.mark.parametrize('interface_name, expected', [
    ('Ethernet9.10', 'Ethernet9'),
    ('Port-Channel22.55', 'Port-Channel22'),
    ('Loopback5', None)
])
def test_get_parent_interface_name(interface_name, expected):
    parent = if_tasks.get_parent_interface_name(interface_name)
    assert parent == expected


@pytest.mark.parametrize('test_interface, expected', [
    ('routed', an_if.Interface(
        admin_enabled=True, child=False, description='', duplex='full',
        mode='routed', mtu=1500, name='Vlan71', parent=None,
        physical_address='0C-FE-87-5F-8C-BD', speed=None, virtual=True,
        attributes=an_if.InterfaceRouteAttributes(
            addresses=[
                an_if.InterfaceAddress(
                    address='10.0.0.1/24', family='ipv4', virtual=True,
                    virtual_type='anycast'),
                an_if.InterfaceAddress(
                    address='ea0e:a6b2:68d4:7b21::1/64', family='ipv6', virtual=True,
                    virtual_type='anycast'),
            ],
            vrf='TestCust1-Prod')
    )),
    ('bridged', an_if.Interface(
        admin_enabled=True, child=False, description='', duplex='full',
        mode='bridged', mtu=9214, name='Ethernet3', parent=None,
        physical_address='0C-FE-87-ED-59-03', speed=1000, virtual=False,
        attributes=an_if.InterfaceBridgeAttributes(
            dot1q_enabled=True, dot1q_pvid=71, dot1q_vids=[88, 72]
        )
    ))
], indirect=['test_interface'])
def test_get_interface_object(test_interface, test_eos_interfaces_vlans,
                              test_eos_vrfs, test_eos_lags, expected):
    if_obj = if_tasks.get_interface_object(test_interface,
                                           test_eos_interfaces_vlans,
                                           test_eos_vrfs, test_eos_lags)
    assert if_obj == expected


@pytest.mark.parametrize('test_interface_object, update, expected', [
    ('test_interface1', False, [
        'interface Loopback5',
        'description A test loopback ' + DESCRIPTION_TAG,
        'no shutdown',
        'no mtu'
    ]),
    ('test_interface2', False, [
        'interface vlan91',
        'description A test svi ' + DESCRIPTION_TAG,
        'shutdown',
        'mtu 9000'
    ]),
    ('test_interface3', False, [
        'interface Ethernet44',
        'no description',
        'no shutdown',
        'mtu 9214'
    ]),
    ('test_interface1', True, [
        'interface Loopback5',
        'description A test loopback ' + DESCRIPTION_TAG,
        'no shutdown'
    ]),
    ('test_interface2', True, [
        'interface vlan91',
        'description A test svi ' + DESCRIPTION_TAG,
        'shutdown',
        'mtu 9000'
    ]),
    ('test_interface3', True, [
        'interface Ethernet44',
        'no shutdown',
        'mtu 9214'
    ])
], indirect=['test_interface_object'])
def test_common_interface_commands(test_interface_object, update, expected):
    assert if_tasks.generate_common_interface_commands(
        test_interface_object, update) == expected


@pytest.mark.parametrize('test_interface_object, update, expected', [
    ('test_interface3', False, ['speed 25g']),
    ('test_interface4', False, ['no speed']),
    ('test_interface3', True, ['speed 25g']),
    ('test_interface4', True, [])
], indirect=['test_interface_object'])
def test_generate_physical_interface_commands(test_interface_object, update, expected):
    assert if_tasks.generate_physical_interface_commands(
        test_interface_object, update) == expected


@pytest.mark.parametrize('test_interface_object, update, expected', [
    ('test_interface3', False, [
        'switchport',
        'switchport mode access',
        'switchport access vlan 77',
        'switchport trunk allowed vlan none'
    ]),
    ('test_interface4', False, [
        'switchport',
        'switchport mode trunk',
        'no switchport trunk native vlan',
        'switchport trunk allowed vlan 5-8,54,77,200,210-213'
    ]),
    ('test_interface5', False, [
        'switchport',
        'switchport mode trunk',
        'switchport trunk native vlan 505',
        'switchport trunk allowed vlan 500-503,505'
    ]),
    ('test_interface3', True, [
        'switchport',
        'switchport mode access',
        'switchport access vlan 77',
        'switchport trunk allowed vlan none'
    ]),
    ('test_interface4', True, [
        'switchport',
        'switchport mode trunk',
        'switchport trunk allowed vlan 5-8,54,77,200,210-213'
    ]),
    ('test_interface5', True, [
        'switchport',
        'switchport mode trunk',
        'switchport trunk native vlan 505',
        'switchport trunk allowed vlan 500-503,505'
    ]),
], indirect=['test_interface_object'])
def test_generate_bridge_mode_commands(test_interface_object, update, expected):
    assert if_tasks.generate_bridged_mode_commands(
        test_interface_object, update) == expected


@pytest.mark.parametrize('test_interface_object, update, expected', [
    ('test_interface1', False, [
        'no vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address 198.18.0.1/24',
        'ip address 198.18.0.2/24 secondary',
        'ip address 198.19.1.1/32 secondary',
        'ipv6 enable',
        'ipv6 address 2001:db8:1:2::1/64',
        'ipv6 address 2001:db8:1::1/128'
    ]),
    ('test_interface2', False, [
        'no vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address virtual 198.18.0.1/24',
        'ip address virtual 198.18.0.2/24 secondary',
        'ipv6 enable',
        'ipv6 address virtual 2001:db8:1:2::1/64',
        'ipv6 address virtual 2001:db8:1::1/128'
    ]),
    ('test_interface6', False, [
        'no switchport',
        'vrf test-vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address 198.18.0.1/24'
    ]),
    ('test_interface1', True, [
        'ip address 198.18.0.1/24',
        'ip address 198.18.0.2/24 secondary',
        'ip address 198.19.1.1/32 secondary',
        'ipv6 enable',
        'ipv6 address 2001:db8:1:2::1/64',
        'ipv6 address 2001:db8:1::1/128'
    ]),
    ('test_interface2', True, [
        'ip address virtual 198.18.0.1/24',
        'ip address virtual 198.18.0.2/24 secondary',
        'ipv6 enable',
        'ipv6 address virtual 2001:db8:1:2::1/64',
        'ipv6 address virtual 2001:db8:1::1/128'
    ]),
    ('test_interface6', True, [
        'no switchport',
        'vrf test-vrf',
        'ip address 198.18.0.1/24'
    ]),
], indirect=['test_interface_object'])
def test_generate_route_mode_commands(test_interface_object, update, expected):
    assert if_tasks.generate_routed_mode_commands(
        test_interface_object, update) == expected


@pytest.mark.parametrize('test_interface_object, update, expected', [
    ('test_interface1', False, [
        'interface Loopback5',
        'description A test loopback [an]',
        'no shutdown',
        'no mtu',
        'no vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address 198.18.0.1/24',
        'ip address 198.18.0.2/24 secondary',
        'ip address 198.19.1.1/32 secondary',
        'ipv6 enable',
        'ipv6 address 2001:db8:1:2::1/64',
        'ipv6 address 2001:db8:1::1/128'
    ]),
    ('test_interface2', False, [
        'interface vlan91',
        'description A test svi [an]',
        'shutdown',
        'mtu 9000',
        'no vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address virtual 198.18.0.1/24',
        'ip address virtual 198.18.0.2/24 secondary',
        'ipv6 enable',
        'ipv6 address virtual 2001:db8:1:2::1/64',
        'ipv6 address virtual 2001:db8:1::1/128'
    ]),
    ('test_interface3', False, [
        'interface Ethernet44',
        'no description',
        'no shutdown',
        'mtu 9214',
        'speed 25g',
        'switchport',
        'switchport mode access',
        'switchport access vlan 77',
        'switchport trunk allowed vlan none'
    ]),
    ('test_interface4', False, [
        'interface Ethernet45',
        'description Test ethernet interface [an]',
        'no shutdown',
        'no mtu',
        'switchport',
        'switchport mode trunk',
        'no switchport trunk native vlan',
        'switchport trunk allowed vlan 5-8,54,77,200,210-213'
    ]),
    ('test_interface5', False, [
        'interface Ethernet46',
        'description Test ethernet interface [an]',
        'no shutdown',
        'no mtu',
        'switchport',
        'switchport mode trunk',
        'switchport trunk native vlan 505',
        'switchport trunk allowed vlan 500-503,505'
    ]),
    ('test_interface6', False, [
        'interface port-channel2',
        'description A test ethernet interface [an]',
        'shutdown',
        'mtu 9000',
        'no switchport',
        'vrf test-vrf',
        'no ip address',
        'no ipv6 address',
        'no ipv6 enable',
        'ip address 198.18.0.1/24'
    ]),
    ('test_interface1', True, [
        'interface Loopback5',
        'description A test loopback [an]',
        'no shutdown',
        'ip address 198.18.0.1/24',
        'ip address 198.18.0.2/24 secondary',
        'ip address 198.19.1.1/32 secondary',
        'ipv6 enable',
        'ipv6 address 2001:db8:1:2::1/64',
        'ipv6 address 2001:db8:1::1/128'
    ]),
    ('test_interface2', True, [
        'interface vlan91',
        'description A test svi [an]',
        'shutdown',
        'mtu 9000',
        'ip address virtual 198.18.0.1/24',
        'ip address virtual 198.18.0.2/24 secondary',
        'ipv6 enable',
        'ipv6 address virtual 2001:db8:1:2::1/64',
        'ipv6 address virtual 2001:db8:1::1/128'
    ]),
    ('test_interface3', True, [
        'interface Ethernet44',
        'no shutdown',
        'mtu 9214',
        'speed 25g',
        'switchport',
        'switchport mode access',
        'switchport access vlan 77',
        'switchport trunk allowed vlan none'
    ]),
    ('test_interface4', True, [
        'interface Ethernet45',
        'description Test ethernet interface [an]',
        'no shutdown',
        'switchport',
        'switchport mode trunk',
        'switchport trunk allowed vlan 5-8,54,77,200,210-213'
    ]),
    ('test_interface5', True, [
        'interface Ethernet46',
        'description Test ethernet interface [an]',
        'no shutdown',
        'switchport',
        'switchport mode trunk',
        'switchport trunk native vlan 505',
        'switchport trunk allowed vlan 500-503,505'
    ]),
    ('test_interface6', True, [
        'interface port-channel2',
        'description A test ethernet interface [an]',
        'shutdown',
        'mtu 9000',
        'no switchport',
        'vrf test-vrf',
        'ip address 198.18.0.1/24'
    ]),
], indirect=['test_interface_object'])
def test_generate_interface_commands(test_interface_object, update, expected):
    assert if_tasks.generate_interface_commands(
        test_interface_object, update) == expected
