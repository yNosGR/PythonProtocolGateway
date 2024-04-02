import serial
import threading
import time


class serial_frame_client():
    ''' basic serial client implenting a empty SOI/EOI frame'''
    client : serial.Serial
    running : bool
    soi : bytes
    '''start of information'''
    eoi : bytes
    '''end of information'''
    pending_frames : list[bytes]

    max_frame_size : int = 256


    def __init__(self) -> None:
        self.client = serial.Serial('/dev/ttyUSB0', 9600)
        pass

    def checksum(self, data : bytes) -> bytes:
        return b''

    def write(self, data : bytes):
        ''' write data, excluding SOI and EOI bytes'''
        data = self.soi + data + self.eoi
        self.client.write()

    def read(self):
        buffer = bytearray()

        while self.running:
            # Read data from serial port
            data = self.client.read()

            # Check if data is available
            if data:
                # Append data to buffer
                buffer += data

                # Find SOI index in buffer
                soi_index = buffer.find(self.soi)

                # Process all occurrences of SOI in buffer
                while soi_index != -1:
                    # Remove data before SOI sequence
                    buffer = buffer[soi_index:]

                    # Find EOI index in buffer
                    eoi_index = buffer.find(self.eoi)

                    if eoi_index != -1:
                        # Extract and store the complete frame
                        self.pending_frames.append(buffer[len(self.soi):eoi_index])

                        # Remove the processed data from the buffer
                        buffer = buffer[eoi_index + len(self.eoi) : ]

                        # Find next SOI index in the remaining buffer
                        soi_index = buffer.find(self.soi)
                    else:
                        # If no EOI is found and buffer size exceeds max_frame_size, clear buffer
                        if len(buffer) > self.max_frame_size:
                            buffer.clear()
                        break #no eoi, continue waiting

            time.sleep(0.01)
        
    
