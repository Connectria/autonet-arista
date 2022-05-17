VIRTUAL_INTERFACE_TYPES = ['loopback', 'vlan', 'portChannel', 'subinterface']
PHYSICAL_INTERFACE_TYPES = ['ethernet']
DESCRIPTION_TAG = '[an]'

SPEED_DUPLEX_MAP = {
    '100full': (100, 'full'),
    '100g': (100000, None),
    '100half': (100, 'half'),
    '10full': (10, 'full'),
    '10g': (10000, None),
    '10half': (10, 'half'),
    '1g': (1000, None),
    '200g': (200000, None),
    '25g': (25000, None),
    '400g': (400000, None),
    '40g': (40000, None),
    '50g': (50000, None),
    'auto': ('auto', None),
}
"""Mapping of speed/duplex pairs to the appropriate command.  Combinations that are
outside the scope of Autonet's purpose (such as breakouts) are omitted.  None is used
when duplex does not apply"""