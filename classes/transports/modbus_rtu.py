import inspect

from classes.protocol_settings import Registry_Type, protocol_settings

try:
    from pymodbus.client.sync import ModbusSerialClient
except ImportError:
    from pymodbus.client import ModbusSerialClient


from configparser import SectionProxy

from defs.common import find_usb_serial_port, get_usb_serial_port_info, strtoint

from .modbus_base import modbus_base


class modbus_rtu(modbus_base):
    port : str = "/dev/ttyUSB0"
    addresses : list[int] = []
    baudrate : int = 9600
    client : ModbusSerialClient

    pymodbus_slave_arg = "unit"

    def __init__(self, settings : SectionProxy, protocolSettings : protocol_settings = None):
        super().__init__(settings, protocolSettings=protocolSettings)

        self.port = settings.get("port", "")
        if not self.port:
            raise ValueError("Port is not set")

        self.port = find_usb_serial_port(self.port)
        if not self.port:
            raise ValueError("Port is not valid / not found")

        print("Serial Port : " + self.port + " = ", get_usb_serial_port_info(self.port)) #print for config convience

        if "baud" in self.protocolSettings.settings:
            self.baudrate = strtoint(self.protocolSettings.settings["baud"])

        self.baudrate = settings.getint("baudrate", self.baudrate)

        address : int = settings.getint("address", 0)
        self.addresses = [address]

        # Get the signature of the __init__ method
        init_signature = inspect.signature(ModbusSerialClient.__init__)

        client_str = self.port+"("+str(self.baudrate)+")"

        if client_str in modbus_base.clients:
            self.client = modbus_base.clients[client_str]
            # Set compatibility flag based on existing client
            self._set_compatibility_flag()
        else:
            if "method" in init_signature.parameters:
                self.client = ModbusSerialClient(method="rtu", port=self.port,
                                            baudrate=int(self.baudrate),
                                            stopbits=1, parity="N", bytesize=8, timeout=2
                                            )
            else:
                self.client = ModbusSerialClient(
                                port=self.port,
                                baudrate=int(self.baudrate),
                                stopbits=1, parity="N", bytesize=8, timeout=2
                                )

            # Set compatibility flag based on created client
            self._set_compatibility_flag()

            #add to clients
            modbus_base.clients[client_str] = self.client

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

    def read_registers(self, start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):

        # Only add unit/slave parameter if the pymodbus version supports it
        if self.pymodbus_slave_arg is not None:
            if self.pymodbus_slave_arg not in kwargs:
                # Ensure addresses is initialized
                if not hasattr(self, 'addresses') or not self.addresses:
                    # Try to get address from settings if not already set
                    if hasattr(self, 'settings'):
                        address = self.settings.getint("address", 0)
                        self.addresses = [address]
                    else:
                        # Fallback to default address
                        self.addresses = [1]
                
                kwargs[self.pymodbus_slave_arg] = int(self.addresses[0])

        if registry_type == Registry_Type.INPUT:
            return self.client.read_input_registers(address=start, count=count, **kwargs)
        elif registry_type == Registry_Type.HOLDING:
            return self.client.read_holding_registers(address=start, count=count, **kwargs)

    def write_register(self, register : int, value : int, **kwargs):
        if not self.write_enabled:
            return

        # Only add unit/slave parameter if the pymodbus version supports it
        if self.pymodbus_slave_arg is not None:
            if self.pymodbus_slave_arg not in kwargs:
                # Ensure addresses is initialized
                if not hasattr(self, 'addresses') or not self.addresses:
                    # Try to get address from settings if not already set
                    if hasattr(self, 'settings'):
                        address = self.settings.getint("address", 0)
                        self.addresses = [address]
                    else:
                        # Fallback to default address
                        self.addresses = [1]
                
                kwargs[self.pymodbus_slave_arg] = self.addresses[0]

        self.client.write_register(register, value, **kwargs) #function code 0x06 writes to holding register

    def connect(self):
        print("DEBUG: modbus_rtu.connect() called")
        # Ensure client is initialized before trying to connect
        if not hasattr(self, 'client') or self.client is None:
            print("DEBUG: Client not found, re-initializing...")
            # Re-initialize the client if it wasn't set properly
            client_str = self.port+"("+str(self.baudrate)+")"
            
            if client_str in modbus_base.clients:
                self.client = modbus_base.clients[client_str]
            else:
                # Get the signature of the __init__ method
                init_signature = inspect.signature(ModbusSerialClient.__init__)
                
                if "method" in init_signature.parameters:
                    self.client = ModbusSerialClient(method="rtu", port=self.port,
                                                baudrate=int(self.baudrate),
                                                stopbits=1, parity="N", bytesize=8, timeout=2
                                                )
                else:
                    self.client = ModbusSerialClient(
                                    port=self.port,
                                    baudrate=int(self.baudrate),
                                    stopbits=1, parity="N", bytesize=8, timeout=2
                                    )
                
                #add to clients
                modbus_base.clients[client_str] = self.client
            
            # Set compatibility flag
            self._set_compatibility_flag()
        
        print(f"DEBUG: Attempting to connect to {self.port} at {self.baudrate} baud...")
        self.connected = self.client.connect()
        print(f"DEBUG: Connection result: {self.connected}")
        super().connect()
