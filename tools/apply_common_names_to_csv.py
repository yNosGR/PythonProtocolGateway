import csv
import json

path = 'protocols/sigineer_v0.11.input_registry_map.csv'
save_path = 'protocols/sigineer_v0.11.input_registry_map.common_names.csv'

common_path = 'tools/common_names.json'

common_names : dict[str,str] = {}

# Open the file and load the JSON data
with open(common_path, 'r') as file:
    common_names = json.load(file)


new_csv : list[dict[str,str]] = []
with open(path, newline='') as csvfile:
    # Create a CSV reader object
    reader = csv.DictReader(csvfile, delimiter=';') #compensate for openoffice
    fieldnames = reader.fieldnames

    # Iterate over each row in the CSV file
    for row in reader:
        if not row['variable name'] and row['documented name']:
            if row['documented name'] not in common_names:
                print('no friendly name : ' + row['documented name'])
                new_csv.append(row)
                continue

            if not row['variable name'].strip(): #if empty, apply name
                row['variable name'] = common_names[row['documented name']] 
                print(row['documented name'] + ' -> ' + common_names[row['documented name']])
                new_csv.append(row)

# Write data to the output CSV
with open(save_path, 'w', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()  
    writer.writerows(new_csv) 

print("saved to "+save_path)