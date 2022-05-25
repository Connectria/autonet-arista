import re

from typing import Union

from autonet_ng.core import exceptions as exc
from autonet_ng.core.objects import vlan as an_vlan


def get_vlans(show_vlan: dict, vlan_id: Union[str, int] = None):
    """
    Gets a list of `VLAN` objects.  If vlan_id is specified, then
    only the matching VLAN will be returned.
    :param show_vlan: The output of the 'show vlan' command.
    :param vlan_id: The requested VLAN ID.
    :return:
    """
    vlans = []
    for vid, vlan in show_vlan['vlans'].items():
        # We don't care about internal or dynamically configured VLANs.
        if vlan['dynamic']:
            continue
        # If only one is requested we skip until we find it.
        if vlan_id and int(vlan_id) != int(vid):
            continue
        vlans.append(an_vlan.VLAN(
            id=int(vid),
            name=vlan['name'],
            admin_enabled=True if vlan['status'] == 'active' else False,
            bridge_domain=None  # Platform doesn't support bridge domains.
        ))

    return vlans


def generate_vlan_create_commands(vlan: an_vlan.VLAN) -> [str]:
    """
    Generates a list of commands required to create the VLAN defined
    in the `vlan` object.
    :param vlan: A `VLAN` object.
    :return:
    """
    commands = [
        f'vlan {vlan.id}',
        f'state {"active" if vlan.admin_enabled else "suspend"}'
    ]
    if vlan.name:
        if re.search(r'\s', vlan.name):
            raise exc.AutonetException("VLAN name cannot contain whitespace.")
        else:
            commands.append(f'name {vlan.name}')

    return commands


def generate_vlan_delete_commands(vlan_id: Union[str, int]) -> [str]:
    """
    Generates the list of commands required to delete the VLAN as
    identified by its VLAN ID.
    :param vlan_id:
    :return:
    """
    return [f'no vlan {vlan_id}']
