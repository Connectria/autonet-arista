import pyeapi

from autonet.core import exceptions as exc
from autonet.core.device import AutonetDevice
from autonet.drivers.driver import DeviceDriver

from autonet_arista.eos import util
from autonet_arista.eos.const import PHYSICAL_INTERFACE_TYPES, VIRTUAL_INTERFACE_TYPES


class AristaDriver(DeviceDriver):
    def __init__(self, device: AutonetDevice):
        super().__init__(device)
        self._eapi = pyeapi.connect(host=str(self.device.address),
                                    username=self.device.credentials.username,
                                    password=self.device.credentials.password,
                                    return_node=True)

    def _exec_admin(self, command):
        result = self._eapi.enable(command)
        return result[0]['result'] if 'result' in result[0] else None

    def _interface_read(self, request_data=None):
        interfaces = []
        show_interfaces_command = 'show interfaces'
        if request_data:
            show_interfaces_command += f" {request_data}"
        eos_interfaces = self._exec_admin(show_interfaces_command)
        eos_interface_vlans = self._exec_admin('show interfaces vlans')
        for _, eos_interface in eos_interfaces['interfaces'].items():
            if eos_interface['hardware'] not in PHYSICAL_INTERFACE_TYPES + VIRTUAL_INTERFACE_TYPES or \
                    'Management' in eos_interface['name']:
                # Skip the interfaces we don't care about.
                continue
            interfaces.append(util.get_interface_object(eos_interface, eos_interface_vlans))

        if request_data and len(interfaces) != 1:
            raise exc.ObjectNotFound()
        else:
            return interfaces[0] if request_data else interfaces
