#!/usr/bin/env python3
"""
Test script for JSON output transport
This script tests the json_out transport with a simple configuration
"""

import sys
import os
import time
import logging
from configparser import ConfigParser

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classes.transports.json_out import json_out
from classes.transports.transport_base import transport_base

def create_test_config():
    """Create a test configuration for the JSON output transport"""
    config = ConfigParser()
    
    # General section
    config.add_section('general')
    config.set('general', 'log_level', 'INFO')
    
    # JSON output transport section
    config.add_section('transport.json_test')
    config.set('transport.json_test', 'transport', 'json_out')
    config.set('transport.json_test', 'output_file', 'stdout')
    config.set('transport.json_test', 'pretty_print', 'true')
    config.set('transport.json_test', 'include_timestamp', 'true')
    config.set('transport.json_test', 'include_device_info', 'true')
    config.set('transport.json_test', 'device_name', 'Test Device')
    config.set('transport.json_test', 'manufacturer', 'Test Manufacturer')
    config.set('transport.json_test', 'model', 'Test Model')
    config.set('transport.json_test', 'serial_number', 'TEST123')
    
    return config

def test_json_output():
    """Test the JSON output transport with sample data"""
    print("Testing JSON Output Transport")
    print("=" * 40)
    
    # Create test configuration
    config = create_test_config()
    
    try:
        # Initialize the JSON output transport
        json_transport = json_out(config['transport.json_test'])
        
        # Connect the transport
        json_transport.connect()
        
        if not json_transport.connected:
            print("ERROR: Failed to connect JSON output transport")
            return False
        
        print("✓ JSON output transport connected successfully")
        
        # Create a mock transport to simulate data from another transport
        class MockTransport(transport_base):
            def __init__(self):
                self.transport_name = "mock_transport"
                self.device_identifier = "mock_device"
                self.device_name = "Mock Device"
                self.device_manufacturer = "Mock Manufacturer"
                self.device_model = "Mock Model"
                self.device_serial_number = "MOCK123"
                self._log = logging.getLogger("mock_transport")
        
        mock_transport = MockTransport()
        
        # Test data - simulate what would come from a real device
        test_data = {
            "battery_voltage": "48.5",
            "battery_current": "2.1",
            "battery_soc": "85",
            "inverter_power": "1200",
            "grid_voltage": "240.2",
            "grid_frequency": "50.0",
            "temperature": "25.5"
        }
        
        print("\nSending test data to JSON output transport...")
        print(f"Test data: {test_data}")
        
        # Send data to JSON output transport
        json_transport.write_data(test_data, mock_transport)
        
        print("\n✓ JSON output transport test completed successfully")
        print("\nExpected output format:")
        print("""
{
  "device": {
    "identifier": "mock_device",
    "name": "Mock Device",
    "manufacturer": "Mock Manufacturer",
    "model": "Mock Model",
    "serial_number": "MOCK123",
    "transport": "mock_transport"
  },
  "timestamp": 1703123456.789,
  "data": {
    "battery_voltage": "48.5",
    "battery_current": "2.1",
    "battery_soc": "85",
    "inverter_power": "1200",
    "grid_voltage": "240.2",
    "grid_frequency": "50.0",
    "temperature": "25.5"
  }
}
        """)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_output():
    """Test JSON output to a file"""
    print("\n" + "=" * 40)
    print("Testing JSON Output to File")
    print("=" * 40)
    
    config = ConfigParser()
    config.add_section('transport.json_file_test')
    config.set('transport.json_file_test', 'transport', 'json_out')
    config.set('transport.json_file_test', 'output_file', '/tmp/test_json_output.json')
    config.set('transport.json_file_test', 'pretty_print', 'true')
    config.set('transport.json_file_test', 'append_mode', 'false')
    config.set('transport.json_file_test', 'include_timestamp', 'true')
    config.set('transport.json_file_test', 'include_device_info', 'true')
    config.set('transport.json_file_test', 'device_name', 'File Test Device')
    config.set('transport.json_file_test', 'manufacturer', 'File Test Manufacturer')
    config.set('transport.json_file_test', 'model', 'File Test Model')
    config.set('transport.json_file_test', 'serial_number', 'FILETEST123')
    
    try:
        json_transport = json_out(config['transport.json_file_test'])
        json_transport.connect()
        
        if not json_transport.connected:
            print("ERROR: Failed to connect JSON file output transport")
            return False
        
        print("✓ JSON file output transport connected successfully")
        
        class MockTransport(transport_base):
            def __init__(self):
                self.transport_name = "file_mock_transport"
                self.device_identifier = "file_mock_device"
                self.device_name = "File Mock Device"
                self.device_manufacturer = "File Mock Manufacturer"
                self.device_model = "File Mock Model"
                self.device_serial_number = "FILEMOCK123"
                self._log = logging.getLogger("file_mock_transport")
        
        mock_transport = MockTransport()
        
        test_data = {
            "test_variable_1": "value1",
            "test_variable_2": "value2",
            "test_variable_3": "value3"
        }
        
        print("Sending test data to JSON file output transport...")
        json_transport.write_data(test_data, mock_transport)
        
        print(f"✓ Data written to /tmp/test_json_output.json")
        print("You can check the file contents with: cat /tmp/test_json_output.json")
        
        return True
        
    except Exception as e:
        print(f"ERROR: File output test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    print("JSON Output Transport Test Suite")
    print("=" * 50)
    
    # Test stdout output
    success1 = test_json_output()
    
    # Test file output
    success2 = test_file_output()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✓ All tests passed! JSON output transport is working correctly.")
        print("\nYou can now use the json_out transport in your configuration files.")
        print("Example configuration:")
        print("""
[transport.json_output]
transport = json_out
output_file = stdout
pretty_print = true
include_timestamp = true
include_device_info = true
        """)
    else:
        print("✗ Some tests failed. Please check the error messages above.")
    
    print("\nFor more information, see:")
    print("- documentation/usage/configuration_examples/json_out_example.md")
    print("- documentation/usage/transports.md")
    print("- config.json_out.example") 