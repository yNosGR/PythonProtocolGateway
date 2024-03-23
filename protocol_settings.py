import csv
from dataclasses import dataclass
from enum import Enum
import json
import re
import os


class Data_Type(Enum):
    BYTE = 1
    '''8bit byte'''
    USHORT = 2
    '''16 bit unsigned int'''
    UINT = 3
    '''32 bit unsigned int'''
    SHORT = 4
    '''16 bit signed int'''
    INT = 5
    '''32 bit signed int'''
    _16BIT_FLAGS = 7
    _8BIT_FLAGS = 8

    ASCII = 84
    ''' 2 characters '''

    _1BIT = 201
    _2BIT = 202
    _3BIT = 203
    _4BIT = 204
    _5BIT = 205
    _6BIT = 206
    _7BIT = 207
    _8BIT = 208
    _9BIT = 209
    _10BIT = 210
    _11BIT = 211
    _12BIT = 212
    _13BIT = 213
    _14BIT = 214
    _15BIT = 215
    _16BIT = 216
    @classmethod
    def fromString(cls, name : str):
        name = name.strip().upper()
        if name[0].isdigit():
            name = "_"+name

        #common alternative names
        alias : dict[str,str] = {
            "UINT8" : "BYTE",
            "INT16" : "SHORT",
            "UINT16" : "USHORT"
        }
        
        if name in alias:
            name = alias[name]

        return getattr(cls, name)
    
    @classmethod
    def getSize(cls, data_type : 'Data_Type'):
        sizes = {
                    Data_Type.BYTE : 8,
                    Data_Type.USHORT : 16,
                    Data_Type.UINT : 32,
                    Data_Type.SHORT : 16,
                    Data_Type.INT : 32,
                    Data_Type._16BIT_FLAGS : 16
                 }
        
        if data_type in sizes:
            return sizes[data_type]

        if data_type.value > 200: 
            return data_type.value-200

        return -1 #should never happen

class Registry_Type(Enum):
    HOLDING = 0x03
    INPUT = 0x04
    
@dataclass
class registry_map_entry:
    registry_type : Registry_Type
    register : int
    register_bit : int
    variable_name : str
    documented_name : str
    unit : str
    unit_mod : float
    concatenate : bool
    concatenate_registers : list[int] 

    value_regex : str = ""

    value_min : int = 0
    ''' min of value range for protocol analyzing'''
    value_max : int = 65535
    ''' max of value range for protocol analyzing'''

    ''' if value needs to be concatenated with other registers'''
    data_type : Data_Type = Data_Type.USHORT


class protocol_settings:
    protocol : str
    reader : str
    settings_dir : str
    variable_mask : list[str]
    input_registry_map : list[registry_map_entry]
    input_registry_size : int = 0
    input_registry_ranges : list[tuple]
    holding_registry_map : list[registry_map_entry]
    holding_registry_size : int = 0
    holding_registry_ranges : list[tuple]

    codes : dict[str, str]

    def __init__(self, protocol : str, settings_dir : str = 'protocols'):
        self.protocol = protocol
        self.settings_dir = settings_dir

        self.variable_mask = []
        if os.path.isfile('variable_mask.txt'):
            with open('variable_mask.txt') as f:
                for line in f:
                    if line[0] == '#': #skip comment
                        continue

                    self.variable_mask.append(line.strip().lower())

        self.load__codes() #load first, so priority to json codes
        if "reader" in self.codes:
            self.reader = self.codes["reader"]
        else:
            self.reader = "modbus_rtu"

        self.load__input_registry_map()
        self.load__holding_registry_map()


    def get_holding_registry_entry(self, name : str):
        return self.get_registry_entry(name, self.holding_registry_map)
    
    def get_input_registry_entry(self, name : str):
        return self.get_registry_entry(name, self.input_registry_map)

    def get_registry_entry(self, name : str, map : list[registry_map_entry]) -> registry_map_entry:
        name = name.strip().lower().replace(' ', '_') #clean name
        for item in map:
            if item.documented_name == name:
                return item
        
        return None

    def load__codes(self, file : str = '', settings_dir : str = ''):
        if not settings_dir:
            settings_dir = self.settings_dir

        if not file:
            file = self.protocol + '.json'

        path = settings_dir + '/' + file

        with open(path) as f:
            self.codes = json.loads(f.read())

    def load__registry(self, path, registry_type : Registry_Type = Registry_Type.INPUT) -> list[registry_map_entry]: 
        registry_map : list[registry_map_entry] = []
        register_regex = re.compile(r'(?P<register>\d+)\.b(?P<bit>\d{1,2})')

        range_regex = re.compile(r'(?P<reverse>r|)(?P<start>\d+)[\-~](?P<end>\d+)')
        ascii_value_regex = re.compile(r'(?P<regex>^\[.+\]$)')


        if not os.path.exists(path): #return empty is file doesnt exist.
            return registry_map
        
        with open(path, newline='', encoding='latin-1') as csvfile:
            # Create a CSV reader object
            reader = csv.DictReader(csvfile, delimiter=';') #compensate for openoffice
            
            # Iterate over each row in the CSV file
            for row in reader:

                # Initialize variables to hold numeric and character parts
                numeric_part = 1
                character_part = ''

                #if or is in the unit; ignore unit
                if "or" in row['unit'].lower() or ":" in row['unit'].lower():
                    numeric_part = 1
                    character_part = row['unit']
                else:
                    # Use regular expressions to extract numeric and character parts
                    matches = re.findall(r'([0-9.]+)|(.*?)$', row['unit'])

                    # Iterate over the matches and assign them to appropriate variables
                    for match in matches:
                        if match[0]:  # If it matches a numeric part
                            numeric_part = float(match[0])
                        elif match[1]:  # If it matches a character part
                            character_part = match[1].strip()
                            #print(str(row['documented name']) + " Unit: " + str(character_part) )

                #clean up doc name, for extra parsing
                row['documented name'] = row['documented name'].strip().lower().replace(' ', '_')

                variable_name = row['variable name'] if row['variable name'] else row['documented name']
                variable_name = variable_name = variable_name.strip().lower().replace(' ', '_').replace('__', '_') #clean name
                
                if re.search("[^a-zA-Z0-9\_]", variable_name) :
                    print("WARNING Invalid Name : " + str(variable_name) + " reg: " + str(row['register']) + " doc name: " + str(row['documented name']) + " path: " + str(path))

                #convert to float
                try:
                    numeric_part = float(numeric_part)
                except:
                    numeric_part = float(1)

                if numeric_part == 0:
                    numeric_part = float(1)

                data_type = Data_Type.USHORT

               
                if 'values' not in row:
                    row['values'] = ""
                    print("WARNING No Value Column : path: " + str(path)) 

                #optional row, only needed for non-default data types
                if 'data type' in row and row['data type']:
                    data_type = Data_Type.fromString(row['data type'])


                #get value range for protocol analyzer
                value_min : int = 0
                value_max : int = 65535 #default - max value for ushort
                value_regex : str = ""
                value_is_json : bool = False

                #test if value is json.
                try:
                    codes_json = json.loads(row['values'])
                    value_is_json = True

                    name = row['documented name']+'_codes'
                    if name not in self.codes:
                        self.codes[name] = codes_json

                except ValueError:
                    value_is_json = False

                if not value_is_json:
                    val_match = range_regex.search(row['values'])
                    if val_match:
                        value_min = int(val_match.group('start'))
                        value_max = int(val_match.group('end'))

                    if data_type == Data_Type.ASCII:
                        #value_regex
                        val_match = ascii_value_regex.search(row['values'])
                        if val_match:
                            value_regex = val_match.group('regex') 

                concatenate : bool = False
                concatenate_registers : list[int] = []

                register : int = -1
                register_bit : int = 0
                match = register_regex.search(row['register'])
                if match:
                    register = int(match.group('register'))
                    register_bit = int(match.group('bit'))
                    #print("register: " + str(register) + " bit : " + str(register_bit))
                else:
                    range_match = range_regex.search(row['register'])
                    if not range_match:
                        register = int(row['register'])
                    else:
                        reverse = range_match.group('reverse')
                        start = int(range_match.group('start'))
                        end = int(range_match.group('end'))
                        register = start
                        if end > start:
                            concatenate = True
                            if reverse:
                                for i in range(end, start, -1):
                                    concatenate_registers.append(i-1)
                            else:
                                for i in range(start, end+1):
                                    concatenate_registers.append(i)
                       
                if concatenate_registers:
                    r = range(len(concatenate_registers))
                else:
                    r = range(1)
                
                for i in r:
                    item = registry_map_entry( 
                                                registry_type = registry_type,
                                                register= register,
                                                register_bit=register_bit,
                                                variable_name= variable_name,
                                                documented_name = row['documented name'],
                                                unit= str(character_part),
                                                unit_mod= numeric_part,
                                                data_type= data_type,
                                                concatenate = concatenate,
                                                concatenate_registers = concatenate_registers,
                                                value_min=value_min,
                                                value_max=value_max,
                                                value_regex=value_regex
                                            )
                    registry_map.append(item)
                    register = register + 1
            
            for index in reversed(range(len(registry_map))):
                item = registry_map[index]
                if index > 0:
                    #if high/low, its a double
                    if (
                        item.documented_name.endswith('_l') 
                        and registry_map[index-1].documented_name.replace('_h', '_l') == item.documented_name
                        ):
                        combined_item = registry_map[index-1]

                        if not combined_item.data_type or combined_item.data_type  == Data_Type.USHORT:
                            if registry_map[index].data_type != Data_Type.USHORT:
                                combined_item.data_type = registry_map[index].data_type
                            else:
                                combined_item.data_type = Data_Type.UINT


                        if combined_item.documented_name == combined_item.variable_name:
                            combined_item.variable_name = combined_item.variable_name[:-2].strip()
                            
                        combined_item.documented_name = combined_item.documented_name[:-2].strip()

                        if not combined_item.unit: #fix inconsistsent documentation
                            combined_item.unit = registry_map[index].unit
                            combined_item.unit_mod = registry_map[index].unit_mod

                        del registry_map[index]

            #apply mask
            if self.variable_mask:
                for index in reversed(range(len(registry_map))):
                    item = registry_map[index]
                    if (
                        item.documented_name.strip().lower() not in self.variable_mask 
                        and item.variable_name.strip().lower() not in self.variable_mask
                        ):
                        del registry_map[index]                  

            return registry_map
        
    def calculate_registry_ranges(self, map : list[registry_map_entry], max_register : int) -> list[tuple]:
        ''' read optimization; calculate which ranges to read'''
        max_batch_size = 45 #see manual; says max batch is 45
        start = -max_batch_size
        ranges : list[tuple] = []

        while (start := start+max_batch_size) <= max_register:
            
            registers : list[int] = [] #use a list, im too lazy to write logic

            end = start+max_batch_size
            for register in map:
                if register.register >= start and register.register < end:
                    registers.append(register.register)

            if registers: #not empty
                ranges.append((min(registers), max(registers)-min(registers))) ## APPENDING A TUPLE!

        return ranges


    def load__input_registry_map(self, file : str = '', settings_dir : str = ''):
        if not settings_dir:
            settings_dir = self.settings_dir

        if not file:
            file = self.protocol + '.input_registry_map.csv'

        path = settings_dir + '/' + file

        self.input_registry_map = self.load__registry(path, Registry_Type.INPUT)

        #get max register size
        for item in self.input_registry_map:
            if item.register > self.input_registry_size:
                self.input_registry_size = item.register

        self.input_registry_ranges = self.calculate_registry_ranges(self.input_registry_map, self.input_registry_size)

    def load__holding_registry_map(self, file : str = '', settings_dir : str = ''):
        if not settings_dir:
            settings_dir = self.settings_dir

        if not file:
            file = self.protocol + '.holding_registry_map.csv'

        path = settings_dir + '/' + file

        self.holding_registry_map = self.load__registry(path, Registry_Type.HOLDING)

        #get max register size
        for item in self.holding_registry_map:
            if item.register > self.holding_registry_size:
                self.holding_registry_size = item.register
        
        self.holding_registry_ranges = self.calculate_registry_ranges(self.holding_registry_map, self.holding_registry_size)

        
#settings = protocol_settings('v0.14')