import pytest

from autonet.core.objects import lag as an_lag

from autonet_arista.eos.tasks import lag as task_lag


@pytest.mark.parametrize('test_esi, expected', [
    ('00:be:e9:af:00:3f:60:00:00:00', '00be:e9af:003f:6000:0000'),
    ('00:01:22:ea:fb:99:ed:00:00:00', '0001:22ea:fb99:ed00:0000')
])
def test_format_esi(test_esi, expected):
    assert task_lag.format_esi(test_esi) == expected


@pytest.mark.parametrize('test_lag_name, expected', [
    ('Port-Channel1', '00be:e9af:003f:6000:0000'),
    ('Port-Channel2', '00be:e9af:003f:6a00:0000'),
    ('Port-Channel10', None)
])
def test_get_lag_esi(test_lag_name, expected, test_show_run_port_channel):
    esi = task_lag.get_lag_esi(test_lag_name, test_show_run_port_channel)
    assert esi == expected


@pytest.mark.parametrize('test_lag_name, expected', [
    (None, [
        an_lag.LAG(name='Port-Channel1',
                   members=['Ethernet6', 'Ethernet5'],
                   evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
        an_lag.LAG(name='Port-Channel2',
                   members=['Ethernet2', 'Ethernet3', 'Ethernet4'],
                   evpn_esi='00:be:e9:af:00:3f:6a:00:00:00'),
        an_lag.LAG(name='Port-Channel10',
                   members=['Ethernet16', 'Ethernet15'],
                   evpn_esi=None)
    ]),
    ('Port-Channel1', [
        an_lag.LAG(name='Port-Channel1',
                   members=['Ethernet6', 'Ethernet5'],
                   evpn_esi='00:be:e9:af:00:3f:60:00:00:00')
    ]),
    ('Port-Channel10', [
        an_lag.LAG(name='Port-Channel10',
                   members=['Ethernet16', 'Ethernet15'],
                   evpn_esi=None)
    ])
])
def test_get_lags(test_lag_name, expected, test_show_port_channel, test_show_run_port_channel):
    lags = task_lag.get_lags(test_show_port_channel, test_show_run_port_channel, test_lag_name)
    assert lags == expected


@pytest.mark.parametrize('test_lag, expected', [
    (an_lag.LAG(name='Port-Channel1',
                members=['Ethernet6', 'Ethernet5'],
                evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
     [
         'interface Port-Channel1',
         'evpn ethernet-segment',
         'identifier 00be:e9af:003f:6000:0000',
         'default interface Ethernet6',
         'interface Ethernet6',
         'channel-group 1 mode active',
         'default interface Ethernet5',
         'interface Ethernet5',
         'channel-group 1 mode active'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=['Ethernet8', 'Ethernet22', 'Ethernet48/1'],
                evpn_esi=None),
     [
         'interface Port-Channel22',
         'default interface Ethernet8',
         'interface Ethernet8',
         'channel-group 22 mode active',
         'default interface Ethernet22',
         'interface Ethernet22',
         'channel-group 22 mode active',
         'default interface Ethernet48/1',
         'interface Ethernet48/1',
         'channel-group 22 mode active'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=['Ethernet7'],
                evpn_esi=None),
     [
         'interface Port-Channel22',
         'default interface Ethernet7',
         'interface Ethernet7',
         'channel-group 22 mode active'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=None,
                evpn_esi=None),
     ['interface Port-Channel22'])
])
def test_generate_lag_create_commands(test_lag, expected):
    commands = task_lag.generate_lag_create_commands(test_lag)
    assert commands == expected


@pytest.mark.parametrize('test_new_lag, test_old_lag, update, expected', [
    (
            an_lag.LAG(name='Port-Channel1',
                       members=['Ethernet7', 'Ethernet5'],
                       evpn_esi=None),
            an_lag.LAG(name='Port-Channel1',
                       members=['Ethernet6', 'Ethernet5'],
                       evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
            True,
            [
                'interface Port-Channel1',
                'interface Ethernet7',
                'channel-group 1 mode active'
            ]
    ),
    (
            an_lag.LAG(name='Port-Channel1',
                       members=['eth7', 'Ethernet5'],
                       evpn_esi=None),
            an_lag.LAG(name='Port-Channel1',
                       members=['Ethernet6', 'Ethernet5'],
                       evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
            False,
            [
                'default interface Ethernet6',
                'interface Port-Channel1',
                'no evpn ethernet-segment',
                'interface Ethernet7',
                'channel-group 1 mode active'
            ]
    ),
    (
            an_lag.LAG(name='Port-Channel1',
                       members=None,
                       evpn_esi=None),
            an_lag.LAG(name='Port-Channel1',
                       members=['Ethernet6', 'Ethernet5'],
                       evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
            True,
            [
                'interface Port-Channel1'
            ]
    ),
    (
            an_lag.LAG(name='Port-Channel1',
                       members=None,
                       evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
            an_lag.LAG(name='Port-Channel1',
                       members=['Ethernet6', 'Ethernet5'],
                       evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
            False,
            [
                'default interface Ethernet6',
                'default interface Ethernet5',
                'interface Port-Channel1',
                'evpn ethernet-segment',
                'identifier 00be:e9af:003f:6000:0000'
            ]
    ),
])
def test_generate_lag_update_commands(test_new_lag, test_old_lag, update, expected):
    commands = task_lag.generate_lag_update_commands(test_new_lag, test_old_lag, update)
    assert commands == expected


@pytest.mark.parametrize('test_lag, expected', [
    (an_lag.LAG(name='Port-Channel1',
                members=['Ethernet6', 'Ethernet5'],
                evpn_esi='00:be:e9:af:00:3f:60:00:00:00'),
     [
         'default interface Ethernet6',
         'default interface Ethernet5',
         'no interface Port-Channel1'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=['Ethernet8', 'Ethernet22', 'Ethernet48/1'],
                evpn_esi=None),
     [
         'default interface Ethernet8',
         'default interface Ethernet22',
         'default interface Ethernet48/1',
         'no interface Port-Channel22'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=['Ethernet7'],
                evpn_esi=None),
     [
         'default interface Ethernet7',
         'no interface Port-Channel22'
     ]),
    (an_lag.LAG(name='Port-Channel22',
                members=[],
                evpn_esi=None),
     ['no interface Port-Channel22']),

])
def test_generate_lag_delete_commands(test_lag, expected):
    commands = task_lag.generate_lag_delete_commands(test_lag)
    assert commands == expected
