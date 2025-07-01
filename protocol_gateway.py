#!/usr/bin/env python3
"""
Main module for Growatt / Inverters ModBus RTU data to MQTT
"""


import importlib
import sys
import time

# Check if Python version is greater than 3.9
if sys.version_info < (3, 9):
    print("==================================================")
    print("WARNING: python version 3.9 or higher is recommended")
    print("Current version: " + sys.version)
    print("Please upgrade your python version to 3.9")
    print("==================================================")
    time.sleep(4)


import argparse
import logging
import os
import sys
import traceback
import multiprocessing
from configparser import ConfigParser, NoOptionError

from classes.protocol_settings import protocol_settings, registry_map_entry
from classes.transports.transport_base import transport_base

# Global queue for inter-process communication
bridge_queue = None

__logo = """

██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗
██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║
██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║
██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║
██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║
╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗          ██████╗  █████╗ ████████╗███████╗██╗    ██╗ █████╗ ██╗   ██╗
██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║         ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝██║    ██║██╔══██╗╚██╗ ██╔╝
██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║         ██║  ███╗███████║   ██║   █████╗  ██║ █╗ ██║███████║ ╚████╔╝
██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║         ██║   ██║██╔══██║   ██║   ██╔══╝  ██║███╗██║██╔══██║  ╚██╔╝
██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗    ╚██████╔╝██║  ██║   ██║   ███████╗╚███╔███╔╝██║  ██║   ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝

"""  # noqa: W291


class CustomConfigParser(ConfigParser):
    def get(self, section, option, *args, **kwargs):
        if isinstance(option, list):
            fallback = None

            if "fallback" in kwargs: #override kwargs fallback, for manually handling here
                fallback = kwargs["fallback"]
                kwargs["fallback"] = None

            for name in option:
                try:
                    value = super().get(section, name, *args, **kwargs)
                except NoOptionError:
                    value = None

                if value:
                    break

            if not value:
                value = fallback

            if value is None:
                raise NoOptionError(option[0], section)
        else:
            value = super().get(section, option, *args, **kwargs)

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return value

        return value.strip() if value is not None else value

    def getint(self, section, option, *args, **kwargs): #bypass fallback bug
        value = self.get(section, option, *args, **kwargs)
        return int(value) if value is not None else None

    def getfloat(self, section, option, *args, **kwargs): #bypass fallback bug
        value = self.get(section, option, *args, **kwargs)
        return float(value) if value is not None else None


class SingleTransportGateway:
    """
    Gateway class for running a single transport in its own process
    """
    __log = None
    __running = False
    __transport = None
    config_file = ""
    __bridge_queue = None

    def __init__(self, config_file: str, transport_name: str, bridge_queue=None):
        self.config_file = config_file
        self.__bridge_queue = bridge_queue
        
        # Set up logging for this process
        self.__log = logging.getLogger(f"single_transport_{transport_name}")
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(asctime)s]  {%(filename)s:%(lineno)d}  %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.__log.addHandler(handler)
        self.__log.setLevel(logging.INFO)
        
        self.__log.info(f"Initializing single transport gateway for {transport_name}")
        
        # Load configuration
        self.__settings = CustomConfigParser()
        self.__settings.read(self.config_file)
        
        # Find and initialize the specific transport
        if transport_name in self.__settings.sections():
            transport_cfg = self.__settings[transport_name]
            transport_type = transport_cfg.get("transport", fallback="")
            protocol_version = transport_cfg.get("protocol_version", fallback="")

            if not transport_type and not protocol_version:
                raise ValueError("Missing Transport / Protocol Version")

            if not transport_type and protocol_version:
                protocolSettings = protocol_settings(protocol_version)
                if not transport_type and not protocolSettings.transport:
                    raise ValueError("Missing Transport")
                if not transport_type:
                    transport_type = protocolSettings.transport

            # Import the module
            module = importlib.import_module("classes.transports." + transport_type)
            # Get the class from the module
            cls = getattr(module, transport_type)
            self.__transport = cls(transport_cfg)
            
            self.__log.info(f"Created transport: {self.__transport.type}:{self.__transport.transport_name}")
            
            # Connect the transport
            self.__log.info(f"Connecting to {self.__transport.type}:{self.__transport.transport_name}...")
            self.__transport.connect()
            
        else:
            raise ValueError(f"Transport section '{transport_name}' not found in config")

    def handle_bridge_message(self, message):
        """
        Handle bridge messages from other transports
        """
        try:
            source_transport = message.get('source_transport')
            target_transport = message.get('target_transport')
            data = message.get('data')
            source_transport_info = message.get('source_transport_info', {})
            
            # Check if this transport is the target
            if target_transport == self.__transport.transport_name:
                self.__log.debug(f"Received bridge message from {source_transport} with {len(data)} items")
                
                # Forward the data to this transport
                if hasattr(self.__transport, 'write_data'):
                    # Create a mock transport object with the source transport info
                    class MockSourceTransport:
                        def __init__(self, info):
                            self.transport_name = info.get('transport_name', '')
                            self.device_identifier = info.get('device_identifier', '')
                            self.device_name = info.get('device_name', '')
                            self.device_manufacturer = info.get('device_manufacturer', '')
                            self.device_model = info.get('device_model', '')
                            self.device_serial_number = info.get('device_serial_number', '')
                            # Add protocolSettings attribute to avoid AttributeError
                            self.protocolSettings = None
                    
                    source_transport_obj = MockSourceTransport(source_transport_info)
                    
                    # Call write_data with the correct parameters
                    self.__transport.write_data(data, source_transport_obj)
                else:
                    self.__log.warning(f"Transport {self.__transport.transport_name} does not support write_data")
                    
        except Exception as err:
            self.__log.error(f"Error handling bridge message: {err}")
            traceback.print_exc()

    def run(self):
        """
        Run the single transport
        """
        self.__running = True
        self.__log.info(f"Starting single transport: {self.__transport.transport_name}")

        # Check if this is an output transport (no read_interval)
        is_output_transport = (self.__transport.read_interval <= 0)
        
        if is_output_transport:
            self.__log.info(f"Running output transport: {self.__transport.transport_name}")
            # For output transports, just handle bridge messages
            while self.__running:
                try:
                    # Check for bridge messages
                    if self.__bridge_queue:
                        try:
                            while not self.__bridge_queue.empty():
                                message = self.__bridge_queue.get_nowait()
                                self.handle_bridge_message(message)
                        except:
                            pass  # Queue is empty or other error
                    
                    time.sleep(0.1)  # Short sleep for output transports
                    
                except Exception as err:
                    self.__log.error(f"Error in output transport {self.__transport.transport_name}: {err}")
                    traceback.print_exc()
        else:
            # For input transports, handle both reading and bridging
            while self.__running:
                try:
                    # Check for bridge messages
                    if self.__bridge_queue:
                        try:
                            while not self.__bridge_queue.empty():
                                message = self.__bridge_queue.get_nowait()
                                self.handle_bridge_message(message)
                        except:
                            pass  # Queue is empty or other error

                    now = time.time()
                    if self.__transport.read_interval > 0 and now - self.__transport.last_read_time > self.__transport.read_interval:
                        self.__transport.last_read_time = now
                        
                        if not self.__transport.connected:
                            self.__transport.connect()
                        else:
                            info = self.__transport.read_data()
                            
                            if info:
                                self.__log.debug(f"Read data from {self.__transport.transport_name}: {len(info)} items")
                                
                                # Handle bridging if configured
                                if self.__transport.bridge and self.__bridge_queue:
                                    self.__log.debug(f"Sending bridge message from {self.__transport.transport_name} to {self.__transport.bridge}")
                                    bridge_message = {
                                        'source_transport': self.__transport.transport_name,
                                        'target_transport': self.__transport.bridge,
                                        'data': info,
                                        'source_transport_info': {
                                            'transport_name': self.__transport.transport_name,
                                            'device_identifier': getattr(self.__transport, 'device_identifier', ''),
                                            'device_name': getattr(self.__transport, 'device_name', ''),
                                            'device_manufacturer': getattr(self.__transport, 'device_manufacturer', ''),
                                            'device_model': getattr(self.__transport, 'device_model', ''),
                                            'device_serial_number': getattr(self.__transport, 'device_serial_number', '')
                                        }
                                    }
                                    self.__bridge_queue.put(bridge_message)
                            else:
                                self.__log.debug(f"No data read from {self.__transport.transport_name}")

                except Exception as err:
                    self.__log.error(f"Error in transport {self.__transport.transport_name}: {err}")
                    traceback.print_exc()

                time.sleep(0.7)


class Protocol_Gateway:
    """
    Main class, implementing the Growatt / Inverters to MQTT functionality
    """
    __log = None
    # log level, available log levels are CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
    __log_level = "DEBUG"

    __running : bool = False
    ''' controls main loop'''

    __transports : list[transport_base] = []
    ''' transport_base is for type hinting. this can be any transport'''

    config_file : str

    def __init__(self, config_file : str):
        self.__log = logging.getLogger("invertermodbustomqqt_log")
        handler = logging.StreamHandler(sys.stdout)
        #self.__log.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s]  {%(filename)s:%(lineno)d}  %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.__log.addHandler(handler)

        self.config_file = os.path.dirname(os.path.realpath(__file__)) + "/growatt2mqtt.cfg"
        newcfg = os.path.dirname(os.path.realpath(__file__)) + "/"+ config_file
        if os.path.isfile(newcfg):
            self.config_file = newcfg

        #logging.basicConfig()
        #pymodbus_log = logging.getLogger('pymodbus')
        #pymodbus_log.setLevel(logging.DEBUG)
        #pymodbus_log.addHandler(handler)

        self.__log.info("Loading...")

        self.__settings = CustomConfigParser()
        self.__settings.read(self.config_file)

        ##[general]
        self.__log_level = self.__settings.get("general","log_level", fallback="INFO")

        log_level = getattr(logging, self.__log_level, logging.INFO)
        self.__log.setLevel(log_level)
        logging.basicConfig(level=log_level)

        for section in self.__settings.sections():
            transport_cfg = self.__settings[section]
            transport_type      = transport_cfg.get("transport", fallback="")
            protocol_version    = transport_cfg.get("protocol_version", fallback="")

            # Process sections that either start with "transport" OR have a transport field
            if section.startswith("transport") or transport_type:
                if not transport_type and not protocol_version:
                    raise ValueError("Missing Transport / Protocol Version")

                if not transport_type and protocol_version: #get transport from protocol settings...  todo need to make a quick function instead of this

                    protocolSettings : protocol_settings = protocol_settings(protocol_version)

                    if not transport_type and not protocolSettings.transport:
                        raise ValueError("Missing Transport")

                    if not transport_type:
                        transport_type = protocolSettings.transport


                # Import the module
                module = importlib.import_module("classes.transports."+transport_type)
                # Get the class from the module
                cls = getattr(module, transport_type)
                transport : transport_base = cls(transport_cfg)

                transport.on_message = self.on_message
                self.__transports.append(transport)

        #connect first
        for transport in self.__transports:
            self.__log.info("Connecting to "+str(transport.type)+":" +str(transport.transport_name)+"...")
            transport.connect()

        time.sleep(0.7)
        #apply links
        for to_transport in self.__transports:
            for from_transport in self.__transports:
                if to_transport.bridge == from_transport.transport_name:
                    to_transport.init_bridge(from_transport)
                    from_transport.init_bridge(to_transport)


    def on_message(self, transport : transport_base, entry : registry_map_entry, data : str):
        ''' message recieved from a transport! '''
        for to_transport in self.__transports:
            if to_transport.transport_name != transport.transport_name:
                if to_transport.transport_name == transport.bridge or transport.transport_name == to_transport.bridge:
                    to_transport.write_data({entry.variable_name : data}, transport)
                    break

    def run_single_transport(self, transport_name: str, config_file: str, bridge_queue=None):
        """
        Run a single transport in its own process
        """
        try:
            # Create a new gateway instance for this transport
            single_gateway = SingleTransportGateway(config_file, transport_name, bridge_queue)
            single_gateway.run()
        except Exception as err:
            print(f"Error in transport {transport_name}: {err}")
            traceback.print_exc()

    def run(self):
        """
        run method, starts ModBus connection and mqtt connection
        """
        if len(self.__transports) <= 1:
            # Use single-threaded approach for 1 or fewer transports
            self.__run_single_threaded()
        else:
            # Use multiprocessing approach for multiple transports
            self.__run_multiprocess()

    def __run_single_threaded(self):
        """
        Original single-threaded implementation
        """
        self.__running = True

        if False:
            self.enable_write()

        while self.__running:
            try:
                now = time.time()
                for transport in self.__transports:
                    if transport.read_interval > 0 and now - transport.last_read_time  > transport.read_interval:
                        transport.last_read_time = now
                        #preform read
                        if not transport.connected:
                            transport.connect() #reconnect
                        else: #transport is connected

                            info = transport.read_data()

                            if not info:
                                continue

                            #todo. broadcast option
                            if transport.bridge:
                                for to_transport in self.__transports:
                                    if to_transport.transport_name == transport.bridge:
                                        to_transport.write_data(info, transport)
                                        break

            except Exception as err:
                traceback.print_exc()
                self.__log.error(err)

            time.sleep(0.7) #change this in future. probably reduce to allow faster reads.

    def __run_multiprocess(self):
        """
        Multiprocessing implementation for multiple transports
        """
        self.__log.info(f"Starting multiprocessing mode with {len(self.__transports)} transports")
        
        # Separate input and output transports
        input_transports = [t for t in self.__transports if t.read_interval > 0]
        output_transports = [t for t in self.__transports if t.read_interval <= 0]
        
        self.__log.info(f"Input transports: {len(input_transports)}, Output transports: {len(output_transports)}")
        
        # Check for bridging configuration
        has_bridging = any(transport.bridge for transport in self.__transports)
        if has_bridging:
            self.__log.info("Bridging detected - enabling inter-process communication")
        else:
            self.__log.info("No bridging configured - transports will run independently")
        
        # Create a shared queue for inter-process communication
        bridge_queue = multiprocessing.Queue() if has_bridging else None
        
        # Create processes for each transport
        processes = []
        for transport in self.__transports:
            process = multiprocessing.Process(
                target=self.run_single_transport,
                args=(transport.transport_name, self.config_file, bridge_queue),
                name=f"transport_{transport.transport_name}"
            )
            process.start()
            processes.append(process)
            self.__log.info(f"Started process for {transport.transport_name} (PID: {process.pid})")
        
        # Monitor processes
        try:
            while True:
                # Check if any process has died
                for i, process in enumerate(processes):
                    if not process.is_alive():
                        transport_name = self.__transports[i].transport_name
                        self.__log.warning(f"Process for {transport_name} died, restarting...")
                        
                        # Restart the process
                        new_process = multiprocessing.Process(
                            target=self.run_single_transport,
                            args=(transport_name, self.config_file, bridge_queue),
                            name=f"transport_{transport_name}"
                        )
                        new_process.start()
                        processes[i] = new_process
                        self.__log.info(f"Restarted process for {transport_name} (PID: {new_process.pid})")
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            self.__log.info("Shutting down multiprocessing mode...")
            for process in processes:
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
            self.__log.info("All processes terminated")






def main():
    """
    main method
    """
    print(__logo)

    ppg = Protocol_Gateway(args.config)
    ppg.run()


if __name__ == "__main__":
    # Create ArgumentParser object
    parser = argparse.ArgumentParser(description="Python Protocol Gateway")

    # Add arguments
    parser.add_argument("--config", "-c", type=str, help="Specify Config File")

    # Add a positional argument with default
    parser.add_argument("positional_config", type=str, help="Specify Config File", nargs="?", default="config.cfg")

    # Parse arguments
    args = parser.parse_args()

    # If '--config' is provided, use it; otherwise, fall back to the positional or default.
    args.config = args.config if args.config else args.positional_config

    main()
