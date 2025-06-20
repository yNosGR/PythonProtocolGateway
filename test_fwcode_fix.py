#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.protocol_settings import protocol_settings, Registry_Type

def test_fwcode_processing():
    """Test that the firmware code concatenated ASCII processing works correctly"""
    print("Testing firmware code processing...")
    
    ps = protocol_settings('eg4_v58')
    
    # Create a mock registry with sample firmware code values
    # Assuming registers 7 and 8 contain ASCII characters for firmware code
    mock_registry = {
        7: 0x4142,   # 'AB' in ASCII (0x41='A', 0x42='B')
        8: 0x4344,   # 'CD' in ASCII (0x43='C', 0x44='D')
    }
    
    # Get the registry map
    registry_map = ps.get_registry_map(Registry_Type.HOLDING)
    
    # Process the registry
    results = ps.process_registery(mock_registry, registry_map)
    
    # Check if fwcode was processed
    if 'fwcode' in results:
        print(f"SUCCESS: fwcode = '{results['fwcode']}'")
        expected = "ABCD"
        if results['fwcode'] == expected:
            print(f"SUCCESS: Expected '{expected}', got '{results['fwcode']}'")
            return True
        else:
            print(f"ERROR: Expected '{expected}', got '{results['fwcode']}'")
            return False
    else:
        print("ERROR: fwcode not found in results")
        print(f"Available keys: {list(results.keys())}")
        return False

if __name__ == "__main__":
    success = test_fwcode_processing()
    sys.exit(0 if success else 1) 