import logging
from classes.protocol_settings import Registry_Type, protocol_settings
from pymodbus.client.sync import ModbusSerialClient
from .modbus_base import modbus_base
from configparser import SectionProxy
from defs.common import find_usb_serial_port, get_usb_serial_port_info

class modbus_rtu(modbus_base):
    port : str = "/dev/ttyUSB0"
    addresses : list[int] = []
    baudrate : int = 9600
    client : ModbusSerialClient 

    def __init__(self, settings : SectionProxy, protocolSettings : protocol_settings = None):
        #logger = logging.getLogger(__name__)
        #logging.basicConfig(level=logging.DEBUG)

        #todo: implement send holding/input option? here?

        self.port = settings.get("port", "")
        if not self.port:
            raise ValueError("Port is not set")
        
        self.port = find_usb_serial_port(self.port) 
        print("Serial Port : " + self.port + " = "+get_usb_serial_port_info(self.port)) #print for config convience

        self.baudrate = settings.getint("baudrate", 9600)

        address : int = settings.getint("address", 0)
        self.addresses = [address]

        self.client = ModbusSerialClient(method='rtu', port=self.port, 
                                     baudrate=int(self.baudrate), 
                                     stopbits=1, parity='N', bytesize=8, timeout=2
                                     )
        super().__init__(settings, protocolSettings=protocolSettings)
        
    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):

        if 'unit' not in kwargs:
            kwargs = {'unit': int(self.addresses[0]), **kwargs}

        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(start, count, **kwargs)
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(start, count, **kwargs)
        
    def write_register(self, register : int, value : int, **kwargs):
        if not self.write_enabled:
            return 
        
        if 'unit' not in kwargs:
            kwargs = {'unit': self.addresses[0], **kwargs}

        self.client.write_register(register, value, **kwargs) #function code 0x06 writes to holding register

    def connect(self):
        self.connected = self.client.connect()
        super().connect()