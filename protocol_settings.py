import csv
from dataclasses import dataclass
import json
import re
import os


@dataclass
class registry_map_entry:
    register : int
    variable_name : str
    documented_name : str
    unit : str
    unit_mod : float
    bytes : int = 1

class protocol_settings:
    protocol : str
    settings_dir : str
    variable_mask : list[str]
    input_registry_map : list[registry_map_entry]
    input_registry_size : int = 0
    holding_registry_map : list[registry_map_entry]
    holding_registry_size : int = 0
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

        with open(path, newline='') as csvfile:
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
                    matches = re.findall(r'([0-9.]+)|(.*?)', row['unit'])

                    # Iterate over the matches and assign them to appropriate variables
                    for match in matches:
                        if match[0]:  # If it matches a numeric part
                            numeric_part = float(match[0])
                        elif match[1]:  # If it matches a character part
                            character_part = match[1].strip()

                #clean up doc name, for extra parsing
                row['documented name'] = row['documented name'].strip().lower().replace(' ', '_')

                variable_name = row['variable name'] if row['variable name'] else row['documented name']
                variable_name = variable_name.lower().replace(' ', '_') #clean name

                #convert to float
                try:
                    numeric_part = float(numeric_part)
                except:
                    numeric_part = float(1)

                if numeric_part == 0:
                    numeric_part = float(1)
                
                item = registry_map_entry( 
                                            register= int(row['register']),
                                            variable_name= variable_name,
                                            documented_name = row['documented name'],
                                            unit= str(character_part),
                                            unit_mod= numeric_part
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
                        combined_item.bytes = 2

                        if combined_item.documented_name == combined_item.variable_name:
                            combined_item.variable_name = combined_item.variable_name[:-2].strip()
                            
                        combined_item.documented_name = combined_item.documented_name[:-2].strip()
                        del registry_map[index]

            #apply mask
            if self.variable_mask:
                for index in reversed(range(len(registry_map))):
                    item = registry_map[index]
                    if (
                        item.documented_name.strip().lower() not in self.variable_mask 
                        and item.variable_name.strip().lower() not in self.variable_mask
                        ):
                        print("del " + item.documented_name)
                        del registry_map[index]
                        
            return registry_map

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

                    
settings = protocol_settings('v0.14')