
#pip install "python-can[gs_usb]"

import can #v4.2.0+
import usb #pyusb - requires https://github.com/mcuee/libusb-win32 - windows only.


bus = can.interface.Bus(bustype='gs_usb', channel='can0', bitrate=500000)


# Stock slcan firmware on Windows
#bus = can.interface.Bus(bustype='slcan', channel='COM0', bitrate=500000)

# Candlelight firmware on windows
#USB\VID_1D50&PID_606F&REV_0000&MI_00
if False:
    dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
    bus = can.Bus(interface="gs_usb", channel=dev.product, index=0, bitrate=250000)





# Listen for messages
try:
    while True:
        msg = bus.recv()  # Block until a message is received

        # Check if it's the State of Charge (SoC) message (ID: 0x0FFF)
        if msg.arbitration_id == 0x0FFF:
            # The data is a 2-byte value (un16)
            soc_bytes = msg.data[:2]
            soc = int.from_bytes(soc_bytes, byteorder='big', signed=False) / 100.0
            
            print(f"State of Charge: {soc:.2f}%")

except KeyboardInterrupt:
    print("Listening stopped.")

quit()

import re
import ast


# Define the register string
register = "x4642.[ 1 + ((( [battery 1 number of cells] *2 )+ (1~[battery 1 number of temperature] *2)) ) ]"

# Define variables
vars = {"battery 1 number of cells": 8, "battery 1 number of temperature": 2}

# Function to evaluate mathematical expressions
def evaluate_variables(expression):
    # Define a regular expression pattern to match variables
    var_pattern = re.compile(r'\[([^\[\]]+)\]')

    # Replace variables in the expression with their values
    def replace_vars(match):
        var_name = match.group(1)
        if var_name in vars:
            return str(vars[var_name])
        else:
            return match.group(0)

    # Replace variables with their values
    return var_pattern.sub(replace_vars, expression)

def evaluate_ranges(expression):
    # Define a regular expression pattern to match ranges
    range_pattern = re.compile(r'\[.*?((?P<start>\d+)\s?\~\s?(?P<end>\d+)).*?\]')

    # Find all ranges in the expression
    ranges = range_pattern.findall(expression)

    # If there are no ranges, return the expression as is
    if not ranges:
        return [expression]

    # Initialize list to store results
    results = []

    # Iterate over each range found in the expression
    for group, range_start, range_end in ranges:
        range_start = int(range_start)
        range_end = int(range_end)
        if range_start > range_end:
            range_start, range_end = range_end, range_start #swap

        # Generate duplicate entries for each value in the range
        for i in range(range_start, range_end + 1):
            replaced_expression = expression.replace(group, str(i))
            results.append(replaced_expression)

    return results

def evaluate_expression(expression):   
     # Define a regular expression pattern to match "maths"
    var_pattern = re.compile(r'\[(?P<maths>.*?)\]')

    # Replace variables in the expression with their values
    def replace_vars(match):
        try:
            maths = match.group("maths")
            maths = re.sub(r'\s', '', maths) #remove spaces, because ast.parse doesnt like them
            
            # Parse the expression safely
            tree = ast.parse(maths, mode='eval')

            # Evaluate the expression
            end_value = eval(compile(tree, filename='', mode='eval'))
                
            return str(end_value)
        except :
            return match.group(0)

    # Replace variables with their values
    return var_pattern.sub(replace_vars, expression)


# Evaluate the register string
result = evaluate_variables(register)
print("Result:", result)

result = evaluate_ranges(result)
print("Result:", result)

results = []
for r in result:
    results.extend(evaluate_ranges(r))

for r in results:
    print(evaluate_expression(r))
