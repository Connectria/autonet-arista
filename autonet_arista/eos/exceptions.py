from autonet.core import exceptions as exc


class MixedAnycastUnicastError(exc.DriverRequestError):
    """
    Raised when attempting to mix anycast and unicast addresses
    on the same interface.
    """
    def __init__(self):
        super().__init__('This platform cannot mix anycast and unicast addresses on the '
                         'same interface.')


class NotSwitchport(exc.DriverRequestError):
    """
    Raised when attempting to perform bridge mode operations
    on an interface that doesn't support bridging.
    """
    def __init__(self):
        super().__init__("This platform cannot perform bridging on the specified"
                         "interface type, valid types are 'ethernet' and 'port-channel'.")
