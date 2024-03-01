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

    _1BIT = 11,
    _2BIT = 12, 
    _3BIT = 13,
    _4BIT = 14, 
    _5BIT = 15, 
    _6BIT = 16, 
    _7BIT = 17, 
    _8BIT = 18, 
    _9BIT = 19, 
    _10BIT = 20, 
    _11BIT = 21, 
    _12BIT = 22, 
    _13BIT = 23,
    _14BIT = 24, 
    _15BIT = 25,
    _16BIT = 26
    @classmethod
    def fromString(cls, name : str):
        name = name.strip().upper()
        if name[0].isdigit():
            name = "_"+name
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

        if data_type.value > 10: 
            return data_type.value-10

        return -1 #should never happen
@dataclass
class registry_map_entry:
    register : int
    register_bit : int
    variable_name : str
    documented_name : str
    unit : str
    unit_mod : float
    data_type : Data_Type = Data_Type.USHORT

class protocol_settings:
    protocol : str
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

        self.load__input_registry_map()
        self.load__holding_registry_map()
        self.load__codes()

    def get_holding_registry_entry(self, name : str):
        return self.get_registry_entry(name, self.holding_registry_map)
    
    def get_input_registry_entry(self, name : str):
        return self.get_registry_entry(name, self.input_registry_map)

    def get_registry_entry(self, name : str, map : list[registry_map_entry]) -> registry_map_entry | None:
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

    def load__registry(self, path) -> list[registry_map_entry]: 
        registry_map : list[registry_map_entry] = []
        register_regex = re.compile(r'(?P<register>\d+)\.b(?P<bit>\d{1,2})')

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
                variable_name = variable_name.lower().replace(' ', '_').replace('__', '_') #clean name

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

                #optional row, only needed for non-default data types
                if 'data type' in row and row['data type']:
                    data_type = Data_Type.fromString(row['data type'])

                register : int = -1;
                register_bit : int = 0;
                match = register_regex.search(row['register'])
                if match:
                    register = int(match.group('register'))
                    register_bit = int(match.group('bit'))
                    print("register: " + str(register) + " bit : " + str(register_bit))
                else:
                    register = int(row['register'])
                
                
                item = registry_map_entry( 
                                            register= register,
                                            register_bit=register_bit,
                                            variable_name= variable_name,
                                            documented_name = row['documented name'],
                                            unit= str(character_part),
                                            unit_mod= numeric_part,
                                            data_type= data_type
                                        )

                registry_map.append(item)
            
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

        self.input_registry_map = self.load__registry(path)

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

        self.holding_registry_map = self.load__registry(path)

        #get max register size
        for item in self.holding_registry_map:
            if item.register > self.holding_registry_size:
                self.holding_registry_size = item.register
        
        self.holding_registry_ranges = self.calculate_registry_ranges(self.holding_registry_map, self.holding_registry_size)

        
#settings = protocol_settings('v0.14')