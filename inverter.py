#!/usr/bin/env python3
"""
Python Module to implement ModBus RTU connection to ModBus Based Inverters
"""
import logging
import re
import time
import importlib

from pymodbus.exceptions import ModbusIOException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from readers.reader_base import reader_base
from protocol_settings import Data_Type, registry_map_entry, protocol_settings, Registry_Type

class Inverter:
    """ Class Inverter implements ModBus RTU protocol for modbus based inverters """
    protocolSettings : protocol_settings
    max_precision : int
    modbus_delay : float = 0.85
    modbus_version = ""
    reader : reader_base
    settings : dict[str, str]
    
    '''time inbetween requests'''

    def __init__(self, name, unit, protocol_version, settings : dict[str,str], max_precision : int = -1, log = None):
        self.name = name
        self.unit = unit
        self.protocol_version = protocol_version
        self.max_precision = max_precision
        self.settings = settings

        print("max_precision: " + str(self.max_precision))
        if (log is None):
            self.__log = log
        else:
            self.__log = logging.getLogger('invertermodbustomqqt_log')
            self.__log.setLevel(logging.DEBUG)

        #load protocol settings
        self.protocolSettings = protocol_settings(self.protocol_version)
        
        #override reader if set
        if settings["reader"]:
            self.protocolSettings.reader = settings["reader"]
        #load reader
        # Import the module
        module = importlib.import_module('readers.'+self.protocolSettings.reader)


            
        
        # Get the class from the module
        cls = getattr(module, self.protocolSettings.reader)

        self.reader : reader_base = cls(self.settings)
        self.reader.connect()

        self.read_info()

    def read_serial_number(self) -> str:
        

        serial_number = str(self.read_variable("Serial Number", Registry_Type.HOLDING))
        print("read SN: " +serial_number)
        if serial_number:
            return serial_number
        
        sn2 = ""
        sn3 = ""
        fields = ['Serial No 1', 'Serial No 2', 'Serial No 3', 'Serial No 4', 'Serial No 5']
        for field in fields:
            self.__log.info("Reading " + field)
            registry_entry = self.protocolSettings.get_holding_registry_entry(field)
            if registry_entry is not None:
                self.__log.info("Reading " + field + "("+str(registry_entry.register)+")")
                data = self.reader.read_registers(registry_entry.register, registry_type=Registry_Type.HOLDING)
                if not hasattr(data, 'registers') or data.registers is None:
                    self.__log.critical("Failed to get serial number register ("+field+") ; exiting")
                    exit()
                    
                serial_number = serial_number  + str(data.registers[0])

                data_bytes = data.registers[0].to_bytes((data.registers[0].bit_length() + 7) // 8, byteorder='big')
                sn2 = sn2 + str(data_bytes.decode('utf-8')) 
                sn3 = str(data_bytes.decode('utf-8')) + sn3

            time.sleep(self.modbus_delay) #sleep inbetween requests so modbus can rest
        
        print(sn2)
        print(sn3)
        
        if not re.search("[^a-zA-Z0-9\_]", sn2) :
            serial_number = sn2

        return serial_number

    def read_info(self):
        """ reads holding registers from ModBus register inverters -- needs to be updated to support protocol csv """
        return None
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

    def write_variable(self, entry : registry_map_entry, value : str, registry_type : Registry_Type = Registry_Type.HOLDING):
        """ writes a value to a ModBus register; todo: registry_type to handle other write functions"""

        #read current value
        current_registers = self.read_registers(start=entry.register, end=entry.register, registry_type=registry_type)
        results = self.process_registery(current_registers, self.protocolSettings.get_registry_map(registry_type))
        current_value = current_registers[entry.register]

      
        if not self.protocolSettings.validate_registry_entry(entry, current_value):
            raise ValueError("Invalid value in register. unsafe to write")
        
        if not self.protocolSettings.validate_registry_entry(entry, value):
            raise ValueError("Invalid new value. unsafe to write")
        
        #handle codes
        if entry.variable_name+"_codes" in self.protocolSettings.codes:
            codes = self.protocolSettings.codes[entry.variable_name+"_codes"]
            for key, val in codes.items():
                if val == value: #convert "string" to key value
                    value = key
                    break

        #results[entry.variable_name]
        ushortValue : int = None #ushort
        if entry.data_type == Data_Type.USHORT:
            ushortValue = int(value)
            if ushortValue < 0 or ushortValue > 65535:
                 raise ValueError("Invalid value")
        elif entry.data_type.value > 200 or entry.data_type == Data_Type.BYTE: #bit types
            bit_size = Data_Type.getSize(entry.data_type)

            new_val = int(value)
            if 0 > new_val or new_val > 2**bit_size:
                raise ValueError("Invalid value")

            bit_index = entry.register_bit
            bit_mask = ((1 << bit_size) - 1) << bit_index  # Create a mask for extracting X bits starting from bit_index
            clear_mask = ~(bit_mask)  # Mask for clearing the bits to be updated

            # Clear the bits to be updated in the current_value
            ushortValue = current_value & clear_mask

            # Set the bits according to the new_value at the specified bit position
            ushortValue |= (new_val << bit_index) & bit_mask

            bit_mask = (1 << bit_size) - 1  # Create a mask for extracting X bits
            check_value = (ushortValue >> bit_index) & bit_mask

            if check_value != new_val:
                raise ValueError("something went wrong bitwise")
        else:
            raise TypeError("Unsupported data type")
            
       

        
        if ushortValue == None:
            raise ValueError("Invalid value - None")

        self.reader.write_register(entry.register, ushortValue, registry_type=registry_type)


    def read_variable(self, variable_name : str, registry_type : Registry_Type, entry : registry_map_entry = None):
        ##clean for convinecne  
        if variable_name:
            variable_name = variable_name.strip().lower().replace(' ', '_')

        registry_map = self.protocolSettings.get_registry_map(registry_type)

        if entry == None:
            for e in registry_map:
                if e.variable_name == variable_name:
                    entry = e
                    break

        if entry:
            start : int = 0
            end : int = 0
            if not entry.concatenate:
                start = entry.register
                end = entry.register
            else:
                start = entry.register
                end = max(entry.concatenate_registers)
            
            registers = self.read_registers(start=start, end=end, registry_type=registry_type)
            results = self.process_registery(registers, registry_map)
            return results[entry.variable_name]
            

    def read_registers(self, ranges : list[tuple] = None, start : int = 0, end : int = None, batch_size : int = 45, registry_type : Registry_Type = Registry_Type.INPUT ) -> dict:
        

        if not ranges: #ranges is empty, use min max
            end = end + 1
            ranges = []
            start = start - batch_size
            while( start := start + batch_size ) < end:
                count = batch_size
                if start + batch_size > end:
                    count = end - start + 1
                ranges.append((start, count)) ##APPEND TUPLE

        registry : dict[int,] = {}
        retries = 7
        retry = 0
        total_retries = 0

        index = -1
        while (index := index + 1) < len(ranges) :
            range = ranges[index]

            print("get registers("+str(index)+"): " + str(range[0]) + " to " + str(range[0]+range[1]-1) + " ("+str(range[1])+")")
            time.sleep(self.modbus_delay) #sleep for 1ms to give bus a rest #manual recommends 1s between commands

            isError = False
            try:
                register = self.reader.read_registers(range[0], range[1], registry_type=registry_type, unit=self.unit)

            except ModbusIOException as e: 
                print("ModbusIOException : ", e.error_code)
                if e.error_code == 4: #if no response; probably time out. retry with increased delay
                    isError = True
                else:
                    raise

            if register.isError() or isError:
                self.__log.error(register.__str__)
                self.modbus_delay = self.modbus_delay + 0.050 #increase delay, error is likely due to modbus being busy

                if self.modbus_delay > 60: #max delay. 60 seconds between requests should be way over kill if it happens
                    self.modbus_delay = 60

                if retry > retries: #instead of none, attempt to continue to read. but with no retires. 
                    continue
                else:
                    #undo step in loop and retry read
                    retry = retry + 1
                    total_retries = total_retries + 1
                    print("Retry("+str(retry)+" - ("+str(total_retries)+")) range("+str(index)+")")
                    index = index - 1
                    continue
            

            retry -= 1
            if retry < 0:
                retry = 0

            #combine registers into "registry"
            i = -1
            while(i := i + 1 ) < range[1]:
                #print(str(i) + " => " + str(i+range[0]))
                registry[i+range[0]] = register.registers[i]

        return registry

    def process_registery(self, registry : dict, map : list[registry_map_entry]) -> dict[str,str]:
        '''process registry into appropriate datatypes and names'''
        
        concatenate_registry : dict = {}
        info = {}
        for item in map:

            if item.register not in registry:
                continue
            value = ''    

            if item.data_type == Data_Type.UINT: #read uint
                if item.register + 1 not in registry:
                    continue
                value = float((registry[item.register] << 16) + registry[item.register + 1])
            elif item.data_type == Data_Type.SHORT: #read signed short
                val = registry[item.register]
                val &= 0xFFFF  # Mask out the sign bit of the unsigned short

                # Convert the combined unsigned value to a signed integer if necessary
                if val & (1 << 15):  # Check if the sign bit (bit 31) is set
                    # Perform two's complement conversion to get the signed integer
                    value = val - (1 << 16)
                else:
                    value = val
                value = -value
            elif item.data_type == Data_Type.INT: #read int
                if item.register + 1 not in registry:
                    continue
                
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
            elif item.data_type == Data_Type._16BIT_FLAGS or item.data_type == Data_Type._8BIT_FLAGS:
                val = registry[item.register]
                #16 bit flags
                start_bit : int = 0
                if item.data_type == Data_Type._8BIT_FLAGS:
                    start_bit = 8
                
                if item.documented_name+'_codes' in self.protocolSettings.codes:
                    flags : list[str] = []
                    for i in range(start_bit, 16):  # Iterate over each bit position (0 to 15)
                        # Check if the i-th bit is set
                        if (val >> i) & 1:
                            flag_index = "b"+str(i)
                            if flag_index in self.protocolSettings.codes[item.documented_name+'_codes']:
                                flags.append(self.protocolSettings.codes[item.documented_name+'_codes'][flag_index])
                            
                    value = ",".join(flags)
                else:
                    flags : list[str] = []
                    for i in range(start_bit, 16):  # Iterate over each bit position (0 to 15)
                        # Check if the i-th bit is set
                        if (val >> i) & 1:
                            flags.append("1")
                        else:
                            flags.append("0")
                    value = ''.join(flags)
            elif item.data_type.value > 200 or item.data_type == Data_Type.BYTE: #bit types
                    bit_size = Data_Type.getSize(item.data_type)
                    bit_mask = (1 << bit_size) - 1  # Create a mask for extracting X bits
                    bit_index = item.register_bit
                    value = (registry[item.register] >> bit_index) & bit_mask
            elif item.data_type == Data_Type.ASCII:
                value = registry[item.register].to_bytes((16 + 7) // 8, byteorder='big') #convert to ushort to bytes
                try:
                    value = value.decode("utf-8") #convert bytes to ascii
                except UnicodeDecodeError as e:
                    print("UnicodeDecodeError:", e)

            else: #default, Data_Type.USHORT
                value = float(registry[item.register])

            if item.unit_mod != float(1):
                value = value * item.unit_mod

            if  isinstance(value, float) and self.max_precision > -1:
                value = round(value, self.max_precision)

            if (item.data_type != Data_Type._16BIT_FLAGS and
                item.documented_name+'_codes' in self.protocolSettings.codes):
                try:
                    cleanval = str(int(value))
            
                    if cleanval in self.protocolSettings.codes[item.documented_name+'_codes']:
                        value = self.protocolSettings.codes[item.documented_name+'_codes'][cleanval]
                except:
                    #do nothing; try is for intval
                    value = value
            
            #if item.unit:
            #    value = str(value) + item.unit
            if item.concatenate:
                concatenate_registry[item.register] = value

                all_exist = True
                for key in item.concatenate_registers:
                    if key not in concatenate_registry:
                        all_exist = False
                        break
                if all_exist:
                #if all(key in concatenate_registry for key in item.concatenate_registers):
                    concatenated_value = ""
                    for key in item.concatenate_registers:
                        concatenated_value = concatenated_value + str(concatenate_registry[key])
                        del concatenate_registry[key]

                    info[item.variable_name] = concatenated_value
            else:
                info[item.variable_name] = value

        return info
    
    def read_registry(self, registry_type : Registry_Type = Registry_Type.INPUT) -> dict[str,str]:
        map = self.protocolSettings.get_registry_map(registry_type)
        if not map:
            return {}
        
        registry = self.read_registers(self.protocolSettings.get_registry_ranges(registry_type), registry_type=registry_type)
        info = self.process_registery(registry, map)
        return info


    def read_input_registry(self) -> dict[str,str]:
        ''' reads input registers and returns as clean dict object inverters '''
        if not self.protocolSettings.input_registry_map: #empty map. no data to read
            return {}
        
        registry = self.read_registers(self.protocolSettings.input_registry_ranges, registry_type=Registry_Type.INPUT)
        info = self.process_registery(registry, self.protocolSettings.input_registry_map)
        return info
    
    def read_holding_registry(self) -> dict[str,str]:
        ''' reads holding registers and returns as clean dict object inverters '''
        if not self.protocolSettings.holding_registry_map: #empty map. no data to read
            return {}

        registry = self.read_registers(self.protocolSettings.holding_registry_ranges, registry_type=Registry_Type.HOLDING)
        info = self.process_registery(registry, self.protocolSettings.holding_registry_map)
        return info