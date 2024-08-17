import sys
import os
import pytest
import glob


#move up a folder for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from classes.protocol_settings import protocol_settings

# List of protocols to test
# Create the search pattern to find .json files recursively
search_pattern = os.path.join("protocols", '**', '*.json')
# Use glob to find all files matching the pattern
files = glob.glob(search_pattern, recursive=True)
# Extract file names without extension
protocols = [os.path.splitext(os.path.basename(f))[0] for f in files]


# Parameterized test function
@pytest.mark.parametrize("protocol", protocols)
def test_protocol_setting(protocol : str):
    print(protocol)
    protocolSettings : protocol_settings = protocol_settings(protocol)

