import logging

import pyeapi

from autonet_ng.core import exceptions as exc
from autonet_ng.core.device import AutonetDevice
from autonet_ng.core.objects import interfaces as an_if
from autonet_ng.drivers.driver import DeviceDriver
from pyeapi.client import CommandError

from autonet_arista.eos.tasks import interface as if_task
from autonet_arista.eos.const import PHYSICAL_INTERFACE_TYPES, VIRTUAL_INTERFACE_TYPES


class AristaDriver(DeviceDriver):
    def __init__(self, device: AutonetDevice):
        super().__init__(device)
        self._eapi = pyeapi.connect(host=str(self.device.address),
                                    username=self.device.credentials.username,
                                    password=self.device.credentials.password,
                                    return_node=True)

    def _exec_admin(self, *commands):
        results = self._eapi.enable(*commands)
        return tuple([r['result'] for r in results])

    def _exec_config(self, commands):
        try:
            self._eapi.configure_session()
            self._eapi.config(commands)
            self._eapi.commit()
        except Exception as e:
            logging.exception(e)
            self._eapi.abort()
        return

    def _interface_exists(self, interface_name) -> bool:
        """
        Determine if interface already exists.
        :param interface_name:
        :return:
        """
        try:
            self._exec_admin(f'show interfaces {interface_name}')
            return True
        except CommandError as e:
            if e.command_error == 'Interface does not exist':
                return False
            raise exc.AutonetException("Could not determine if interface exists.")

    def _interface_read(self, request_data=None):
        interfaces = []
        show_interfaces_command = 'show interfaces'
        if request_data:
            show_interfaces_command += f" {request_data}"
        show_commands = (show_interfaces_command, 'show interfaces vlans',
                         'show vrf', 'show port-channel detailed')
        interface_data = self._exec_admin(show_commands)
        for _, eos_interface in interface_data[0]['interfaces'].items():
            if eos_interface['hardware'] \
                    not in PHYSICAL_INTERFACE_TYPES + VIRTUAL_INTERFACE_TYPES \
                    or 'Management' in eos_interface['name']:
                # Skip the interfaces we don't care about.
                continue
            interfaces.append(if_task.get_interface_object(
                eos_interface, *interface_data[1:]))

        if request_data and len(interfaces) != 1:
            raise exc.ObjectNotFound()
        else:
            return interfaces[0] if request_data else interfaces

    def _interface_create(self, request_data: an_if.Interface) -> an_if.Interface:
        if self._interface_exists(request_data.name):
            raise exc.ObjectExists

        commands = if_task.generate_interface_commands(request_data)
        self._exec_config(commands)

        return self._interface_read(request_data.name)

    def _interface_update(self, request_data: an_if.Interface, update) -> an_if.Interface:
        if not self._interface_exists(request_data.name):
            raise exc.ObjectNotFound

        commands = if_task.generate_interface_commands(request_data, update=update)
        self._exec_config(commands)

        return self._interface_read(request_data.name)

    def _interface_delete(self, request_data: str):
        if not self._interface_exists(request_data):
            raise exc.ObjectNotFound

        commands = if_task.generate_delete_commands(interface_name=request_data)
        self._exec_config(commands)
