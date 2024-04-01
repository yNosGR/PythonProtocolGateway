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

import atexit
import glob
import random
import re

import os
import json
import logging
import sys
import traceback
from configparser import RawConfigParser, ConfigParser
import paho.mqtt.client as mqtt


from classes.protocol_settings import protocol_settings,Data_Type,registry_map_entry,Registry_Type,WriteMode
from classes.transports.transport_base import transport_base




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
                                                                                                                                     
"""


class Protocol_Gateway:
    """
    Main class, implementing the Growatt / Inverters to MQTT functionality
    """
    # Global variables, defined private, all variables will be configured via cfg file
    # settings --> from config file
    __settings = None
    # interval in seconds for pulling modbus data [s]
    __interval = None
    # in case inverter is offline the script will sleep that defined time [s]
    __offline_interval = None
    # error interval in [s]
    __error_interval = None

    __log = None
    # log level, available log levels are CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
    __log_level = 'DEBUG'

    __device_serial_number = "hotnoob"

    __running : bool = False
    ''' controls main loop'''

    __transports : list[transport_base] = []
    ''' transport_base is for type hinting. this can be any transport'''

    config_file : str

    def __init__(self, config_file : str):
        self.__log = logging.getLogger('invertermodbustomqqt_log')
        handler = logging.StreamHandler(sys.stdout)
        self.__log.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s]  {%(filename)s:%(lineno)d}  %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.__log.addHandler(handler)

        self.config_file = os.path.dirname(os.path.realpath(__file__)) + '/growatt2mqtt.cfg'
        newcfg = os.path.dirname(os.path.realpath(__file__)) + '/'+ config_file
        if os.path.isfile(newcfg):
            self.config_file = newcfg

        #logging.basicConfig()
        #pymodbus_log = logging.getLogger('pymodbus')
        #pymodbus_log.setLevel(logging.DEBUG)
        #pymodbus_log.addHandler(handler)

        self.__log.info("Loading...")

        self.__settings = ConfigParser()
        self.__settings.read(self.config_file)

        ##[general]
        self.__log_level = self.__settings.get('general','log_level', fallback='DEBUG')
        if (self.__log_level != 'DEBUG'):
            self.__log.setLevel(logging.getLevelName(self.__log_level))

        for section in self.__settings.sections():
            if section.startswith('transport'):
                transport_cfg = self.__settings[section]
                transport_type      = transport_cfg.get('transport', fallback="")
                protocol_version    = transport_cfg.get('protocol_version', fallback="")

                if not transport_type and not protocol_version:
                    raise ValueError('Missing Transport / Protocol Version')
                
            
                if not transport_type and protocol_version: #get transport from protocol settings... 
                    protocolSettings : protocol_settings = protocol_settings(protocol_version)

                    if not transport_type and not protocolSettings.transport:
                        raise ValueError('Missing Transport')
                    
                    if not transport_type:
                        transport_type = protocolSettings.transport


                # Import the module
                module = importlib.import_module('classes.transports.'+transport_type)
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



        atexit.register(self.exit_handler)

    def exit_handler(self):
        '''on exit handler'''
        print("Exiting")
        self.__mqtt_client.publish( self.__mqtt_topic + "/availability","offline")
        return

    def on_message(self, transport : transport_base, registry_map_entry : registry_map_entry, data : str):
        ''' message recieved from a transport! '''
    

    def run(self):
        """
        run method, starts ModBus connection and mqtt connection
        """

        self.__running = True

        if False:
            self.analyze_protocol()
            quit()



        if False: #this needs to be implemented in transport init
            if not self.__device_serial_number: #if empty, fetch serial
                self.__device_serial_number = self.read_serial_number()
                        
            print("using serial number: " + self.__device_serial_number)

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
                                        to_transport.write_data(info)
                                        break
              
            except Exception as err:
                traceback.print_exc()
                self.__log.error(err)

            time.sleep(7)

   




def main():
    """
    main method
    """
    print(__logo)

    ppg = Protocol_Gateway(args.config)
    ppg.run()


if __name__ == "__main__":
    # Create ArgumentParser object
    parser = argparse.ArgumentParser(description='Python Protocol Gateway')

    # Add arguments
    parser.add_argument('--config', '-c', type=str, help='Specify Config File', default='config.cfg')
    # Parse arguments
    args = parser.parse_args()

    main()
