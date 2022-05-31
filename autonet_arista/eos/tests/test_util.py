import pytest

from autonet.core.objects import interfaces as an_if

from autonet_arista.eos import util


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


@pytest.mark.parametrize('name, expected', [
    ('Ethernet5', False),
    ('Lo22', True),
    ('po1', True),
    ('Vlan88', True),
    ('eth9', False)
])
def test_is_virtual(name, expected):
    assert util.is_virtual(name) == expected


@pytest.mark.parametrize('name, expected', [
    ('Ethernet5', True),
    ('Lo22', False),
    ('po1', True),
    ('Vlan88', False),
    ('eth9', True)
])
def test_is_switchport(name, expected):
    assert util.is_switchport(name) == expected
