import csv
import json

path = 'protocols/v0.14.input_registry_map.csv'

save_path = 'tools/common_names.json'


common_names = {}
common_path = 'tools/common_names.json' #load existing names
common_names : dict[str,str] = {}

# Open the file and load the JSON data
with open(common_path, 'r') as file:
    common_names = json.load(file)

with open(path, newline='') as csvfile:
    # Create a CSV reader object
    reader = csv.DictReader(csvfile, delimiter=';') #compensate for openoffice
    
    # Iterate over each row in the CSV file
    for row in reader:
        if row['variable name'] and row['documented name']:
            if row['documented name'] in common_names and common_names[row['documented name']] != row['variable name']:
                print('Warning, Naming Conflict')
                print(row['documented name'] + ' -> ' +  row['variable name'])
                print(row['documented name'] + ' -> ' +  common_names[row['documented name']])
            else:
                common_names[row['documented name']] = row['variable name']

json_str = json.dumps(common_names, indent=1)

if not save_path:
    print(json_str)
    quit()

with open(save_path, 'w') as file:
    file.write(json_str)

print("saved to "+save_path)