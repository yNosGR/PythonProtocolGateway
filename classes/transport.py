import importlib

from .transports.transport_base import transport_base
from .protocol_settings import protocol_settings
from configparser import ConfigParser


class Transport():
    ''' i need a better name for this F...'''
    type : str 
    transport : transport_base
    settings : dict[str, object]
    def __init__(self, type : str, settings : ConfigParser) -> None:
        self.type = type
        # Import the module
        module = importlib.import_module('classes.transports.'+self.type)
        # Get the class from the module
        cls = getattr(module, self.type)

        self.transport : transport_base = cls(settings)
