import logging
from classes.protocol_settings import Registry_Type, protocol_settings
from pymodbus.client.sync import ModbusSerialClient
from .transport_base import transport_base
from configparser import SectionProxy

class modbus_rtu(transport_base):
    port : str = "/dev/ttyUSB0"
    baudrate : int = 9600
    client : ModbusSerialClient 

    def __init__(self, settings : SectionProxy, protocolSettings : protocol_settings = None):
        #logger = logging.getLogger(__name__)
        #logging.basicConfig(level=logging.DEBUG)

        self.port = settings.get("port", "")
        if not self.port:
            raise ValueError("Port is not set")
        
        self.baudrate = settings.getint("buadrate", 9600)


        self.client = ModbusSerialClient(method='rtu', port=self.port, 
                                     baudrate=int(self.baudrate), 
                                     stopbits=1, parity='N', bytesize=8, timeout=2
                                     )
        super().__init__(protocolSettings=protocolSettings)
        
    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(start, count, **kwargs)
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(start, count, **kwargs)
        
    def write_register(self, register : int, value : int, **kwargs):
        self.client.write_register(register, value, **kwargs) #function code 0x06 writes to holding register

    def connect(self):
        self.client.connect()
