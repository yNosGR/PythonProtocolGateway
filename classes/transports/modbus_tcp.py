import inspect

from classes.protocol_settings import Registry_Type, protocol_settings

#compatability
try:
    from pymodbus.client.sync import ModbusTcpClient
except ImportError:
    from pymodbus.client import ModbusTcpClient

from configparser import SectionProxy

from .modbus_base import modbus_base


class modbus_tcp(modbus_base):
    port : str = 502
    host : str = ""
    client : ModbusTcpClient
    pymodbus_slave_arg = "unit"

    def __init__(self, settings : SectionProxy, protocolSettings : protocol_settings = None):
        self.host = settings.get("host", "")
        if not self.host:
            raise ValueError("Host is not set")

        self.port = settings.getint("port", self.port)

        client_str = self.host+"("+str(self.port)+")"
        #check if client is already initialied
        if client_str in modbus_base.clients:
            self.client = modbus_base.clients[client_str]
            # Set compatibility flag based on existing client
            self._set_compatibility_flag()
            super().__init__(settings, protocolSettings=protocolSettings)
            return

        self.client = ModbusTcpClient(host=self.host, port=self.port, timeout=7, retries=3)

        # Set compatibility flag based on created client
        self._set_compatibility_flag()

        #add to clients
        modbus_base.clients[client_str] = self.client

        super().__init__(settings, protocolSettings=protocolSettings)

    def _set_compatibility_flag(self):
        """Determine the correct parameter name for slave/unit based on pymodbus version"""
        self.pymodbus_slave_arg = None
        
        try:
            # For pymodbus 3.7+, we don't need unit/slave parameter
            import pymodbus
            version = pymodbus.__version__
            
            # pymodbus 3.7+ doesn't need slave/unit parameter for most operations
            if version.startswith('3.'):
                self.pymodbus_slave_arg = None
            else:
                # Fallback for any other versions - assume newer API
                self.pymodbus_slave_arg = None
                
        except (ImportError, AttributeError):
            # If we can't determine version, assume newer API (3.7+)
            self.pymodbus_slave_arg = None

    def write_register(self, register : int, value : int, **kwargs):
        if not self.write_enabled:
            return

        # Only add unit/slave parameter if the pymodbus version supports it
        if self.pymodbus_slave_arg is not None:
            if self.pymodbus_slave_arg not in kwargs:
                kwargs[self.pymodbus_slave_arg] = 1

        self.client.write_register(register, value, **kwargs) #function code 0x06 writes to holding register

    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):

        # Only add unit/slave parameter if the pymodbus version supports it
        if self.pymodbus_slave_arg is not None:
            if self.pymodbus_slave_arg not in kwargs:
                kwargs[self.pymodbus_slave_arg] = 1

        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(start, count, **kwargs  )
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(start, count, **kwargs)

    def connect(self):
        self.connected = self.client.connect()
        super().connect()
