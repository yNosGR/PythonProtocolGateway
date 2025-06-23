import sys
from configparser import SectionProxy
from typing import TextIO
import time

from defs.common import strtobool

from ..protocol_settings import Registry_Type, WriteMode, registry_map_entry
from .transport_base import transport_base


class influxdb_out(transport_base):
    ''' InfluxDB v1 output transport that writes data to an InfluxDB server '''
    host: str = "localhost"
    port: int = 8086
    database: str = "solar"
    username: str = ""
    password: str = ""
    measurement: str = "device_data"
    include_timestamp: bool = True
    include_device_info: bool = True
    batch_size: int = 100
    batch_timeout: float = 10.0
    
    client = None
    batch_points = []
    last_batch_time = 0

    def __init__(self, settings: SectionProxy):
        self.host = settings.get("host", fallback=self.host)
        self.port = settings.getint("port", fallback=self.port)
        self.database = settings.get("database", fallback=self.database)
        self.username = settings.get("username", fallback=self.username)
        self.password = settings.get("password", fallback=self.password)
        self.measurement = settings.get("measurement", fallback=self.measurement)
        self.include_timestamp = strtobool(settings.get("include_timestamp", fallback=self.include_timestamp))
        self.include_device_info = strtobool(settings.get("include_device_info", fallback=self.include_device_info))
        self.batch_size = settings.getint("batch_size", fallback=self.batch_size)
        self.batch_timeout = settings.getfloat("batch_timeout", fallback=self.batch_timeout)
        
        self.write_enabled = True  # InfluxDB output is always write-enabled
        super().__init__(settings)

    def connect(self):
        """Initialize the InfluxDB client connection"""
        self._log.info("influxdb_out connect")
        
        try:
            from influxdb import InfluxDBClient
            
            # Create InfluxDB client
            self.client = InfluxDBClient(
                host=self.host,
                port=self.port,
                username=self.username if self.username else None,
                password=self.password if self.password else None,
                database=self.database
            )
            
            # Test connection
            self.client.ping()
            
            # Create database if it doesn't exist
            databases = self.client.get_list_database()
            if not any(db['name'] == self.database for db in databases):
                self._log.info(f"Creating database: {self.database}")
                self.client.create_database(self.database)
            
            self.connected = True
            self._log.info(f"Connected to InfluxDB at {self.host}:{self.port}")
            
        except ImportError:
            self._log.error("InfluxDB client not installed. Please install with: pip install influxdb")
            self.connected = False
        except Exception as e:
            self._log.error(f"Failed to connect to InfluxDB: {e}")
            self.connected = False

    def write_data(self, data: dict[str, str], from_transport: transport_base):
        """Write data to InfluxDB"""
        if not self.write_enabled or not self.connected:
            return

        self._log.info(f"write data from [{from_transport.transport_name}] to influxdb_out transport")
        self._log.info(data)

        # Prepare tags for InfluxDB
        tags = {}
        
        # Add device information as tags if enabled
        if self.include_device_info:
            tags.update({
                "device_identifier": from_transport.device_identifier,
                "device_name": from_transport.device_name,
                "device_manufacturer": from_transport.device_manufacturer,
                "device_model": from_transport.device_model,
                "device_serial_number": from_transport.device_serial_number,
                "transport": from_transport.transport_name
            })
        
        # Prepare fields (the actual data values)
        fields = {}
        for key, value in data.items():
            # Check if we should force float formatting based on protocol settings
            should_force_float = False
            
            # Try to get registry entry from protocol settings to check unit_mod
            if hasattr(from_transport, 'protocolSettings') and from_transport.protocolSettings:
                # Check both input and holding registries
                for registry_type in [Registry_Type.INPUT, Registry_Type.HOLDING]:
                    registry_map = from_transport.protocolSettings.get_registry_map(registry_type)
                    for entry in registry_map:
                        if entry.variable_name == key:
                            # If unit_mod is not 1.0, this value should be treated as float
                            if entry.unit_mod != 1.0:
                                should_force_float = True
                                self._log.debug(f"Variable {key} has unit_mod {entry.unit_mod}, forcing float format")
                            break
                    if should_force_float:
                        break
            
            # Try to convert to numeric values for InfluxDB
            try:
                # Try to convert to float first
                float_val = float(value)
                
                # If it's an integer but should be forced to float, or if it's already a float
                if should_force_float or not float_val.is_integer():
                    fields[key] = float_val
                else:
                    fields[key] = int(float_val)
            except (ValueError, TypeError):
                # If conversion fails, store as string
                fields[key] = str(value)
        
        # Create InfluxDB point
        point = {
            "measurement": self.measurement,
            "tags": tags,
            "fields": fields
        }
        
        # Add timestamp if enabled
        if self.include_timestamp:
            point["time"] = int(time.time() * 1e9)  # Convert to nanoseconds
        
        # Add to batch
        self.batch_points.append(point)
        
        # Check if we should flush the batch
        current_time = time.time()
        if (len(self.batch_points) >= self.batch_size or 
            (current_time - self.last_batch_time) >= self.batch_timeout):
            self._flush_batch()

    def _flush_batch(self):
        """Flush the batch of points to InfluxDB"""
        if not self.batch_points:
            return
            
        try:
            self.client.write_points(self.batch_points)
            self._log.info(f"Wrote {len(self.batch_points)} points to InfluxDB")
            self.batch_points = []
            self.last_batch_time = time.time()
        except Exception as e:
            self._log.error(f"Failed to write batch to InfluxDB: {e}")
            self.connected = False

    def init_bridge(self, from_transport: transport_base):
        """Initialize bridge - not needed for InfluxDB output"""
        pass

    def __del__(self):
        """Cleanup on destruction - flush any remaining points"""
        if self.batch_points:
            self._flush_batch()
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass 