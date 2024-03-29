from .serial_frame_client import serial_frame_client
from .reader_base import reader_base

class serial_pylon(reader_base):
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

    ''' for a lack of a better name'''
    def __init__(self) -> None:
        '''address is required to be specified '''
        pass

    def connect(self):
        #3.1 Get protocol version
        
        pass
    