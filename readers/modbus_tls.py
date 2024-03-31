import logging
from protocol_settings import Registry_Type
from pymodbus.client.sync import ModbusTlsClient
from .reader_base import reader_base

class modbus_udp(reader_base):
    port : int = 502
    host : str = ""

    hostname : str = ""
    ''' optional for cert '''
    
    certfile : str = ""
    keyfile : str = ""
    client : ModbusTlsClient 

    def __init__(self, settings : dict[str,str]):
        #logger = logging.getLogger(__name__)
        #logging.basicConfig(level=logging.DEBUG)

        if "port" in settings:
            self.port = settings["port"]

        if "host" in settings:
            self.host = settings["host"]

        if not self.host:
            raise ValueError("Host is not set")
        
        if "certfile" in settings:
            self.certfile = settings["certfile"]

        if not self.certfile:
            raise ValueError("certfile is not set")

        if "keyfile" in settings:
            self.keyfile = settings["keyfile"]

        if not self.keyfile:
            raise ValueError("keyfile is not set")
        
        if "hostname" in settings:
            self.hostname = settings["hostname"]

        if not self.hostname:
            self.hostname = self.host

        self.client = ModbusTlsClient(host=self.host, 
                                      hostname = self.hostname,
                                      certfile = self.certfile,
                                      keyfile  = self.keyfile,
                                      port=self.port, 
                                      timeout=7, 
                                      retries=3)
        
    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(start, count, **kwargs)
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(start, count, **kwargs)

    def connect(self):
        self.client.connect()
