from .serial_frame_client import serial_frame_client
from .transport_base import transport_base


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from configparser import SectionProxy
    from classes.protocol_settings import protocol_settings

class serial_pylon(transport_base):
    ''' for a lack of a better name'''

    port : str = "/dev/ttyUSB0"
    addresses : list[int] = []
    baudrate : int = 9600

    client : serial_frame_client

    #this format is pretty common; i need a name for it.
    SOI : bytes = b'\x7e'
    VER : bytes = b'\x00'
    ''' version has to be fetched first '''
    ADR : bytes
    CID1 : bytes
    CID2 : bytes
    LENGTH : bytes
    INFO : bytes
    CHKSUM : bytes
    EOI : bytes = b'\x0d'

    def __init__(self, settings : 'SectionProxy', protocolSettings : 'protocol_settings' = None):
        super().__init__(settings, protocolSettings=protocolSettings)
        '''address is required to be specified '''
        self.port = settings.get("port", "")
        if not self.port:
            raise ValueError("Port is not set")

        self.baudrate = settings.getint("buadrate", 9600)

        address : int = settings.getint("address", 0)
        self.addresses = [address]
        pass

    def connect(self):
        #3.1 Get protocol version
        if self.VER == b'\x00':
            #get VER for communicating
            #SOI VER ADR 46H 4FH LENGT INFO CHKSUM EOI
        
    