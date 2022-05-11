import pyeapi

from autonet_ng.core import exceptions as exc
from autonet_ng.core.device import AutonetDevice
from autonet_ng.drivers.driver import DeviceDriver

from autonet_arista.eos import util
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
            interfaces.append(util.get_interface_object(eos_interface,
                                                        *interface_data[1:]))

        if request_data and len(interfaces) != 1:
            raise exc.ObjectNotFound()
        else:
            return interfaces[0] if request_data else interfaces

