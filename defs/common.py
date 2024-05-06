import serial.tools.list_ports
import re

def strtobool (val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    
    return 0

def strtoint(val : str) -> int:
    ''' converts str to int, but allows for hex string input, identified by x prefix'''
    if val and val[0] == 'x':
        return int.from_bytes(bytes.fromhex(val[1:]), byteorder='big')
    
    if val and val.startswith("0x"):
        return int.from_bytes(bytes.fromhex(val[2:]), byteorder='big')
    
    if not val: #empty
        return 0
    
    return int(val)

def get_usb_serial_port_info(port : str = '') -> str:
    for p in serial.tools.list_ports.comports():
        if str(p.device).upper() == port.upper():
            return "["+hex(p.vid)+":"+hex(p.pid)+":"+p.serial_number+":"+p.location+"]"

def find_usb_serial_port(port : str =  '', vendor_id : str = '', product_id : str = '', serial_number : str = '', location : str = '') -> str:
    if not port.startswith('['):
        return port
    
    match  = re.match(r"\[(?P<vendor>[x\d]+|):?(?P<product>[x\d]+|):?(?P<serial>\d+|):?(?P<location>[\d\-]+|)\]", port)
    if match:
        vendor_id = int(match.group("vendor"), 16) if match.group("vendor") else ''
        product_id = int(match.group("product"), 16) if match.group("product") else ''
        serial_number = match.group("serial") if match.group("serial") else ''
        location = match.group("location") if match.group("location") else ''

    for port in serial.tools.list_ports.comports():
        if ((not vendor_id or port.vid == vendor_id) and
            ( not product_id or port.pid == product_id) and
            ( not serial_number or port.serial_number == serial_number) and
            ( not location or port.location == location)):
            return port.device
    return None