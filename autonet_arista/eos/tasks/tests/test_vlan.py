import pytest

from autonet.core import exceptions as exc
from autonet.core.objects import vlan as an_vlan

from autonet_arista.eos.tasks import vlan as vlan_task


@pytest.mark.parametrize('vlan_id, expected', [
    (None, [
        an_vlan.VLAN(id=2301, name='VLAN2301',
                     bridge_domain=None, admin_enabled=False),
        an_vlan.VLAN(id=1, name='default',
                     bridge_domain=None, admin_enabled=True),
        an_vlan.VLAN(id=71, name='TestCust1-Net1',
                     bridge_domain=None, admin_enabled=True),
        an_vlan.VLAN(id=72, name='TestCust1-Net2',
                     bridge_domain=None, admin_enabled=True)
    ]),
    (71, [
        an_vlan.VLAN(id=71, name='TestCust1-Net1',
                     bridge_domain=None, admin_enabled=True)
    ]),
    (4093, [])
])
def test_get_vlan(vlan_id, expected, test_show_vlan):
    vlans = vlan_task.get_vlans(test_show_vlan, vlan_id)
    assert vlans == expected


@pytest.mark.parametrize('test_vlan, expected', [
    (
            an_vlan.VLAN(id=71, name='TestCust1-Net1',
                         bridge_domain=None, admin_enabled=True),
            [
                'vlan 71',
                'state active',
                'name TestCust1-Net1'
            ]
    ),
    (
            an_vlan.VLAN(id=71, name=None,
                         bridge_domain=None, admin_enabled=False),
            [
                'vlan 71',
                'state suspend',
            ]
    )
])
def test_generate_create_vlan_commands(test_vlan, expected):
    commands = vlan_task.generate_vlan_create_commands(test_vlan)
    assert commands == expected


def test_generate_create_vlan_commands_errors():
    test_vlan = an_vlan.VLAN(id=71, name="Invalid Name",
                             bridge_domain=None, admin_enabled=False)
    with pytest.raises(exc.AutonetException) as e:
        vlan_task.generate_vlan_create_commands(test_vlan)
        assert isinstance(e, exc.AutonetException)


@pytest.mark.parametrize('test_vlan, expected', [
    (
            an_vlan.VLAN(id=71, name='TestCust1-Net1',
                         bridge_domain=None, admin_enabled=None),
            [
                'vlan 71',
                'state active',
                'name TestCust1-Net1'
            ]
    ),
    (
            an_vlan.VLAN(id=71, name=None,
                         bridge_domain=None, admin_enabled=False),
            [
                'vlan 71',
                'state suspend',
                'no name'
            ]
    )
])
def test_generate_update_vlan_commands(test_vlan, expected):
    commands = vlan_task.generate_vlan_update_commands(test_vlan)
    assert commands == expected


def test_generate_update_vlan_commands_errors():
    test_vlan = an_vlan.VLAN(id=71, name="Invalid Name",
                             bridge_domain=None, admin_enabled=False)
    with pytest.raises(exc.AutonetException) as e:
        vlan_task.generate_vlan_update_commands(test_vlan)
        assert isinstance(e, exc.AutonetException)


@pytest.mark.parametrize('test_vlan_id, expected', [
    (6, ['no vlan 6']),
    ('88', ['no vlan 88'])
])
def test_generate_delete_vlan_commands(test_vlan_id, expected):
    commands = vlan_task.generate_vlan_delete_commands(test_vlan_id)
    assert commands == expected
