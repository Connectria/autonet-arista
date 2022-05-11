import ipaddress
import pytest


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
