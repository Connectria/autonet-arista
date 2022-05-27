import re

from autonet_ng.core.objects import lag as an_lag
from typing import Union

from autonet_arista.eos.tasks import common as common_task


def format_esi(esi: str) -> str:
    """
    Parse the ESI format provided by Autonet into the format acceptable to
    Arista's CLI/API.
    :param esi: An ESI
    :return:
    """
    # Use the bytes object's `fromhex()` and `hex()` methods to cast to
    # bytes and then back to string of proper format.
    return bytes.fromhex(esi.replace(':', '')).hex(':', bytes_per_sep=2)


def parse_lag_id(lag_name: str) -> str:
    """
    Parses the port-channel name and returns the ID.
    :param lag_name:
    :return:
    """
    return re.search(r'Port-Channel(?P<po_id>\d*)$', lag_name).group('po_id')


def get_lag_esi(lag_name, show_run_port_channel) -> Union[str, None]:
    """
    Gets the configured EVPN ESI for a given LAG from the textual
    running configuration.  Returns the ESI as a string directly from
    the configuration, or None if no ESI is found.
    :param lag_name: The name of the requested LAG
    :param show_run_port_channel: The textual interface configuration of
                                  all port channel interfaces.
    :return:
    """
    config_lines = show_run_port_channel.split('\n')

    if_context_regex = r'interface Port-Channel(?P<po_id>\d*)$'
    es_context_regex = r'evpn ethernet-segment$'
    esi_regex = r'identifier (?P<esi>([0-9abcdef]{4}:){4}[0-9abcdef]{4})$'
    lag_context = parse_lag_id(lag_name)

    if_context = None
    evpn_es_context = False
    for line in config_lines:
        # if we match an interface line, we set the interface context to
        # said result, and reset the value of evpn_es_context.
        if match := re.search(if_context_regex, line):
            if_context = match.group('po_id')
            evpn_es_context = False
        # If we aren't in the right interface context, then we just skip
        # all the rest of the checks.
        if lag_context != if_context:
            continue
        # if we match evpn_es_context, then we set it true.
        if re.search(es_context_regex, line):
            evpn_es_context = True
            continue
        # if we are in evpn_es_context and match an ESI we return the ESI.
        if match := re.search(esi_regex, line):
            if evpn_es_context:
                return match.group('esi')

    return None


def get_lags(show_port_channel: dict, show_run_port_channel: str,
             lag_name: str = None) -> [an_lag.LAG]:
    """
    Get a list of `LAG` objects.  If a given lag name is provided
    then only that LAG is returned.
    :param show_port_channel: The output of 'show port-channel dense'
                              command.
    :param show_run_port_channel: The textual interface configuration of
                                  all port channel interfaces.
    :param lag_name: The name of the requested LAG
    :return:
    """
    lags = []
    # Get the fully qualified LAG name so that it matches up with the
    # name present in the command outputs.
    if lag_name:
        lag_name = common_task.get_fq_if_name(lag_name)
    for name, data in show_port_channel['portChannels'].items():
        # We do not support non LACP channels, so skip them.
        if data['protocol'] != 'lacp':
            continue
        # If a specific lag is requested, we skip until we find it.
        if lag_name and name != lag_name:
            continue
        lags.append(an_lag.LAG(
            name=name,
            members=[x for x, _ in data['ports'].items()],
            evpn_esi=get_lag_esi(name, show_run_port_channel)
        ))

    return lags


def generate_lag_create_commands(lag: an_lag.LAG) -> [str]:
    """
    Generate a list of commands required to create a new LAG on the device.
    :param lag: A `LAG` object.
    :return:
    """
    # Create the interface, and it's ESI if provided.
    commands = [f'interface {lag.name}']
    if lag.evpn_esi:
        commands += [
            'evpn ethernet-segment',
            f'identifier {format_esi(lag.evpn_esi)}'
        ]
    # Bind member interfaces, if they are passed in.
    if lag.members:
        lag_id = parse_lag_id(lag.name)
        for member in lag.members:
            commands += [
                f'default interface {member}',
                f'interface {member}',
                f'channel-group {lag_id} mode active'
            ]

    return commands


def generate_lag_delete_commands(lag: an_lag.LAG) -> [str]:
    """
    Generate a list of commands to destroy a given LAG.
    :param lag: A `LAG` object.
    :return:
    """
    commands = [f'default interface {member}' for member in lag.members]
    commands.append(f'no interface {lag.name}')
    return commands


def generate_lag_update_commands(new_lag: an_lag.LAG, old_lag: an_lag.LAG, update: bool) -> [str]:
    """
    Generates a list of commands to update a given lag from its current
    state to the requested state.
    :param new_lag: The requested `LAG` object.
    :param old_lag: The existing version of the `LAG` object to be
                    modified.
    :param update: True if update operation, and False for a replace
                   operation.
    :return:
    """
    # Regenerate the new_lag.members with fully qualified names so
    # that they may be compared with the fully qualified names that
    # will be present in old_lag.members.
    if new_lag.members:
        new_lag.members = [common_task.get_fq_if_name(member)
                           for member in new_lag.members]
    commands = []
    # Take care of destroying any member configuration that's no
    # longer going to be required.
    if not update:
        # Generate a list of members to be removed.
        new_members = new_lag.members or []
        remove_members = [member for member in old_lag.members
                          if member not in new_members]
        commands += [f'default interface {member}' for member in remove_members]

    # Now enter into the Port-Channel configuration block.
    commands.append(f'interface {new_lag.name}')

    # Handle ESI set or unset, as required.
    if not update and new_lag.evpn_esi is None:
        commands.append('no evpn ethernet-segment')
    if new_lag.evpn_esi:
        commands.append('evpn ethernet-segment')
        commands.append(f'identifier {format_esi(new_lag.evpn_esi)}')

    # And finally add new interfaces.
    lag_id = parse_lag_id(new_lag.name)
    if new_lag.members:
        for member in new_lag.members:
            if member not in old_lag.members:
                commands += [
                    f'interface {member}',
                    f'channel-group {lag_id} mode active'
                ]
    return commands
