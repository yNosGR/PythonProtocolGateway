
import logging
from classes.protocol_settings import Registry_Type,protocol_settings,registry_map_entry

from typing import Callable
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .transport_base import transport_base
    from configparser import SectionProxy

class transport_base:
    type : str = ''
    protocolSettings : 'protocol_settings'
    protocol_version : str = ''
    transport_name : str = ''
    device_name : str = ''
    device_serial_number : str = 'hotnoob'
    device_manufacturer : str = 'hotnoob'
    device_model : str = 'hotnoob'
    bridge : str = ''
    write_enabled : bool = False

    read_interval : float = 0
    last_read_time : float = 0

    connected : bool = False

    on_message : Callable[['transport_base', registry_map_entry, str], None] = None
    ''' callback, on message recieved '''

    _log : logging.Logger = None

    def __init__(self, settings : 'SectionProxy', protocolSettings : 'protocol_settings' = None) -> None:
        
        self._log : logging.Logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        self.transport_name = settings.name #section name
        
        self.type = self.__class__.__name__        

        self.protocolSettings = protocolSettings
        if not self.protocolSettings: #if not, attempt to load. lazy i know
            self.protocol_version = settings.get('protocol_version')
            if self.protocol_version:
                self.protocolSettings = protocol_settings(self.protocol_version)

        if self.protocolSettings:
            self.protocol_version = self.protocolSettings.protocol

        if settings:
            self.device_serial_number = settings.get("serial_number", self.device_serial_number)
            self.device_manufacturer = settings.get("manufacturer", self.device_manufacturer)
            self.device_name = settings.get("name", fallback=self.device_manufacturer+" "+self.device_name)
            self.bridge = settings.get("bridge", self.bridge)
            self.read_interval = settings.getfloat("read_interval", self.read_interval)

    def init_bridge(self, from_transport : 'transport_base'):
        pass

    @classmethod
    def _get_top_class_name(cls, cls_obj):
        if not cls_obj.__bases__:
            return cls_obj.__name__
        else:
            return cls._get_top_class_name(cls_obj.__bases__[0])

    def connect(self, transports : 'transport_base'):
        pass
    
    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        pass

    def write_data(self, data : dict[str,str]):
        pass

    def write_register(self, register : int, value : int, **kwargs):
        pass