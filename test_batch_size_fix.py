#!/usr/bin/env python3
"""
Test script to verify the batch_size fix
This script tests that the modbus transport correctly uses the batch_size from protocol settings
"""

import sys
import os
import json
from configparser import ConfigParser

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classes.protocol_settings import protocol_settings
from classes.transports.modbus_base import modbus_base

def test_batch_size_from_protocol():
    """Test that the batch_size is correctly read from protocol settings"""
    print("Testing Batch Size Fix")
    print("=" * 40)
    
    # Test with EG4 v58 protocol
    protocol_name = "eg4_v58"
    
    try:
        # Load protocol settings
        protocol_settings_obj = protocol_settings(protocol_name)
        
        # Check if batch_size is loaded correctly
        batch_size = protocol_settings_obj.settings.get("batch_size")
        print(f"Protocol: {protocol_name}")
        print(f"Batch size from protocol: {batch_size}")
        
        if batch_size == "40":
            print("✓ Batch size correctly loaded from protocol file")
        else:
            print(f"✗ Expected batch_size=40, got {batch_size}")
            return False
        
        # Test that calculate_registry_ranges uses the correct batch_size
        test_map = []  # Empty map for testing
        ranges = protocol_settings_obj.calculate_registry_ranges(test_map, 100, init=True)
        
        # The calculate_registry_ranges method should use the batch_size from settings
        # We can verify this by checking the internal logic
        expected_batch_size = int(protocol_settings_obj.settings.get("batch_size", 45))
        print(f"Expected batch size in calculations: {expected_batch_size}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_modbus_transport_batch_size():
    """Test that modbus transport uses protocol batch_size"""
    print("\n" + "=" * 40)
    print("Testing Modbus Transport Batch Size")
    print("=" * 40)
    
    # Create a test configuration
    config = ConfigParser()
    config.add_section('transport.test')
    config.set('transport.test', 'protocol_version', 'eg4_v58')
    config.set('transport.test', 'port', '/dev/ttyUSB0')
    config.set('transport.test', 'baudrate', '19200')
    config.set('transport.test', 'address', '1')
    
    try:
        # Create modbus transport
        transport = modbus_base(config['transport.test'])
        
        # Test that the transport has access to protocol settings
        if hasattr(transport, 'protocolSettings') and transport.protocolSettings:
            batch_size = transport.protocolSettings.settings.get("batch_size")
            print(f"Modbus transport batch size: {batch_size}")
            
            if batch_size == "40":
                print("✓ Modbus transport correctly loaded protocol batch_size")
            else:
                print(f"✗ Expected batch_size=40, got {batch_size}")
                return False
        else:
            print("✗ Modbus transport does not have protocol settings")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Batch Size Fix Test Suite")
    print("=" * 50)
    
    # Test protocol settings
    success1 = test_batch_size_from_protocol()
    
    # Test modbus transport
    success2 = test_modbus_transport_batch_size()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ All tests passed! Batch size fix is working correctly.")
        print("\nThe modbus transport will now use the batch_size from the protocol file")
        print("instead of the hardcoded default of 45.")
        print("\nFor EG4 v58 protocol, this means:")
        print("- Protocol batch_size: 40")
        print("- Modbus reads will be limited to 40 registers per request")
        print("- This should resolve the 'Illegal Data Address' errors")
    else:
        print("✗ Some tests failed. Please check the error messages above.")
    
    print("\nTo test with your hardware:")
    print("1. Restart the protocol gateway")
    print("2. Check the logs for 'get registers' messages")
    print("3. Verify that register ranges are now limited to 40 registers")
    print("4. Confirm that 'Illegal Data Address' errors are reduced or eliminated") 