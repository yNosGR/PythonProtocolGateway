#!/usr/bin/env python3
"""
Main module for Growatt / Inverters ModBus RTU data to MQTT
"""
import atexit
import glob
import time
import os
import json
import logging
import sys
import traceback
from configparser import RawConfigParser
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from inverter import Inverter

from protocol_settings import protocol_settings

__logo = """
   ____                        _   _   ____  __  __  ___ _____ _____ 
  / ___|_ __ _____      ____ _| |_| |_|___ \|  \/  |/ _ \_   _|_   _|
 | |  _| '__/ _ \ \ /\ / / _` | __| __| __) | |\/| | | | || |   | |  
 | |_| | | | (_) \ V  V / (_| | |_| |_ / __/| |  | | |_| || |   | |  
  \____|_|  \___/ \_/\_/ \__,_|\__|\__|_____|_|  |_|\__\_\|_|   |_|  
                                                                      
    """


class InverterModBusToMQTT:
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
    # device name of serial usb connection [/dev/tty...]
    __port = None
    # baudrate to access modbus connection
    __baudrate = -1
    # modbus client handle
    __client = None
    # mqtt server host address
    __mqtt_host = None
    # mqtt client handle
    __mqtt_client = None

    # mqtt port of mqtt broker
    __mqtt_port = -1
    # mqtt topic the inverter data will be published
    __mqtt_topic = ""
    
    __mqtt_discovery_topic : str = "homeassistant"

    __mqtt_discovery_enabled : bool = True

    __mqtt_json : bool = False

    __mqtt_reconnect_delay : int = 7

    
    __mqtt_reconnect_attempts : int = 21
    ''' max number of reconnects during a disconnect '''

    # mqtt error topic in case the growatt2mqtt runs in error moder or inverter is powered off
    __mqtt_error_topic = ""
    # mqtt properties handle for publishing data
    __properties = None
    # logging module
    __log = None
    # log level, available log levels are CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG
    __log_level = 'DEBUG'

    __device_serial_number = "hotnoob"

    __max_precision : int = -1

    __analyze_protocol : bool = False
    ''' enable / disable analyze mode'''
    
    inverter : Inverter
    measurement : str

    def __init__(self):
        self.__log = logging.getLogger('invertermodbustomqqt_log')
        handler = logging.StreamHandler(sys.stdout)
        self.__log.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s]  {%(filename)s:%(lineno)d}  %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.__log.addHandler(handler)
        return None

    def init_invertermodbustomqtt(self):
        """
        initialize
        """
        self.__log.info("Initialize Inverter ModBus To MQTT Server")
        self.__settings = RawConfigParser()

        cfg = os.path.dirname(os.path.realpath(__file__)) + '/growatt2mqtt.cfg'
        newcfg = os.path.dirname(os.path.realpath(__file__)) + '/config.cfg'
        if os.path.isfile(newcfg):
            cfg = newcfg

        self.__settings.read(cfg)
        self.__interval = self.__settings.getint(
            'time', 'interval', fallback=1)
        self.__offline_interval = self.__settings.getint(
            'time', 'offline_interval', fallback=60)
        self.__error_interval = self.__settings.getint(
            'time', 'error_interval', fallback=60)
        
        self.__log_level = self.__settings.get('general','log_level', fallback='DEBUG')
        self.__max_precision = self.__settings.getint('general','max_precision', fallback=-1)

        if (self.__log_level != 'DEBUG'):
            self.__log.setLevel(logging.getLevelName(self.__log_level))
        self.__log.info('Setup Serial Connection... ')
        self.__port = self.__settings.get(
            'serial', 'port', fallback='/dev/ttyUSB0')
        self.__baudrate = self.__settings.get(
            'serial', 'baudrate', fallback=9600)
        self.__client = ModbusClient(method='rtu', port=self.__port, baudrate=int(
            self.__baudrate), stopbits=1, parity='N', bytesize=8, timeout=1)
        self.__client.connect()
        self.__log.info('Serial connection established...')

        self.__log.info("start connection mqtt ...")
        self.__mqtt_host = self.__settings.get(
            'mqtt', 'host', fallback='mqtt.eclipseprojects.io')
        
        self.__mqtt_port = self.__settings.get('mqtt', 'port', fallback=1883)
        self.__mqtt_topic = self.__settings.get('mqtt', 'topic', fallback='home/inverter')
        self.__mqtt_discovery_topic = self.__settings.get('mqtt', 'discovery_topic', fallback='homeassistant')
        self.__mqtt_discovery_enabled = strtobool(self.__settings.get('mqtt', 'discovery_enabled', fallback="true"))
        self.__mqtt_json = strtobool(self.__settings.get('mqtt', 'json', fallback="false"))
        self.__mqtt_reconnect_delay = self.__settings.getint('mqtt', 'reconnect_delay', fallback=7)
        if not isinstance( self.__mqtt_reconnect_delay , int) or self.__mqtt_reconnect_delay < 1: #minumum 1 second
            self.__mqtt_reconnect_delay = 1


        self.__mqtt_reconnect_attempts = self.__settings.getint('mqtt', 'reconnect_attempts', fallback=21)
        if not isinstance( self.__mqtt_reconnect_attempts , int) or self.__mqtt_reconnect_attempts < 0: #minimum 0
            self.__mqtt_reconnect_attempts = 0


        #this is kinda dumb, overcomplicates things, let's stick to 1 inverter at a time, can always run multiple instances of script
        #keep this loop for backwards compatability
        for section in self.__settings.sections():
            if not section.startswith('inverter'):
                continue

            name = self.__settings.get(section, 'name', fallback="NO NAME")
            unit = int(self.__settings.get(section, 'unit'))
            protocol_version = str(self.__settings.get(section, 'protocol_version'))
            self.__analyze_protocol = self.__settings.getboolean(section, 'analyze_protocol', fallback=False)
            self.measurement = self.__settings.get(section, 'measurement')
            self.inverter = Inverter(self.__client, name, unit, protocol_version, self.__max_precision, self.__log)
            self.inverter.print_info()

        

        self.__mqtt_error_topic = self.__settings.get(
            'mqtt', 'error_topic', fallback='home/inverter/error')
        self.__log.info("mqtt settings: \n")
        self.__log.info("mqtt host %s\n", self.__mqtt_host)
        self.__log.info("mqtt port %s\n", self.__mqtt_port)
        self.__log.info("mqtt_topic %s\n", self.__mqtt_topic)
        self.__mqtt_client = mqtt.Client()
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message
        self.__mqtt_client.on_disconnect = self.on_disconnect
        

        ## Set username and password
        username = self.__settings.get('mqtt', 'user')
        password = self.__settings.get('mqtt', 'pass')
        if username:
            self.__mqtt_client.username_pw_set(username=username, password=password)

        self.__mqtt_client.connect(str(self.__mqtt_host), int(self.__mqtt_port), 60)
        self.__mqtt_client.loop_start()

        self.__properties = Properties(PacketTypes.PUBLISH)
        self.__properties.MessageExpiryInterval = 30  # in seconds

        atexit.register(self.exit_handler)

    def exit_handler(self):
        '''on exit handler'''
        print("Exiting")
        self.__mqtt_client.publish( self.__mqtt_topic + "/availability","offline")
        return


    def on_disconnect(self, client, userdata, rc):
        self.__log.info("Disconnected from MQTT Broker!")
        # Attempt to reconnect
        for attempt in range(0, self.__mqtt_reconnect_attempts):
            try:
                self.__log.warning("Attempting to reconnect("+str(attempt)+")...")
                self.__mqtt_client.reconnect()
                #self.__mqtt_client.loop_stop()
                #self.__mqtt_client.connect(str(self.__mqtt_host), int(self.__mqtt_port), 60)
                #self.__mqtt_client.loop_start()
                return
            except:
                self.__log.warning("Reconnection failed. Retrying in "+str(self.__mqtt_reconnect_delay)+" second(s)...")
                time.sleep(self.__mqtt_reconnect_delay)
        
        #failed to reonnect
        self.__log.critical("Failed to Reconnect, Too many attempts")
        exit() #exit, service should restart entire script

    def on_connect(self, client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server. """
        self.__log.info("Connected with result code %s\n",str(rc))


    def on_message(self, client, userdata, msg):
        """ The callback for when a PUBLISH message is received from the server. """
        self.__log.info(msg.topic+" "+str(msg.payload))

    def run(self):
        """
        run method, starts ModBus connection and mqtt connection
        """

        if self.__analyze_protocol:
            self.analyze_protocol()
            quit()


        self.__device_serial_number = self.__settings.get('mqtt_device', 'serial_number', fallback='')

        if not self.__device_serial_number: #if empty, fetch serial
            self.__device_serial_number = self.inverter.read_serial_number()

        if self.__mqtt_discovery_enabled:
            self.mqtt_discovery()

        error_sleep = 0
        while True:
            if not self.__mqtt_client.is_connected(): ##mqtt not connected. 
                print('MQTT is not connected')
                time.sleep(self.__mqtt_reconnect_delay)
                continue



            online = False
            # If this inverter errored then we wait a bit before trying again
            if error_sleep > 0:
                error_sleep -= self.__interval
                continue

            try:
                
                info = self.inverter.read_input_register()

                if info is None:
                    self.__log.info("Register is None; modbus busy?")
                    continue

                # Mark that at least one inverter is online so we should continue collecting data
                online = True
                now = time.time()
                points = [{
                    'time': int(now),
                    'measurement': self.measurement,
                    "fields": info
                }]
                self.__log.info(points)

                #have to send this every loop, because mqtt doesnt disconnect when HA restarts. HA bug. 
                self.__mqtt_client.publish(self.__mqtt_topic + "/availability","online", qos=0,retain=True)

                if(self.__mqtt_json):
                    # Serializing json
                    json_object = json.dumps(points[0], indent=4)
                    self.__mqtt_client.publish(self.__mqtt_topic, json_object, 0, properties=self.__properties)
                else:
                    for key, val in info.items():
                        self.__mqtt_client.publish(str(self.__mqtt_topic+'/'+key).lower(), str(val))

            except Exception as err:
                traceback.print_exc()
                self.__log.error(self.inverter.name)
                self.__log.error(err)
                json_object = '{"name":' + str(self.inverter.name)+',error_code:'+str(err)+'}'
                self.__mqtt_client.publish(self.__mqtt_error_topic, json_object, 0, properties=self.__properties)
                error_sleep = self.__error_interval

            if online:
                time.sleep(self.__interval)
            else:
                # If all the inverters are not online because no power is being generated then we sleep for 1 min
                time.sleep(self.__offline_interval)

    def analyze_protocol(self, settings_dir : str = 'protocols'):
        print("=== PROTOCOL ANALYZER ===")
        protocol_names : list[str] = []
        protocols : dict[str,protocol_settings] = {}

        for file in glob.glob(settings_dir + "/*.json"):
            file = file.lower().replace(settings_dir, '').replace('/', '').replace('\\', '').replace('\\', '').replace('.json', '')
            print(file)
            protocol_names.append(file)

        max_input_register : int = 0
        max_holding_register : int = 0

        for name in protocol_names:
            protocols[name] = protocol_settings(name)

            if protocols[name].input_registry_size > max_input_register:
                max_input_register = protocols[name].input_registry_size

            if protocols[name].input_registry_size > max_holding_register:
                max_holding_register = protocols[name].holding_registry_size

        print("max input register: ", max_input_register)
        print("max holding register: ", max_holding_register)

        self.inverter.modbus_delay = self.inverter.modbus_delay * 2 #increase delay because were doing some heavy reads
        print("read INPUT Registers: ")
        ##batch_size = 1, read registers one by one; if out of bound. it just returns error
        input_register = self.inverter.read_registers(min=0, max=max_input_register, batch_size=1)
        holding_register = self.inverter.read_registers(min=0, max=max_holding_register, batch_size=1, register_type="holding")

        #print results for debug
        print("=== START INPUT REGISTER ===")
        print([(key, value) for key, value in input_register.items()])
        print("=== END INPUT REGISTER ===")
        print("=== START HOLDING REGISTER ===")
        print([(key, value) for key, value in holding_register.items()])
        print("=== END HOLDING REGISTER ===")

        #very well possible the registers will be incomplete due to different hardware sizes
        #so dont assume they are set / complete
        #we'll see about the behaviour. if it glitches, this could be a way to determine protocol.

        input_register_score : dict[str, int] = {}
        holding_register_score : dict[str, int] = {}

        for name, protocol in protocols.items():
            input_register_score[name] = 0
            holding_register_score[name] = 0

            for entry in protocol.input_registry_map:
                if entry.register in input_register and input_register[entry.register] > 0: #empty registers appear as 0; so if it is being used it is likely above 0. if the normal state is zero it wont be detected
                    input_register_score[name] = input_register_score[name] + 1

            for entry in protocol.holding_registry_map:
                if entry.register in holding_register and holding_register[entry.register] > 0:
                    holding_register_score[name] = holding_register_score[name] + 1

        
        protocol_scores: dict[str, int] = {}
        #combine scores
        for name, protocol in protocols.items():
            protocol_scores[name] = input_register_score[name] + holding_register_score[name]

        #print scores
        for name in sorted(protocol_scores, key=protocol_scores.get, reverse=True):
            print("=== "+str(name)+" - "+str(protocol_scores[name])+" ===")
            print("input register : " + str(input_register_score[name]) + " of " + str(len(protocols[name].input_registry_map)))
            print("holding register : " + str(holding_register_score[name]) + " of " + str(len(protocols[name].holding_registry_map)))
        
                    
                    
    def mqtt_discovery(self):
        print("Publishing HA Discovery Topics...")

        disc_payload = {}
        disc_payload['availability_topic'] = self.__mqtt_topic + "/availability"

        device = {}
        device['manufacturer'] = self.__settings.get('mqtt_device', 'manufacturer', fallback='HotNoob')
        device['model'] = self.__settings.get('mqtt_device', 'model', fallback='HotNoob Was Here 2024')
        device['identifiers'] = "hotnoob_" + self.__device_serial_number
        device['name'] = self.__settings.get('mqtt_device', 'device_name', fallback='Solar Inverter')

        length = len(self.inverter.protocolSettings.input_registry_map)
        count = 0
        for item in self.inverter.protocolSettings.input_registry_map:
            count = count + 1
            print('Publishing Topic '+str(count)+' of ' + str(length), end='\r', flush=True)


            clean_name = item.variable_name.lower().replace(' ', '_')
            #device['sw_version'] = bms_version
            disc_payload = {}
            disc_payload['availability_topic'] = self.__mqtt_topic + "/availability"
            disc_payload['device'] = device
            disc_payload['name'] = clean_name
            disc_payload['unique_id'] = "hotnoob_" + self.__device_serial_number + "_"+clean_name
            disc_payload['state_topic'] = self.__mqtt_topic + "/"+clean_name
            
            if item.unit:
                disc_payload['unit_of_measurement'] = item.unit


            discovery_topic = self.__mqtt_discovery_topic+"/sensor/inverter-" + self.__device_serial_number  + "/" + disc_payload['name'].replace(' ', '_') + "/config"
            
            self.__mqtt_client.publish(discovery_topic,
                                       json.dumps(disc_payload),qos=0, retain=True)
        
        self.__mqtt_client.publish(disc_payload['availability_topic'],"online",qos=0, retain=True)
        print()
        self.__log.info("Published HA Discovery Topics")


def strtobool (val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    
    return 0

def main():
    """
    main method
    """
    print(__logo)
    inverter2mqtt = InverterModBusToMQTT()
    inverter2mqtt.init_invertermodbustomqtt()
    inverter2mqtt.run()


if __name__ == "__main__":
    main()
