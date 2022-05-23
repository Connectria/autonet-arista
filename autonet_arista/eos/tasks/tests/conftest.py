import ipaddress
import pytest

from autonet_ng.core.objects import interfaces as an_if

TEST_INTERFACE_1 = an_if.Interface(
    name='Loopback5', mode='routed', description='A test loopback',
    admin_enabled=True, attributes=an_if.InterfaceRouteAttributes(
        vrf=None, addresses=[
            an_if.InterfaceAddress(family='ipv4', address='198.18.0.1/24',
                                   virtual=False, virtual_type=None),
            an_if.InterfaceAddress(family='ipv4', address='198.18.0.2/24',
                                   virtual=False, virtual_type=None),
            an_if.InterfaceAddress(family='ipv4', address='198.19.1.1/32',
                                   virtual=False, virtual_type=None),
            an_if.InterfaceAddress(family='ipv6', address='2001:db8:1:2::1/64',
                                   virtual=False, virtual_type=None),
            an_if.InterfaceAddress(family='ipv6', address='2001:db8:1::1/128',
                                   virtual=False, virtual_type=None)
        ]),
)
TEST_INTERFACE_2 = an_if.Interface(
    name='vlan91', mode='routed', description='A test svi',
    admin_enabled=False, mtu=9000, attributes=an_if.InterfaceRouteAttributes(
        vrf=None, addresses=[
            an_if.InterfaceAddress(family='ipv4', address='198.18.0.1/24',
                                   virtual=True, virtual_type='anycast'),
            an_if.InterfaceAddress(family='ipv4', address='198.18.0.2/24',
                                   virtual=True, virtual_type='anycast'),
            an_if.InterfaceAddress(family='ipv6', address='2001:db8:1:2::1/64',
                                   virtual=True, virtual_type='anycast'),
            an_if.InterfaceAddress(family='ipv6', address='2001:db8:1::1/128',
                                   virtual=True, virtual_type='anycast')
        ]),
)
TEST_INTERFACE_3 = an_if.Interface(
    name='Ethernet44', mode='bridged', description=None,
    admin_enabled=True, mtu=9214, speed=25000, duplex='full',
    attributes=an_if.InterfaceBridgeAttributes(
        dot1q_enabled=False, dot1q_pvid=77)
)
TEST_INTERFACE_4 = an_if.Interface(
    name='Ethernet45', mode='bridged', description='Test ethernet interface',
    admin_enabled=True, attributes=an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True,
        dot1q_vids=[5, 6, 7, 8, 200, 210, 211, 212, 213, 77, 54])
)
TEST_INTERFACE_5 = an_if.Interface(
    name='Ethernet46', mode='bridged', description='Test ethernet interface',
    admin_enabled=True, attributes=an_if.InterfaceBridgeAttributes(
        dot1q_enabled=True,
        dot1q_pvid=505,
        dot1q_vids=[500, 501, 502, 503, 505])
)
TEST_INTERFACE_6 = an_if.Interface(
    name='port-channel2', mode='routed', description='A test ethernet interface',
    admin_enabled=False, mtu=9000, attributes=an_if.InterfaceRouteAttributes(
        vrf='test-vrf', addresses=[
            an_if.InterfaceAddress(family='ipv4', address='198.18.0.1/24',
                                   virtual=False, virtual_type=None),
        ]),
)
TEST_INTERFACES = {
    'test_interface1': TEST_INTERFACE_1,
    'test_interface2': TEST_INTERFACE_2,
    'test_interface3': TEST_INTERFACE_3,
    'test_interface4': TEST_INTERFACE_4,
    'test_interface5': TEST_INTERFACE_5,
    'test_interface6': TEST_INTERFACE_6,
}


@pytest.fixture()
def test_interface_object(request):
    return TEST_INTERFACES[request.param]


@pytest.fixture
def test_ipv6_prefix():
    return '2001:DB8:7ac0:beef::/64'


@pytest.fixture
def test_addr_list():
    return [
        {
            "secondaryIpsOrderedList": [
                {
                    "maskLen": 32,
                    "address": "198.18.100.8"
                },
                {
                    "maskLen": 32,
                    "address": "198.18.101.8"
                }
            ],
            "broadcastAddress": "255.255.255.255",
            "virtualSecondaryIps": {},
            "dhcp": False,
            "secondaryIps": {
                "198.18.100.8": {
                    "maskLen": 32,
                    "address": "198.18.100.8"
                },
                "198.18.101.8": {
                    "maskLen": 32,
                    "address": "198.18.101.8"
                }
            },
            "primaryIp": {
                "maskLen": 24,
                "address": "198.18.0.1"
            },
            "virtualSecondaryIpsOrderedList": [],
            "virtualIp": {
                "maskLen": 0,
                "address": "0.0.0.0"
            }
        }
    ]


@pytest.fixture
def test_anycast_addr_list():
    return [
        {
            "secondaryIpsOrderedList": [],
            "broadcastAddress": "255.255.255.255",
            "virtualSecondaryIps": {},
            "dhcp": False,
            "secondaryIps": {},
            "primaryIp": {
                "maskLen": 0,
                "address": "0.0.0.0"
            },
            "virtualSecondaryIpsOrderedList": [],
            "virtualIp": {
                "maskLen": 24,
                "address": "10.0.0.1"
            }
        }
    ]


@pytest.fixture
def test_v6_addr_list(request):
    # Test will offer a list of prefixes, so we'll
    # generate and return addresses in kind.
    addresses = []
    for prefix in request.param:
        ip = ipaddress.ip_interface(prefix)
        addresses.append(
            {
                "subnet": str(ip.network),
                "dadfailed": False,
                "active": True,
                "address": str(ip.ip)
            }
        )
    return addresses


@pytest.fixture
def test_eos_vrfs():
    """
    Build the structure of a `show vrfs` response that is used
    by the `test_generate_interface_vrf_map`
    :return:
    """
    return {
        "vrfs": {
            "default": {
                "routeDistinguisher": "",
                "vrfState": "up",
                "interfacesV6": [
                    "Loopback5",
                    "Vlan4091",
                    "Vlan4092",
                    "Vlan4093"
                ],
                "interfacesV4": [
                    "Ethernet10",
                    "Ethernet11",
                    "Ethernet12",
                    "Loopback0",
                    "Loopback5",
                    "Vlan4091",
                    "Vlan4092",
                    "Vlan4093"
                ],
                "interfaces": [
                    "Ethernet10",
                    "Ethernet11",
                    "Ethernet12",
                    "Loopback0",
                    "Loopback5",
                    "Vlan4091",
                    "Vlan4092",
                    "Vlan4093"
                ],
                "protocols": {
                    "ipv4": {
                        "routingState": "up",
                        "protocolState": "up",
                        "supported": True
                    },
                    "ipv6": {
                        "routingState": "down",
                        "protocolState": "up",
                        "supported": True
                    }
                }
            },
            "TestCust1-Prod": {
                "routeDistinguisher": "192.168.0.101:4094",
                "vrfState": "up",
                "interfacesV6": [
                    "Vlan71",
                    "Vlan4094"
                ],
                "interfacesV4": [
                    "Ethernet1",
                    "Vlan71",
                    "Vlan72",
                    "Vlan4094"
                ],
                "interfaces": [
                    "Ethernet1",
                    "Vlan71",
                    "Vlan72",
                    "Vlan4094"
                ],
                "protocols": {
                    "ipv4": {
                        "routingState": "up",
                        "protocolState": "up",
                        "supported": True
                    },
                    "ipv6": {
                        "routingState": "up",
                        "protocolState": "up",
                        "supported": True
                    }
                }
            },
            "mgmt-if": {
                "routeDistinguisher": "",
                "vrfState": "up",
                "interfacesV6": [],
                "interfacesV4": [
                    "Management1"
                ],
                "interfaces": [
                    "Management1"
                ],
                "protocols": {
                    "ipv4": {
                        "routingState": "up",
                        "protocolState": "up",
                        "supported": True
                    },
                    "ipv6": {
                        "routingState": "down",
                        "protocolState": "up",
                        "supported": True
                    }
                }
            }
        }
    }


@pytest.fixture
def test_eos_lags():
    return {
        "portChannels": {
            "Port-Channel1": {
                "recircFeature": [],
                "fallbackState": "unconfigured",
                "minSpeed": "0 gbps",
                "minLinks": 0,
                "currWeight": 1,
                "maxWeight": 16,
                "inactivePorts": {
                    "Ethernet5": {
                        "reasonUnconfigured": "waiting for LACP response",
                        "timeBecameInactive": 0.0
                    }
                },
                "activePorts": {
                    "Ethernet6": {
                        "protocol": "lacp",
                        "weight": 1,
                        "timeBecameActive": 1646592377.4616487,
                        "lacpMode": "active"
                    }
                },
                "inactiveLag": False
            }
        }
    }


@pytest.fixture
def test_vrf_map():
    return {
        'Ethernet10': 'default',
        'Ethernet11': 'default',
        'Ethernet12': 'default',
        'Loopback0': 'default',
        'Loopback5': 'default',
        'Vlan4091': 'default',
        'Vlan4092': 'default',
        'Vlan4093': 'default',
        'Ethernet1': 'TestCust1-Prod',
        'Vlan71': 'TestCust1-Prod',
        'Vlan72': 'TestCust1-Prod',
        'Vlan4094': 'TestCust1-Prod',
        'Management1': 'mgmt-if'
    }


@pytest.fixture
def test_routed_interface():
    return {
        "lastStatusChangeTimestamp": 1644614921.9291403,
        "name": "Vlan71",
        "interfaceStatus": "connected",
        "burnedInAddress": "0c:fe:87:5f:8c:bd",
        "l2Mru": 0,
        "mtu": 1500,
        "hardware": "vlan",
        "bandwidth": 0,
        "forwardingModel": "routed",
        "lineProtocolStatus": "up",
        "l3MtuConfigured": False,
        "interfaceAddress": [
            {
                "secondaryIpsOrderedList": [],
                "broadcastAddress": "255.255.255.255",
                "virtualSecondaryIps": {},
                "dhcp": False,
                "secondaryIps": {},
                "primaryIp": {
                    "maskLen": 0,
                    "address": "0.0.0.0"
                },
                "virtualSecondaryIpsOrderedList": [],
                "virtualIp": {
                    "maskLen": 24,
                    "address": "10.0.0.1"
                }
            }
        ],
        "interfaceAddressIp6": {
            "addrSource": "manual",
            "globalUnicastIp6s": [
                {
                    "subnet": "ea0e:a6b2:68d4:7b21::/64",
                    "dadfailed": False,
                    "active": False,
                    "address": "ea0e:a6b2:68d4:7b21::1"
                }
            ],
            "linkLocalIp6": {
                "subnet": "fe80::/64",
                "dadfailed": False,
                "active": True,
                "address": "fe80::efe:87ff:fe5f:8cbd"
            },
            "globalAddressesAreVirtual": True
        },
        "physicalAddress": "0c:fe:87:5f:8c:bd",
        "description": "[an]"
    }


@pytest.fixture
def test_bridge_interface():
    return {
        "loopbackMode": "loopbackNone",
        "lastStatusChangeTimestamp": 1644614920.7884653,
        "lanes": 0,
        "name": "Ethernet3",
        "interfaceStatus": "connected",
        "autoNegotiate": "unknown",
        "burnedInAddress": "0c:fe:87:ed:59:03",
        "l2Mru": 0,
        "interfaceStatistics": {
            "inBitsRate": 0.0,
            "inPktsRate": 0.0,
            "outBitsRate": 0.0,
            "updateInterval": 300.0,
            "outPktsRate": 0.0
        },
        "mtu": 9214,
        "hardware": "ethernet",
        "duplex": "duplexFull",
        "bandwidth": 1000000000,
        "forwardingModel": "bridged",
        "lineProtocolStatus": "up",
        "l3MtuConfigured": False,
        "interfaceCounters": {
            "outBroadcastPkts": 5,
            "outUcastPkts": 4,
            "totalOutErrors": 0,
            "inMulticastPkts": 0,
            "counterRefreshTime": 1652158345.038377,
            "inBroadcastPkts": 0,
            "outputErrorsDetail": {
                "deferredTransmissions": 0,
                "txPause": 0,
                "collisions": 0,
                "lateCollisions": 0
            },
            "inOctets": 0,
            "outDiscards": 0,
            "outOctets": 571073445,
            "inUcastPkts": 0,
            "inTotalPkts": 0,
            "inputErrorsDetail": {
                "runtFrames": 0,
                "rxPause": 0,
                "fcsErrors": 0,
                "alignmentErrors": 0,
                "giantFrames": 0,
                "symbolErrors": 0
            },
            "linkStatusChanges": 2,
            "outMulticastPkts": 4014417,
            "totalInErrors": 0,
            "inDiscards": 0
        },
        "interfaceAddress": [],
        "physicalAddress": "0c:fe:87:ed:59:03",
        "description": ""
    }


@pytest.fixture
def test_eos_interfaces_vlans():
    return {
        "interfaces": {
            "Ethernet2": {
                "untaggedVlan": 71
            },
            "Ethernet3": {
                "taggedVlans": [
                    88,
                    72
                ],
                "untaggedVlan": 71
            },
            "Ethernet4": {
                "untaggedVlan": 1
            }
        }
    }


@pytest.fixture
def test_interface(request, test_routed_interface, test_bridge_interface):
    if request.param == 'routed':
        return test_routed_interface
    if request.param == 'bridged':
        return test_bridge_interface
    return None


@pytest.fixture
def test_show_vrf():
    # This is a partial datastructure compared to what the device
    # would actually return.
    return {
        'vrfs': {
            'blue': {
                'routeDistinguisher': '198.18.0.101:4091',
                'protocols': {
                    'ipv4': {
                        'routingState': 'up'
                    },
                    'ipv6': {
                        'routingState': 'down'
                    }
                }
            },
            'red': {
                'routeDistinguisher': '198.18.0.101:4094',
                'protocols': {
                    'ipv4': {
                        'routingState': 'up'
                    },
                    'ipv6': {
                        'routingState': 'up'
                    }
                }
            }
        }
    }


@pytest.fixture
def test_show_int_vxlan():
    # This is a partial datastructure compared to what the device
    # would actually return. 
    return {
        'interfaces': {
            'Vxlan1': {
                'srcIpAddr': '192.168.0.101',
                'vrfToVniMap': {
                    'red': 20000,
                    'blue': 20001
                },
                'vlanToVniMap': {
                    '4093': {
                        'source': 'evpn',
                        'vni': 20001
                    },
                    '4092': {
                        'source': 'evpn',
                        'vni': 11000
                    },
                    '4091': {
                        'source': 'evpn',
                        'vni': 111001
                    },
                    '72': {
                        'source': '',
                        'vni': 70002
                    },
                    '71': {
                        'source': '',
                        'vni': 70001
                    },
                    '4094': {
                        'source': 'evpn',
                        'vni': 20000
                    }
                }
            }
        }
    }


@pytest.fixture
def test_bgp_text_config():
    return """
router bgp 65002
   router-id 198.18.0.101
   neighbor overlay peer group
   neighbor overlay remote-as 65001
   neighbor overlay update-source Loopback0
   neighbor overlay allowas-in 1
   neighbor overlay ebgp-multihop 2
   neighbor overlay send-community extended
   neighbor overlay maximum-routes 12000
   neighbor underlay peer group
   neighbor underlay remote-as 65001
   neighbor underlay allowas-in 1
   neighbor underlay maximum-routes 12000
   neighbor 198.18.0.1 peer group overlay
   neighbor 198.18.0.2 peer group overlay
   neighbor 198.18.0.3 peer group overlay
   neighbor 198.18.1.0 peer group underlay
   neighbor 198.18.2.0 peer group underlay
   neighbor 198.18.3.0 peer group underlay
   !
   vlan 71
      rd 198.18.0.101:71
      route-target import 65002:70001
      route-target export 65002:70001
      route-target export 65002:10000
      redistribute learned
   !
   vlan 72
      rd 198.18.0.101:72
      route-target import 65002:70002
      route-target export 65002:70002
      redistribute learned
   !
   address-family evpn
      neighbor overlay activate
      no neighbor underlay activate
   !
   address-family ipv4
      no neighbor overlay activate
      network 192.168.0.101/32
   !
   vrf red
      rd 198.18.0.101:4094
      route-target import evpn 65002:20000
      route-target export evpn 65002:20000
      route-target both 65002:255555
      neighbor 198.19.2.1 remote-as 65408
      neighbor 198.19.2.1 remove-private-as all replace-as
      neighbor 198.19.2.1 maximum-routes 12000
      redistribute connected
      redistribute static
      redistribute attached-host
   vrf blue
      rd 198.18.0.101:4091
      route-target import evpn 65002:20001
      route-target export evpn 65002:20001
      route-target import vpn-ipv4 65002:20001
      route-target export vpn-ipv4 65002:20001
      router-id 198.18.0.101
      neighbor 198.19.3.1 remote-as 65499
      neighbor 198.19.3.1 remove-private-as all replace-as
      neighbor 198.19.3.1 maximum-routes 12000
      redistribute connected
      redistribute static
      redistribute attached-host
    """


@pytest.fixture
def test_bgp_config():
    return {
        'asn': '65002',
        'rid': '198.18.0.101',
        'vlans': {
            '71': {
                'export_targets': ['65002:70001', '65002:10000'],
                'import_targets': ['65002:70001'],
                'rd': '198.18.0.101:71'
            },
            '72': {
                'export_targets': ['65002:70002'],
                'import_targets': ['65002:70002'],
                'rd': '198.18.0.101:72'
            }
        },
        'vrfs': {
            'blue': {
                'export_targets': {
                    'evpn': ['65002:20001'],
                    'vpn-ipv4': ['65002:20001'],
                    'vpn-ipv6': [],
                },
                'import_targets': {
                    'evpn': ['65002:20001'],
                    'vpn-ipv4': ['65002:20001'],
                    'vpn-ipv6': [],
                },
                'rd': '198.18.0.101:4091',
                'rid': '198.18.0.101'
            },
            'red': {
                'export_targets': {
                    'evpn': ['65002:20000', '65002:255555'],
                    'vpn-ipv4': ['65002:255555'],
                    'vpn-ipv6': ['65002:255555'],
                },
                'import_targets': {
                    'evpn': ['65002:20000', '65002:255555'],
                    'vpn-ipv4': ['65002:255555'],
                    'vpn-ipv6': ['65002:255555']
                },
                'rd': '198.18.0.101:4094'
            }
        }
    }
