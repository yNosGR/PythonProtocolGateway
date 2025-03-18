import sys
import os

#move up a folder for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from protocol_gateway import CustomConfigParser

def test_example_cfg():
    parser = CustomConfigParser()
    parser.read("config.cfg.example")
