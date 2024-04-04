from enum import Enum
import struct

import serial

from ..Object import Object

from .serial_frame_client import serial_frame_client
from .transport_base import transport_base



from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from configparser import SectionProxy
    from classes.protocol_settings import protocol_settings, registry_map_entry


class return_codes(Enum):
    NORMAL                  = 0x00
    VERSION_ERROR           = 0x01
    CHECKSUM_ERROR          = 0x02
    LCHECKSUM_ERROR         = 0x03
    INVALID_CID2            = 0x04
    COMMAND_FORMAT_ERROR    = 0X05
    INVALID_DATA            = 0X06
    ADDRESS_ERROR           = 0X90
    COMMUNICATION_ERROR     = 0X91
    UNKNOWN_ERROR           = -1

    @classmethod
    def fromByte(cls, value : bytes):
        try:
            return cls(int(value, 16))  # Attempt to access the Enum member
        except ValueError:
            return return_codes.UNKNOWN_ERROR

class serial_pylon(transport_base):
    ''' for a lack of a better name'''

    port : str = "/dev/ttyUSB0"
    addresses : list[int] = []
    baudrate : int = 9600

    client : serial_frame_client

    #this format is pretty common; i need a name for it.
    SOI : bytes = b'\x7e' # aka b"~"
    VER : bytes = b'\x00' 
    ''' version has to be fetched first '''
    ADR : bytes
    CID1 : bytes
    CID2 : bytes
    LENGTH : bytes
    ''' 2 bytes - include LENID & LCHKSUM'''
    INFO : bytes
    CHKSUM : bytes
    EOI : bytes = b'\x0d' # aka b"\r"

    def __init__(self, settings : 'SectionProxy', protocolSettings : 'protocol_settings' = None):
        super().__init__(settings, protocolSettings=protocolSettings)
        '''address is required to be specified '''
        self.port = settings.get("port", "")
        if not self.port:
            raise ValueError("Port is not set")

        self.baudrate = settings.getint("baudrate", 9600)

        address : int = settings.getint("address", 0)
        self.addresses = [address]

        self.ADR = struct.pack('B', address)
        #todo, multi address support later

        self.client = serial_frame_client(self.port, 
                                          self.baudrate, 
                                          self.SOI, 
                                          self.EOI, 
                                          bytesize=8, parity=serial.PARITY_NONE, stopbits=1, exclusive=True)


        pass

    def connect(self):
        self.client.connect()
        #3.1 Get protocol version
        if self.VER == b'\x00':
            #get VER for communicating
            #SOI VER ADR 46H 4FH LENGT INFO CHKSUM EOI
            version = self.read_variable('version')
            if version:
                self.VER = version
            pass

    def read_variable(self, variable_name : str, entry : 'registry_map_entry' = None):
        ##clean for convinecne  
        if variable_name:
            variable_name = variable_name.strip().lower().replace(' ', '_')

        registry_map = self.protocolSettings.get_registry_map()

        if entry == None:
            for e in registry_map:
                if e.variable_name == variable_name:
                    entry = e
                    break
        

        if entry:
            #entry.concatenate this protocol probably doesnt require concatenate, since info is variable length.
            command = entry.register #CID1 and CID2 combined creates a single ushort
            self.send_command(command)  
            frame = self.client.read()
            if frame:
                return self.decode_frame(frame)

        return None

    def calculate_checksum(self, data):
        # Calculate the sum of all characters in ASCII value
        ascii_sum = sum(data)

        # Take modulus 65536
        remainder = ascii_sum % 65536

        # Bitwise invert the remainder and add 1
        checksum = ~remainder & 0xFFFF
        checksum += 1

        return checksum

    def decode_frame(self, raw_frame: bytes) -> bytes:
        b4 = raw_frame
        raw_frame = bytes(raw_frame)

        frame_data = raw_frame[0:len(raw_frame) - 5]
        frame_chksum = raw_frame[-5:-1]

        calc_checksum = self.calculate_checksum(frame_data)
        if calc_checksum != int(frame_chksum, 16):
            self._log.warning(f"Serial Pylon checksum error, got {calc_checksum}, expected {frame_chksum}")

        data = Object()
        data.ver = frame_data[0:2]
        data.adr = frame_data[2:4]
        data.cid1 = frame_data[4:6]
        data.cid2 = frame_data[6:8]
        data.infolength = frame_data[8:12]
        data.info = frame_data[12:]

        #on return, cid2 holds a return error code. so reads are time sensitive. will have to write syncronis functions in client
        #fromByte
        returnCode = return_codes.fromByte(data.cid2)
        if returnCode != return_codes.NORMAL:
            self._log.warning(f"Serial Pylon Error code {returnCode}")

        #todo, process info
        return data.info

    
    def build_frame(self, command : int, info: bytes = b''):
        ''' builds frame without soi and eoi; that is left for frame client'''

        info_length = 0

        lenid = len(info)
        if lenid != 0:
            lenid_sum = (lenid & 0xf) + ((lenid >> 4) & 0xf) + ((lenid >> 8) & 0xf)
            lenid_modulo = lenid_sum % 16
            lenid_invert_plus_one = 0b1111 - lenid_modulo + 1

            info_length = (lenid_invert_plus_one << 12) + lenid

        self.LENGTH = struct.pack('<H', info_length)

        frame : bytes = self.VER + self.ADR +struct.pack('<H', command) + self.LENGTH + info

        #protocol is in ASCII hex. :facepalm:
        frame = ''.join(['{:02X}'.format(byte) for byte in frame])

        frame_chksum = self.calculate_checksum(frame)
        frame = frame + '{:04X}'.format(struct.pack('<H', frame_chksum))

       

        return frame
        
        
    def send_command(self, cmd, info: bytes = b''):
        data = self.build_frame(cmd, info)
        self.client.write(data)

        