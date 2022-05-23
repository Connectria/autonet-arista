import logging
import pyeapi

from typing import Union

from autonet_ng.core import exceptions as exc
from autonet_ng.core.device import AutonetDevice
from autonet_ng.core.objects import interfaces as an_if
from autonet_ng.core.objects import vrf as an_vrf
from autonet_ng.core.objects import vxlan as an_vxlan
from autonet_ng.drivers.driver import DeviceDriver
from pyeapi.client import CommandError

from autonet_arista.eos.tasks import interface as if_task
from autonet_arista.eos.tasks import vrf as vrf_task
from autonet_arista.eos.tasks import vxlan as vxlan_task
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
        try:
            self._exec_admin(f'show interfaces {interface_name}')
            return True
        except CommandError as e:
            if e.command_error == 'Interface does not exist':
                return False
            raise exc.AutonetException("Could not determine if interface exists.")

    def _vxlan_exists(self, vnid: Union[int, str]) -> Union[an_vxlan.VXLAN, bool]:
        """
        Returns the VXLAN object it exists, otherwise returns False.
        """
        try:
            return self._tunnels_vxlan_read(vnid)[0]
        except exc.ObjectNotFound:
            return False

    def _interface_read(self, request_data: str = None) -> an_if.Interface:
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

    def _tunnels_vxlan_read(self, request_data: str = None):
        commands = ('show interfaces vxlan1', 'show running-config section bgp')
        show_int_vxlan, show_bgp_config = self._exec_admin(commands)
        vnid = int(request_data) if request_data else None
        result = vxlan_task.get_vxlans(
            show_int_vxlan,
            show_bgp_config['output'],
            vnid=vnid)

        if request_data and len(result) != 1:
            raise exc.ObjectNotFound
        else:
            return result

    def _tunnels_vxlan_create(self, request_data: an_vxlan.VXLAN) -> an_vxlan.VXLAN:
        if self._vxlan_exists(request_data.id):
            raise exc.ObjectExists

        # Config needs to be done in two stages.  First the tunnel itself is
        # created, which will trigger the device to allocate resources for it.
        # Once those resources are allocated, they are discovered, and then
        # used for the auto-generation of RD and RT.
        commands = vxlan_task.generate_vxlan_commands(vxlan=request_data)
        self._exec_config(commands)
        # Stage one completed.  Now resource allocations are discovered.
        commands = ('show interfaces vxlan1', 'show running-config section bgp')
        show_int_vxlan, show_bgp_config = self._exec_admin(commands)
        commands = vxlan_task.generate_vxlan_evpn_commands(
            request_data, show_int_vxlan, show_bgp_config['output'])
        self._exec_config(commands)
        return self._tunnels_vxlan_read(str(request_data.id))

    def _tunnels_vxlan_delete(self, request_data: str):
        vxlan = self._vxlan_exists(request_data)
        if not vxlan:
            raise exc.ObjectNotFound()
        show_bgp_config, = self._exec_admin('show running-config section bgp')
        commands = vxlan_task.generate_vxlan_delete_commands(vxlan, show_bgp_config['output'])
        self._exec_config(commands)

    def _vrf_read(self, request_data: str = None):
        commands = ['show vrf', 'show running-config section bgp']
        show_vrf, show_bgp_config = self._exec_admin(commands)
        results = vrf_task.get_vrfs(
                show_vrf,
                show_bgp_config['output'],
                vrf=request_data)
        if request_data and len(results) != 1:
            raise exc.ObjectNotFound()
        return results

    def _vrf_create(self, request_data: an_vrf.VRF):
        pass