
import logging
from classes.protocol_settings import Registry_Type,protocol_settings

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .transport_base import transport_base
    from configparser import SectionProxy

class transport_base:
    protocolSettings : 'protocol_settings'
    device_name : str = ''
    device_serial_number : str = ''
    device_manufacturer : str = ''
    device_model : str = ''
    bridge : str = ''

    __log : logging.Logger = logging.getLogger(__name__)

    def __init__(self, settings : 'SectionProxy' = None, protocolSettings : 'protocol_settings' = None) -> None:
        self.protocolSettings = protocolSettings

        if settings:
            self.device_serial_number = settings.get("serial_number", self.device_serial_number)
            self.device_manufacturer = settings.get("manufacturer", self.device_manufacturer)
            self.device_name = settings.get("name", fallback=self.device_manufacturer+" "+self.device_name)
            self.bridge = settings.get("bridge", self.bridge)


    def connect(self, transports : 'transport_base'):
        pass
    
    def read_registers(start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        pass

    def write_register(self, register : int, value : int, **kwargs):
        pass