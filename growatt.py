#!/usr/bin/env python3
"""
Python Module to implement ModBus RTU connection to Growatt Inverters
"""
import logging
import time
import struct
from pymodbus.exceptions import ModbusIOException

from protocol_settings import Data_Type, registry_map_entry, protocol_settings

class Growatt:
    """ Class Growatt implements ModBus RTU protocol for growatt inverters """
    protocolSettings : protocol_settings
    max_precision : int

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
            self.__log = logging.getLogger('growatt2mqqt_log')
            self.__log.setLevel(logging.DEBUG)

        #load protocol settings
        self.protocolSettings = protocol_settings(self.protocol_version)

        self.read_info()

    def read_serial_number(self) -> str:
        serial_number = ""
        fields = ['Serial No. 1', 'Serial No. 2', 'Serial No. 3', 'Serial No. 4', 'Serial No. 5']
        for field in fields:
            registry_entry = self.protocolSettings.get_holding_registry_entry(field)
            if registry_entry is not None:
                data = self.client.read_holding_registers(registry_entry.register)
                serial_number = serial_number  + str(data.registers[0])

        return serial_number

    def read_info(self):
        """ reads holding registers from Growatt inverters """
        row = self.client.read_holding_registers(73, unit=self.unit)
        if row.isError():
            raise ModbusIOException

        self.modbus_version = row.registers[0]

    def print_info(self):
        """ prints basic information about the current Growatt inverter """
        self.__log.info('Growatt:')
        self.__log.info('\tName: %s\n', str(self.name))
        self.__log.info('\tUnit: %s\n', str(self.unit))
        self.__log.info('\tModbus Version: %s\n', str(self.modbus_version))

    def read_input_register(self) -> dict[str,str]:
        """ this function reads based on the given ModBus RTU protocol version the ModBus data from growatt inverters"""
        #read input register
        batch_size = 45 #see manual; says max batch is 45
        start = -batch_size
        registry = []
        
        while (start := start+batch_size) <= self.protocolSettings.input_registry_size :
            print("get registers: " + str(start) )
            time.sleep(0.001) #sleep for 1ms to give bus a rest
            register = self.client.read_input_registers(start, batch_size, unit=self.unit)
            if register.isError():
                self.__log.error(register.__str__)
                return None
            
            #combine registers into "registry"
            registry.extend(register.registers)                

            #dump registers
            #for i in range(0,batch_size):
            #    print("Register {}: {}".format(start+i, float(register.registers[i])/10))

        info = {}
        info['StatusCode'] = registry[0]
        
        for item in self.protocolSettings.input_registry_map:
            value = ''

        
            

            if item.data_type == Data_Type.UINT: #read uint
                value = float((registry[item.register] << 16) + registry[item.register + 1])
            elif item.data_type == Data_Type.INT: #read int
                value = int.from_bytes(bytes([registry[item.register], registry[item.register + 1]]), byteorder='little', signed=True)
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
