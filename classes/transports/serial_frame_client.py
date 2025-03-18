from typing import Callable
import serial
import threading
import time


class serial_frame_client():
    ''' basic serial client implenting a empty SOI/EOI frame'''
    client : serial.Serial
    running : bool = False
    soi : bytes
    '''start of information'''
    eoi : bytes
    '''end of information'''
    pending_frames : list[bytes] = []

    max_frame_size : int = 256

    port : str = '/dev/ttyUSB0'
    baud :  int = 9600

    timeout : float = 5
    ''' timeout in seconds '''

    #region asyncronous
    asynchronous : bool = False
    ''' if set, runs main loop'''

    on_message : Callable[[bytes], None] = None
    ''' async mode only'''

    thread : threading.Thread
    ''' main thread for read loop'''

    callback_lock : threading.Lock = threading.Lock()
    '''lock for callback'''
    #endregion asyncronous


    def __init__(self, port : str , baud : int , soi : bytes, eoi : bytes, **kwrgs) -> None:
        self.soi = soi
        self.eoi = eoi
        self.port = port
        self.baud = baud
        self.client = serial.Serial(port, baud, **kwrgs)

    def connect(self):
        if self.asynchronous:
            self.running = True
            self.pending_frames = []
            self.thread = threading.Thread(target=self.read_thread)
            self.thread.daemon = True
            self.thread.start()
        return True

    def write(self, data : bytes):
        ''' write data, excluding SOI and EOI bytes'''
        data = self.soi + data + self.eoi
        self.client.write(data)

    def read(self, reset_buffer = True, frames = 1) -> list[bytes] | bytes:
        ''' returns list of frames, if frames > 1 '''
        buffer = bytearray()
        self.pending_frames.clear()

        #for shatty order sensitive protocols.
        # Clear input buffers
        if reset_buffer:
            self.client.reset_input_buffer()

        timedout = time.time() + self.timeout
        self.client.timeout = self.timeout
        frameCount = 0

        while time.time() < timedout:
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

                        frame = buffer[len(self.soi):eoi_index]
                        if frames == 1:
                            return frame

                        if frameCount > 1:
                            # Extract and store the complete frame
                            self.pending_frames.append(frame)

                            if self.pending_frames.count() == frames:
                                return self.pending_frames

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

    def read_thread(self):
        buffer = bytearray()
        self.running = True
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

                #can probably be in the loop, but being cautious
                for frame in self.pending_frames:
                    with self.callback_lock:
                        if self.on_message:
                            self.on_message(frame)

            time.sleep(0.01)


