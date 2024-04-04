import csv
from dataclasses import dataclass
from enum import Enum
import itertools
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

class WriteMode(Enum):
    READ = 0x00
    ''' READ ONLY '''
    READDISABLED = 0x01
    ''' DO NOT READ OR WRITE'''
    WRITE = 0x02
    ''' READ AND WRITE '''

    @classmethod
    def fromString(cls, name : str):
        name = name.strip().upper()

        #common alternative names
        alias : dict[str,WriteMode] = {
            "R"     : "READ",
            "READ"  : "READ",
            "WD"    : "READ",
            "RD"            : "READDISABLED",
            "READDISABLED"  : "READDISABLED",
            "DISABLED"      : "READDISABLED",
            "D"             : "READDISABLED",
            "RW"    : "WRITE",
            "W"     : "WRITE",
            "WRITE" : "WRITE"
        }
        
        if name in alias:
            name = alias[name]
        else:
            name = "READ" #default

        return getattr(cls, name)

class Registry_Type(Enum):
    ZERO = 0x00
    ''' for protocols that don't have a command / registry type '''

    HOLDING = 0x03
    INPUT = 0x04
    
@dataclass
class registry_map_entry:
    registry_type : Registry_Type
    register : int
    register_bit : int
    register_byte : int 
    ''' byte offset for canbus ect... '''
    variable_name : str
    documented_name : str
    unit : str
    unit_mod : float
    concatenate : bool
    concatenate_registers : list[int] 

    values : list
    value_regex : str = ""

    value_min : int = 0
    ''' min of value range for protocol analyzing'''
    value_max : int = 65535
    ''' max of value range for protocol analyzing'''

    ''' if value needs to be concatenated with other registers'''
    data_type : Data_Type = Data_Type.USHORT
    data_type_size : int = -1
    ''' for non-fixed size types like ASCII'''

    read_command : bytes = None
    ''' for transports/protocols that require sending a command ontop of "register" '''
 
    write_mode : WriteMode = WriteMode.READ
    ''' enable disable reading/writing '''
    
    def __str__(self):
        return self.variable_name

    def __eq__(self, other):
        return (    isinstance(other, registry_map_entry) 
                    and self.register == other.register 
                    and self.register_bit == other.register_bit
                    and self.registry_type == other.registry_type
                    and self.register_byte == other.register_byte)

    def __hash__(self):
        # Hash based on tuple of object attributes
        return hash((self.variable_name, self.register_bit, self.register_byte, self.registry_type))


class protocol_settings:
    protocol : str
    transport : str
    settings_dir : str
    variable_mask : list[str]
    registry_map : dict[Registry_Type, list[registry_map_entry]] = {}
    registry_map_size : dict[Registry_Type, int] = {}
    registry_map_ranges : dict[Registry_Type, list[tuple]] = {}

    codes : dict[str, str]
    settings : dict[str, str]
    ''' default settings provided by protocol json '''

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

        self.load__json() #load first, so priority to json codes

        if "transport" in self.settings:
            self.transport = self.settings["transport"]
        elif "reader" in self.settings:
            self.transport = self.settings["reader"]
        else:
            self.transport = "modbus_rtu"


        for registry_type in Registry_Type:
            self.load_registry_map(registry_type)

    def get_registry_map(self, registry_type : Registry_Type = Registry_Type.ZERO) -> list[registry_map_entry]:
        return self.registry_map[registry_type]
    
    def get_registry_ranges(self, registry_type : Registry_Type) -> list[registry_map_entry]:
        return self.registry_map_ranges[registry_type]


    def get_holding_registry_entry(self, name : str):
        ''' deprecated '''
        return self.get_registry_entry(name, registry_type=Registry_Type.HOLDING)
    
    def get_input_registry_entry(self, name : str):
        ''' deprecated '''
        return self.get_registry_entry(name, registry_type=Registry_Type.INPUT)

    def get_registry_entry(self, name : str, registry_type : Registry_Type) -> registry_map_entry:
        
        name = name.strip().lower().replace(' ', '_') #clean name
        for item in self.registry_map[registry_type]:
            if item.documented_name == name:
                return item
        
        return None

    def load__json(self, file : str = '', settings_dir : str = ''):
        if not settings_dir:
            settings_dir = self.settings_dir

        if not file:
            file = self.protocol + '.json'

        path = settings_dir + '/' + file

        with open(path) as f:
            self.codes = json.loads(f.read())

        self.settings = {}

        # Iterate over the keys and add entries not ending with "_codes" to self.settings
        for key, value in self.codes.items():
            if not key.endswith("_codes"):
                self.settings[key] = value


    def load__registry(self, path, registry_type : Registry_Type = Registry_Type.INPUT) -> list[registry_map_entry]: 
        registry_map : list[registry_map_entry] = []
        register_regex = re.compile(r'(?P<register>\d+)\.b(?P<bit>\d{1,2})')

        data_type_regex = re.compile(r'(?P<datatype>\w+)\.(?P<length>\d+)')

        range_regex = re.compile(r'(?P<reverse>r|)(?P<start>\d+)[\-~](?P<end>\d+)')
        ascii_value_regex = re.compile(r'(?P<regex>^\[.+\]$)')
        list_regex = re.compile(r'\s*(?:(?P<range_start>\d+)-(?P<range_end>\d+)|(?P<element>[^,\s][^,]*?))\s*(?:,|$)')


        if not os.path.exists(path): #return empty is file doesnt exist.
            return registry_map
        
        def determine_delimiter(first_row) -> str:
            if first_row.count(';') > first_row.count(','):
                return ';'
            else:
                return ','

                
        with open(path, newline='', encoding='latin-1') as csvfile:

            #clean column names before passing to csv dict reader

            delimeter = ';' 
            first_row = next(csvfile).lower().replace('_', ' ')
            if first_row.count(';') < first_row.count(','):
                delimeter = ','

            first_row = re.sub(r"\s+" + re.escape(delimeter) +"|" + re.escape(delimeter) +"\s+", delimeter, first_row) #trim values

            csvfile = itertools.chain([first_row], csvfile) #add clean header to begining of iterator 

            # Create a CSV reader object
            reader = csv.DictReader(csvfile, delimiter=delimeter)

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

                data_type_len : int = -1
                #optional row, only needed for non-default data types
                if 'data type' in row and row['data type']:
                    matches = data_type_regex.search(row['data type'])
                    if matches:
                        data_type_len = int(matches.group('length'))
                        data_type = Data_Type.fromString(matches.group('datatype'))
                    else:
                        data_type = Data_Type.fromString(row['data type'])


                #get value range for protocol analyzer
                values : list = []
                value_min : int = 0
                value_max : int = 65535 #default - max value for ushort
                value_regex : str = ""
                value_is_json : bool = False

                #test if value is json.
                if "{" in row['values']: #to try and stop non-json values from parsing. the json parser is buggy for validation
                    try:
                        codes_json = json.loads(row['values'])
                        value_is_json = True

                        name = row['documented name']+'_codes'
                        if name not in self.codes:
                            self.codes[name] = codes_json

                    except ValueError:
                        value_is_json = False

                if not value_is_json:
                    if ',' in row['values']:
                        matches = list_regex.finditer(row['values'])

                        for match in matches:
                            groups = match.groupdict()
                            if groups['range_start'] and groups['range_end']:
                                start = int(groups['range_start'])
                                end = int(groups['range_end'])
                                values.extend(range(start, end + 1))
                            else:
                                values.append(groups['element'])
                    else:
                        matched : bool = False
                        val_match = range_regex.search(row['values'])
                        if val_match:
                            value_min = int(val_match.group('start'))
                            value_max = int(val_match.group('end'))
                            matched = True

                        if data_type == Data_Type.ASCII:
                            #value_regex
                            val_match = ascii_value_regex.search(row['values'])
                            if val_match:
                                value_regex = val_match.group('regex') 
                                matched = True

                        if not matched: #single value
                            values.append(row['values'])

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
                        if row['register'][0] == 'x':
                            register = int.from_bytes(bytes.fromhex(row['register'][1:]), byteorder='big')
                        else:   
                            register = int(row['register'])
                    else:
                        reverse = range_match.group('reverse')
                        start = int(range_match.group('start'))
                        end = int(range_match.group('end'))
                        register = start
                        if end > start:
                            concatenate = True
                            if reverse:
                                for i in range(end, start-1, -1):
                                    concatenate_registers.append(i)
                            else:
                                for i in range(start, end+1):
                                    concatenate_registers.append(i)
                       
                if concatenate_registers:
                    r = range(len(concatenate_registers))
                else:
                    r = range(1)

                read_command = None
                if "read command" in row:
                    if row['read command'][0] == 'x':
                        read_command = bytes.fromhex(row['read command'][1:])
                    else:
                        read_command = row['read command'].encode('utf-8')

                writeMode : WriteMode = WriteMode.READ
                if "writable" in row:
                    writeMode = WriteMode.fromString(row['writable'])
                
                for i in r:
                    item = registry_map_entry(
                                                registry_type = registry_type,
                                                register= register,
                                                register_bit=register_bit,
                                                register_byte= -1,
                                                variable_name= variable_name,
                                                documented_name = row['documented name'],
                                                unit= str(character_part),
                                                unit_mod= numeric_part,
                                                data_type= data_type,
                                                data_type_len = data_type_len,
                                                concatenate = concatenate,
                                                concatenate_registers = concatenate_registers,
                                                values=values,
                                                value_min=value_min,
                                                value_max=value_max,
                                                value_regex=value_regex,
                                                read_command = read_command,
                                                write_mode=writeMode
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

        if "batch_size" in self.settings:
            try:
                max_batch_size = int(self.settings['batch_size'])
            except ValueError:
                pass

        start = -max_batch_size
        ranges : list[tuple] = []

        while (start := start+max_batch_size) <= max_register:
            
            registers : list[int] = [] #use a list, im too lazy to write logic

            end = start+max_batch_size
            for register in map:
                if register.register >= start and register.register < end:
                    if register.write_mode == WriteMode.READDISABLED: ##register is disabled; skip
                        continue
                    registers.append(register.register)

            if registers: #not empty
                ranges.append((min(registers), max(registers)-min(registers)+1)) ## APPENDING A TUPLE!

        return ranges

    def load_registry_map(self, registry_type : Registry_Type, file : str = '', settings_dir : str = ''):
        if not settings_dir:
            settings_dir = self.settings_dir

        if not file:
            if registry_type == Registry_Type.ZERO:
                file = self.protocol + '.registry_map.csv'
            else:
                file = self.protocol + '.'+registry_type.name.lower()+'_registry_map.csv'

        path = settings_dir + '/' + file

        self.registry_map[registry_type] = self.load__registry(path, registry_type)

        size : int = 0
        
        #get max register size
        for item in self.registry_map[registry_type]:
            if item.register > size:
                size = item.register

        self.registry_map_size[registry_type] = size
        self.registry_map_ranges[registry_type] = self.calculate_registry_ranges(self.registry_map[registry_type], self.registry_map_size[registry_type])


    def validate_registry_entry(self, entry : registry_map_entry, val) -> int:
            #if code, validate first. 
            if entry.documented_name+'_codes' in self.codes:
                if val in self.codes[entry.documented_name+'_codes']:
                    return 1
                else:
                    return 0

            if entry.data_type == Data_Type.ASCII:
                if val and not re.match('[^a-zA-Z0-9\_\-]', val): #validate ascii
                    if entry.value_regex: #regex validation
                        if re.match(entry.value_regex, val):
                            if entry.concatenate:
                                return len(entry.concatenate_registers)

            else: #default type
                if int(val) >= entry.value_min and int(val) <= entry.value_max:
                    return 1

            return 0    
#settings = protocol_settings('v0.14')