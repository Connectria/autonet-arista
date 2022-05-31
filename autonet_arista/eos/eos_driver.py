import logging
import pyeapi

from typing import List, Union

from autonet.core.device import AutonetDevice
from autonet.core.objects import interfaces as an_if
from autonet.core.objects import lag as an_lag
from autonet.core.objects import vlan as an_vlan
from autonet.core.objects import vrf as an_vrf
from autonet.core.objects import vxlan as an_vxlan
from autonet.drivers.driver import DeviceDriver
from pyeapi.client import CommandError

from autonet_arista.eos.tasks import interface as if_task
from autonet_arista.eos.tasks import lag as lag_task
from autonet_arista.eos.tasks import vlan as vlan_task
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

    def _interface_read(self, request_data: str = None) -> Union[List[an_if.Interface], an_if.Interface]:
        interfaces = []
        show_interfaces_command = 'show interfaces'
        if request_data:
            show_interfaces_command += f" {request_data}"
        show_commands = (show_interfaces_command, 'show interfaces vlans',
                         'show vrf', 'show port-channel detailed')

        try:
            interface_data = self._exec_admin(show_commands)
        # Handle interface not found gracefully.
        except CommandError:
            return []

        for _, eos_interface in interface_data[0]['interfaces'].items():
            if eos_interface['hardware'] \
                    not in PHYSICAL_INTERFACE_TYPES + VIRTUAL_INTERFACE_TYPES \
                    or 'Management' in eos_interface['name']:
                # Skip the interfaces we don't care about.
                continue
            interfaces.append(if_task.get_interface_object(
                eos_interface, *interface_data[1:]))

        return interfaces[0] if request_data else interfaces

    def _interface_create(self, request_data: an_if.Interface) -> an_if.Interface:
        commands = if_task.generate_interface_commands(request_data)
        self._exec_config(commands)
        return self._interface_read(request_data.name)

    def _interface_update(self, request_data: an_if.Interface, update) -> an_if.Interface:
        commands = if_task.generate_interface_commands(request_data, update=update)
        self._exec_config(commands)
        return self._interface_read(request_data.name)

    def _interface_delete(self, request_data: str):
        commands = if_task.generate_delete_commands(interface_name=request_data)
        self._exec_config(commands)

    def _tunnels_vxlan_read(self, request_data: str = None) -> Union[List[an_vxlan.VXLAN], an_vxlan.VXLAN]:
        commands = ('show interfaces vxlan1', 'show running-config section bgp')
        show_int_vxlan, show_bgp_config = self._exec_admin(commands)
        vnid = int(request_data) if request_data else None
        results = vxlan_task.get_vxlans(
            show_int_vxlan,
            show_bgp_config['output'],
            vnid=vnid)

        if request_data and len(results) == 1:
            return results[0]
        else:
            return results

    def _tunnels_vxlan_create(self, request_data: an_vxlan.VXLAN) -> an_vxlan.VXLAN:
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
        vxlan = self._tunnels_vxlan_read(request_data)
        show_bgp_config, = self._exec_admin('show running-config section bgp')
        commands = vxlan_task.generate_vxlan_delete_commands(vxlan, show_bgp_config['output'])
        self._exec_config(commands)

    def _vrf_read(self, request_data: str = None) -> Union[List[an_vrf.VRF], an_vrf.VRF]:
        commands = ['show vrf', 'show running-config section bgp']
        show_vrf, show_bgp_config = self._exec_admin(commands)
        results = vrf_task.get_vrfs(
            show_vrf,
            show_bgp_config['output'],
            vrf=request_data)
        if request_data and len(results) == 1:
            return results[0]
        else:
            return results

    def _vrf_create(self, request_data: an_vrf.VRF) -> an_vrf.VRF:
        show_bgp_config, = self._exec_admin('show running-config section bgp')
        commands = vrf_task.generate_create_vrf_commands(request_data, show_bgp_config['output'])
        self._exec_config(commands)
        return self._vrf_read(request_data.name)

    def _vrf_delete(self, request_data: str) -> None:
        vrf = self._vrf_read(request_data)
        show_bgp_config, = self._exec_admin('show running-config section bgp')
        commands = vrf_task.generate_delete_vrf_commands(vrf, show_bgp_config['output'])
        self._exec_config(commands)

    def _bridge_vlan_read(self, request_data: Union[str, int]) -> Union[List[an_vlan.VLAN], an_vlan.VLAN]:
        commands = ['show vlan']
        show_vlan, = self._exec_admin(commands)
        results = vlan_task.get_vlans(show_vlan, vlan_id=request_data)

        if request_data and len(results) == 1:
            return results[0]
        else:
            return results

    def _bridge_vlan_create(self, request_data: an_vlan.VLAN) -> an_vlan.VLAN:
        commands = vlan_task.generate_vlan_create_commands(vlan=request_data)
        self._exec_config(commands)
        return self._bridge_vlan_read(request_data.id)

    def _bridge_vlan_update(self, request_data: an_vlan.VLAN, update: bool) -> an_vlan.VLAN:
        if update:
            commands = vlan_task.generate_vlan_update_commands(vlan=request_data)
        else:
            commands = vlan_task.generate_vlan_create_commands(vlan=request_data)
        self._exec_config(commands)
        return self._bridge_vlan_read(request_data.id)

    def _bridge_vlan_delete(self, request_data: str) -> None:
        commands = vlan_task.generate_vlan_delete_commands(vlan_id=request_data)
        self._exec_config(commands)

    def _interface_lag_read(self, request_data: str) -> Union[List[an_lag.LAG], an_lag.LAG]:
        commands = [
            'show port-channel dense',
            'show running-config section interface Port-Channel'
        ]

        show_port_channel, show_run_port_channel = self._exec_admin(commands)
        results = lag_task.get_lags(
            show_port_channel, show_run_port_channel['output'], lag_name=request_data)

        if request_data and len(results) == 1:
            return results[0]
        return results

    def _interface_lag_create(self, request_data: an_lag.LAG) -> an_lag.LAG:
        commands = lag_task.generate_lag_create_commands(request_data)
        self._exec_config(commands)
        return self._interface_lag_read(request_data.name)

    def _interface_lag_update(self, request_data: an_lag.LAG, update: bool) -> an_lag.LAG:
        new_lag = request_data
        old_lag = self._interface_lag_read(new_lag.name)
        if not update and not old_lag:
            commands = lag_task.generate_lag_create_commands(new_lag)
        else:
            commands = lag_task.generate_lag_update_commands(new_lag, old_lag, update)
        self._exec_config(commands)
        return self._interface_lag_read(new_lag.name)

    def _interface_lag_delete(self, request_data: str) -> None:
        lag = self._interface_lag_read(request_data=request_data)
        commands = lag_task.generate_lag_delete_commands(lag)
        self._exec_config(commands)
