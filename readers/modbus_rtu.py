import logging
from protocol_settings import Registry_Type
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from .reader_base import reader_base

class modbus_rtu(reader_base):
    port : str = "/dev/ttyUSB0"
    baudrate : int = 9600
    client : ModbusClient 

    def __init__(self, settings : dict[str,str]):
        #logger = logging.getLogger(__name__)
        #logging.basicConfig(level=logging.DEBUG)

        if "port" in settings:
            self.port = settings["port"]

        if "buadrate" in settings:
            self.baudrate = settings["buadrate"]

        self.client = ModbusClient(method='rtu', port=self.port, 
                                     baudrate=int(self.baudrate), 
                                     stopbits=1, parity='N', bytesize=8, timeout=2
                                     )
        
    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(start, count, **kwargs)
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(start, count, **kwargs)

    def connect(self):
        self.client.connect()
