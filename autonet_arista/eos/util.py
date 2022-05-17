import logging
import re

from autonet_ng.core.objects import interfaces as an_if
from typing import Union

from autonet_arista.eos.const import DESCRIPTION_TAG, VIRTUAL_INTERFACE_TYPES


def get_v6_mask_length(addr: str) -> str:
    """
    Returns the prefix length of an IPv6 prefix or address.
    :param addr:
    :return:
    """
    regex = r".*/([0-9]*)"
    result = re.search(pattern=regex, string=addr)
    try:
        return result.group(1)
    except Exception as e:
        logging.exception(e)
        raise ValueError(f"Could not parse prefix length from {addr}")


def is_virtual(name: str) -> bool:
    """
    Determine the given interface is a virtual interface type.
    :param name: The interface name.
    :return:
    """
    if_type = re.search(r"([A-z-]*)\d*", name).group(1)
    for virtual_type in ['loopback', 'vlan', 'port-channel']:
        if if_type.lower() in virtual_type:
            return True
    return False


def is_switchport(name: str) -> bool:
    """
    Determine if the given interface supports switchport commands.
    :param name: The interface name.
    :return:
    """
    if_type = re.search(r"([A-z-]*)\d*", name).group(1)
    for virtual_type in ['ethernet', 'port-channel']:
        if if_type.lower() in virtual_type:
            return True
    return False
