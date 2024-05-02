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
    
    if not val: #empty
        return 0
    
    return int(val)