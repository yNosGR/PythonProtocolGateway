#!/usr/bin/env python3
"""
Python Module to implement ModBus RTU connection to ModBus Based Inverters
"""
import logging
import time
import struct
from pymodbus.exceptions import ModbusIOException

from protocol_settings import Data_Type, registry_map_entry, protocol_settings

class Inverter:
    """ Class Inverter implements ModBus RTU protocol for modbus based inverters """
    protocolSettings : protocol_settings
    max_precision : int
    modbus_delay : float = 0.85
    
    '''time inbetween requests'''

    def __init__(self, client, name, unit, protocol_version, max_precision : int = -1, log = None):
        self.client = client
        self.name = name
        self.unit = unit
        self.protocol_version = protocol_version
        self.max_precision = max_precision
        print("max_precision: " + str(self.max_precision))
        if (log is None):
            self.__log = log
        else:
            self.__log = logging.getLogger('invertermodbustomqqt_log')
            self.__log.setLevel(logging.DEBUG)

        #load protocol settings
        self.protocolSettings = protocol_settings(self.protocol_version)

        self.read_info()

    def read_serial_number(self) -> str:
        serial_number = ""
        fields = ['Serial No. 1', 'Serial No. 2', 'Serial No. 3', 'Serial No. 4', 'Serial No. 5']
        for field in fields:
            self.__log.info("Reading " + field)
            registry_entry = self.protocolSettings.get_holding_registry_entry(field)
            if registry_entry is not None:
                data = self.client.read_holding_registers(registry_entry.register)
                if not hasattr(data, 'registers') or data.registers is None:
                    self.__log.critical("Failed to get serial number register ("+field+") ; exiting")
                    exit()
                    
                serial_number = serial_number  + str(data.registers[0])

            time.sleep(self.modbus_delay) #sleep inbetween requests so modbus can rest

        return serial_number

    def read_info(self):
        """ reads holding registers from ModBus register inverters -- needs to be updated to support protocol csv """
        row = self.client.read_holding_registers(73, unit=self.unit)
        if row.isError():
            raise ModbusIOException

        self.modbus_version = row.registers[0]

    def print_info(self):
        """ prints basic information about the current ModBus inverter """
        self.__log.info('Inverter:')
        self.__log.info('\tName: %s\n', str(self.name))
        self.__log.info('\tUnit: %s\n', str(self.unit))
        self.__log.info('\tModbus Version: %s\n', str(self.modbus_version))

    def read_registers(self, ranges : list[tuple] = None, min : int = 0, max : int = None, batch_size : int = 45) -> dict:
        

        if not ranges: #ranges is empty, use min max
            ranges = []
            min = -batch_size
            while( min := min + batch_size ) < max:
                ranges.append((min, min + batch_size)) ##APPEND TUPLE

        registry : dict = {}
        retries = 7
        retry = 0
    
        index = -1
        while (index := index + 1) < len(range) :
            range = ranges[index]

            print("get registers("+str(index)+"): " + str(range[0]) + " to " + str(range[1]+1) )
            time.sleep(self.modbus_delay) #sleep for 1ms to give bus a rest #manual recommends 1s between commands

            isError = False
            try:
                register = self.client.read_input_registers(range[0], range[1]+1, unit=self.unit)
            except ModbusIOException as e: 
                if e.error_code == 4: #if no response; probably time out. retry with increased delay
                    isError = True
                else:
                    raise

            if register.isError() or isError:
                self.__log.error(register.__str__)
                self.modbus_delay = self.modbus_delay + 0.050 #increase delay, error is likely due to modbus being busy

                if self.modbus_delay > 60: #max delay. 60 seconds between requests should be way over kill if it happens
                    self.modbus_delay = 60

                if retry > retries:
                    return None
                else:
                    #undo step in loop and retry read
                    retry = retry + 1
                    index = index - -1
                    continue
            
            #combine registers into "registry"
            i = -1
            while(i := i + 1 ) < range[1]+1:
                registry[i+range[0]] = register.registers[i]

        return registry


    def read_input_register(self) -> dict[str,str]:
        """ this function reads based on the given ModBus RTU protocol version the ModBus data from ModBus inverters"""
        #read input register
        #batch_size = 45 #see manual; says max batch is 45

        registry = self.read_registers(self.protocolSettings.input_registry_ranges)

        info = {}
        info['StatusCode'] = registry[0]
        
        for item in self.protocolSettings.input_registry_map:
            value = ''

        
            

            if item.data_type == Data_Type.UINT: #read uint
                value = float((registry[item.register] << 16) + registry[item.register + 1])
            elif item.data_type == Data_Type.INT: #read int

                combined_value_unsigned = (registry[item.register] << 16) + registry[item.register + 1]

                # Convert the combined unsigned value to a signed integer if necessary
                if combined_value_unsigned & (1 << 31):  # Check if the sign bit (bit 31) is set
                    # Perform two's complement conversion to get the signed integer
                    value = combined_value_unsigned - (1 << 32)
                else:
                    value = combined_value_unsigned
                value = -value
                #value = struct.unpack('<h', bytes([min(max(registry[item.register], 0), 255), min(max(registry[item.register+1], 0), 255)]))[0]
                #value = int.from_bytes(bytes([registry[item.register], registry[item.register + 1]]), byteorder='little', signed=True)
            else: #default, Data_Type.BYTE
                value = float(registry[item.register])

            if item.unit_mod != float(1):
                value = value * item.unit_mod

            if  isinstance(value, float) and self.max_precision > -1:
                value = round(value, self.max_precision)

            if item.documented_name+'_codes' in self.protocolSettings.codes:
                try:
                    cleanval = str(int(value))
            
                    if cleanval in self.protocolSettings.codes[item.documented_name+'_codes']:
                        value = self.protocolSettings.codes[item.documented_name+'_codes'][cleanval]
                except:
                    #do nothing; try is for intval
                    value = value
            
            #if item.unit:
            #    value = str(value) + item.unit

            info[item.variable_name] = value

        return info


    # def read_fault_table(self, name, base_index, count):
    #     fault_table = {}
    #     for i in range(0, count):
    #         fault_table[name + '_' + str(i)] = self.read_fault_record(base_index + i * 5)
    #     return fault_table
    #
    # def read_fault_record(self, index):
    #     row = self.client.read_input_registers(index, 5, unit=self.unit)
    #     # TODO: Figure out how to read the date for these records?
    #     print(row.registers[0],
    #             ErrorCodes[row.registers[0]],
    #             '\n',
    #             row.registers[1],
    #             row.registers[2],
    #             row.registers[3],
    #             '\n',
    #             2000 + (row.registers[1] >> 8),
    #             row.registers[1] & 0xFF,
    #             row.registers[2] >> 8,
    #             row.registers[2] & 0xFF,
    #             row.registers[3] >> 8,
    #             row.registers[3] & 0xFF,
    #             row.registers[4],
    #             '\n',
    #             2000 + (row.registers[1] >> 4),
    #             row.registers[1] & 0xF,
    #             row.registers[2] >> 4,
    #             row.registers[2] & 0xF,
    #             row.registers[3] >> 4,
    #             row.registers[3] & 0xF,
    #             row.registers[4]
    #           )
    #     return {
    #         'FaultCode': row.registers[0],
    #         'Fault': ErrorCodes[row.registers[0]],
    #         #'Time': int(datetime.datetime(
    #         #    2000 + (row.registers[1] >> 8),
    #         #    row.registers[1] & 0xFF,
    #         #    row.registers[2] >> 8,
    #         #    row.registers[2] & 0xFF,
    #         #    row.registers[3] >> 8,
    #         #    row.registers[3] & 0xFF
    #         #).timestamp()),
    #         'Value': row.registers[4]
    #     }
