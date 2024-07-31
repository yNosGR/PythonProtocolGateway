import sys
import os
import pytest

#move up a folder for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from classes.protocol_settings import protocol_settings

# List of protocols to test
protocols = [os.path.splitext(f)[0] for f in os.listdir("protocols") if f.endswith('.json')]


# Parameterized test function
@pytest.mark.parametrize("protocol", protocols)
def test_protocol_setting(protocol : str):
    protocolSettings : protocol_settings = protocol_settings(protocol)

