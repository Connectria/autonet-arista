import pytest

from autonet_ng.core import objects as obj

from autonet_arista.eos import util


def test_get_interface_vrf_map(test_eos_vrfs):
    vrf_map = util.get_interface_vrf_map(test_eos_vrfs)
    for if_name in ["Ethernet10", "Ethernet11", "Ethernet12", "Loopback0",
                    "Loopback5", "Vlan4091", "Vlan4092", "Vlan4093"]:
        assert vrf_map[if_name] is None
    for if_name in ['Ethernet1', 'Vlan71', 'Vlan72', 'Vlan4094']:
        assert vrf_map[if_name] == 'TestCust1-Prod'


def test_get_lag_map(test_eos_lags):
    lag_map = util.get_lag_map(test_eos_lags)
    for if_name in ['Ethernet5', 'Ethernet6']:
        assert lag_map[if_name] == 'Port-Channel1'


@pytest.mark.parametrize('test_ipv6_prefix', [
    ('8f4a:edd0::eb65:8423:6d85:8d98/126', '126'),
    ('8cf1:8c12:e545:4eaa:d333:e1be:e145:a0e0/96', '96'),
    ('1c9a:8d83:87ae::21a6:4652:caa9/64', '64'),
    ('9439:6393:5b22:517a:3cf2:66c3:e3a0:c7ce/64', '64'),
    ('ea0e:a6b2:68d4:7b21:62e0:bd6a:acc0:ade7/64', '64'),
    ('c9e5:63f9:c278:a14f:cefa::9d95/48', '48'),
    ('e51a:fc9e:dd36:4924:98dd:4ace:1140:1fc0/56', '56'),
    ('ee1:d581:3938:d72e:9638:7703:2b08:898e/12', '12'),
    ('a48c:a9dd::9589:a337:a62e:4e4d/52', '52'),
    ('7745:eab5:e71e:3b76:9b3b:8d54:16c9:2096/50', '50'),
    ('63a9:d61:eb71:d256:491c:a3bf:a8f5:d473/128', '128'),
    ('d427:2654:4337:bd50:ac5c:b28b:48bc:b9c7/128', '128'),
])
def test_get_v6_mask_length(test_ipv6_prefix):
    """
    Test that `get_v6_mask_length` correctly parses a mask.
    """
    assert util.get_v6_mask_length(test_ipv6_prefix[0]) == test_ipv6_prefix[1]


def test_get_v6_mask_length_failure():
    """
    Test that `get_v6_mask_length` raises appropriate exception
    on failure.
    """
    with pytest.raises(ValueError):
        util.get_v6_mask_length('not_an_ipv6_prefix')


def test_get_ipv4_address_unicast(test_addr_list):
    """
    Test that `get_ipv4_addresses` returns an appropriate
    list of addresses with unicast configuration.
    """
    addresses = util.get_ipv4_addresses(test_addr_list)
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
    addresses = util.get_ipv4_addresses(test_anycast_addr_list)
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
    addresses = util.get_ipv6_addresses(test_v6_addr_list, virtual)
    assert len(addresses) == len(test_v6_addr_list)
    for i, address in enumerate(addresses):
        virtual_type = 'anycast' if virtual else None
        assert address.family == 'ipv6'
        assert address.address == expected[i]
        assert address.virtual == virtual
        assert address.virtual_type == virtual_type


def test_get_route_attributes(test_routed_interface, test_eos_vrfs):
    ra = util.get_route_attributes(test_routed_interface, test_eos_vrfs)
    assert ra.vrf == 'TestCust1-Prod'
    assert len(ra.addresses) == 2
    for address in ra.addresses:
        assert isinstance(address, obj.interfaces.InterfaceAddress)


@pytest.mark.parametrize('if_name, expected', [
    ('Ethernet2', (71, None)),
    ('Ethernet3', (71, [72, 88])),
    ('Ethernet4', (1, None))
])
def test_get_interface_vlan_info(if_name, test_eos_interfaces_vlans, expected):
    untagged, tagged = util.get_interface_vlan_info(if_name, test_eos_interfaces_vlans)
    assert untagged, tagged == expected


def test_get_bridge_attributes(test_bridge_interface, test_eos_interfaces_vlans):
    ba = util.get_bridge_attributes(test_bridge_interface, test_eos_interfaces_vlans)
    assert ba.dot1q_enabled
    assert ba.dot1q_vids == [88, 72]
    assert ba.dot1q_pvid == 71


@pytest.mark.parametrize('test_interface, expected', [
    ('routed', obj.interfaces.InterfaceRouteAttributes),
    ('bridged', obj.interfaces.InterfaceBridgeAttributes)
], indirect=['test_interface'])
def test_get_attributes(test_interface, test_eos_interfaces_vlans, test_eos_vrfs, expected):
    a = util.get_attributes(test_interface, test_eos_interfaces_vlans, test_eos_vrfs)
    assert isinstance(a, expected)


@pytest.mark.parametrize('interface_name, expected', [
    ('Ethernet9.10', 'Ethernet9'),
    ('Port-Channel22.55', 'Port-Channel22'),
    ('Loopback5', None)
])
def test_get_parent_interface_name(interface_name, expected):
    parent = util.get_parent_interface_name(interface_name)
    assert parent == expected


@pytest.mark.parametrize('test_interface, expected', [
    ('routed', obj.interfaces.Interface(
        admin_enabled=True, child=False, description='[an]', duplex='full',
        mode='routed', mtu=1500, name='Vlan71', parent=None,
        physical_address='0C-FE-87-5F-8C-BD', speed=None, virtual=True,
        attributes=obj.interfaces.InterfaceRouteAttributes(
            addresses=[
                obj.interfaces.InterfaceAddress(
                    address='10.0.0.1/24', family='ipv4', virtual=True,
                    virtual_type='anycast'),
                obj.interfaces.InterfaceAddress(
                    address='ea0e:a6b2:68d4:7b21::1/64', family='ipv6', virtual=True,
                    virtual_type='anycast'),
            ],
            vrf='TestCust1-Prod')
    )),
    ('bridged', obj.interfaces.Interface(
        admin_enabled=True, child=False, description='', duplex='full',
        mode='bridged', mtu=9214, name='Ethernet3', parent=None,
        physical_address='0C-FE-87-ED-59-03', speed=1000, virtual=False,
        attributes=obj.interfaces.InterfaceBridgeAttributes(
            dot1q_enabled=True, dot1q_pvid=71, dot1q_vids=[88, 72]
        )
    ))
], indirect=['test_interface'])
def test_get_interface_object(test_interface, test_eos_interfaces_vlans,
                              test_eos_vrfs, test_eos_lags, expected):
    if_obj = util.get_interface_object(test_interface,
                                       test_eos_interfaces_vlans,
                                       test_eos_vrfs, test_eos_lags)
    assert if_obj == expected
