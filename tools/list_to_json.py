import json
import re

# Given string
input_string = "0: 208VAC 1: 230VAC 2: 240VAC 3:220VAC 4:100VAC 5:110VAC 6:120VAC"
while True:
    user_input = input("Enter Data: ")
    user_input  = re.sub(r'\s+', " ", user_input)
    user_input  = re.sub(r'\:\s+', ":", user_input)
    user_input  = re.sub(r'\s+\:', ":", user_input)

    # Split the string into key-value pairs

    if user_input.find(";") != -1:
        pairs = user_input.split(";")
    elif user_input.find("；") != -1:
        pairs = user_input.split("；")
    else:
        pairs = user_input.split()
    

    # Create a dictionary from the key-value pairs
    result = {}
    for pair in pairs:
        if not pair:
            continue

        if pair.find("：") != -1:
            key, value = pair.split("：")
        else:
            key, value = pair.split(":")

        
        result[key.strip()] = value.strip()

    # Convert the dictionary to JSON
    json_result = json.dumps(result)

    print(json_result)
