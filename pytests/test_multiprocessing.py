#!/usr/bin/env python3
"""
Test script for multiprocessing implementation
"""

import os
import sys
import time

# Add the current directory to the path so we can import the gateway
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from protocol_gateway import Protocol_Gateway

def test_multiprocessing():
    """
    Test the multiprocessing implementation
    """
    print("Testing multiprocessing implementation...")
    
    # Test with a config file that has multiple transports
    config_file = "config.cfg"
    
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found. Please create a config with multiple transports.")
        return
    
    try:
        # Create the gateway
        gateway = Protocol_Gateway(config_file)
        
        print(f"Found {len(gateway._Protocol_Gateway__transports)} transports:")
        for transport in gateway._Protocol_Gateway__transports:
            transport_type = "INPUT" if transport.read_interval > 0 else "OUTPUT"
            print(f"  - {transport.transport_name}: {transport_type} transport")
            if hasattr(transport, 'bridge') and transport.bridge:
                print(f"    Bridges to: {transport.bridge}")
        
        # Test the multiprocessing mode
        print("\nStarting multiprocessing test (will run for 30 seconds)...")
        print("Press Ctrl+C to stop early")
        
        # Start the gateway in a separate thread so we can monitor it
        import threading
        import signal
        
        def run_gateway():
            try:
                gateway.run()
            except KeyboardInterrupt:
                print("Gateway stopped by user")
        
        gateway_thread = threading.Thread(target=run_gateway)
        gateway_thread.daemon = True
        gateway_thread.start()
        
        # Monitor for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            time.sleep(1)
            print(f"Running... ({int(time.time() - start_time)}s elapsed)")
        
        print("Test completed successfully!")
        
    except Exception as err:
        print(f"Error during test: {err}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multiprocessing() 