#!/usr/bin/env python3
import time
import os
import json

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 

from configparser import RawConfigParser
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from growatt import Growatt

# Global variables, defined private, all variables will be configured via cfg file
__settings = None               # settings --> from config file
__interval = None               # interval in seconds for pulling modbus data [s]
__offline_interval = None       # in case inverter is offline the script will sleep that defined time [s]
__error_interval = None         # error interval in [s]
__port = None                   # device name of serial usb connection [/dev/tty...]
__baudrate = -1                 # baudrate to access modbus connection
__client = None                 # modbus client handle
__mqtt_host = None              # mqtt server host address
__mqtt_client = None            # mqtt client handle
__mqtt_port = -1                # mqtt port
__mqtt_topic = ""               # mqtt topic the inverter data will be published
__properties = None             # mqtt properties handle for publishing data


def init():
    print("Initialize growatt2mqtt")
    __settings = RawConfigParser()
    __settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')
    __interval = __settings.getint('query', 'interval', fallback=1)
    __offline_interval = __settings.getint('query', 'offline_interval', fallback=60)
    __error_interval = __settings.getint('query', 'error_interval', fallback=60)

    print('Setup Serial Connection... ', end='')
    __port = __settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
    __baudrate = __settings.get('solarmon', 'baudrate', fallback=9600)
    __client = ModbusClient(method='rtu', port=__port, baudrate=int(__baudrate), stopbits=1, parity='N', bytesize=8, timeout=1)
    __client.connect()
    print('Serial connection established...')

    print("start connection mqtt ...")
    __mqtt_host = __settings.get('mqtt', 'host', fallback='mqtt.eclipseprojects.io')
    __mqtt_port = __settings.get('mqtt', 'port', fallback=1883)
    __mqtt_topic = __settings.get('mqtt', 'topic', fallback='home/inverter')
    print("mqtt settings: ")
    print("mqtt host "+__mqtt_host)
    print("mqtt port "+__mqtt_port)
    print("mqtt_topic "+__mqtt_topic)
    __mqtt_client = mqtt.Client()
    __mqtt_client.on_connect = on_connect
    __mqtt_client.on_message = on_message

    __mqtt_client.connect(str(__mqtt_host),int(__mqtt_port),60)
    __mqtt_client.loop_start()

    __properties=Properties(PacketTypes.PUBLISH)
    __properties.MessageExpiryInterval=30 # in seconds

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


def run():
    print('Loading inverters... ')
    inverters = []
    for section in __settings.sections():
        if not section.startswith('inverters.'):
            continue

        name = section[10:]
        unit = int(__settings.get(section, 'unit'))
        measurement = __settings.get(section, 'measurement')
        growatt = Growatt(__client, name, unit)
        growatt.print_info()
        inverters.append({
            'error_sleep': 0,
            'growatt': growatt,
            'measurement': measurement
        })
    print('Done!')

    while True:
        online = False
        for inverter in inverters:
            # If this inverter errored then we wait a bit before trying again
            if inverter['error_sleep'] > 0:
                inverter['error_sleep'] -= __interval
                continue

            growatt = inverter['growatt']
            try:
                now = time.time()
                info = growatt.read()

                if info is None:
                    continue

                # Mark that at least one inverter is online so we should continue collecting data
                online = True

                points = [{
                    'time': int(now),
                    'measurement': inverter['measurement'],
                    "fields": info
                }]
                print(points)
                # Serializing json  
                json_object = json.dumps(points[0], indent = 4)
        
                __mqtt_client.publish(__mqtt_topic,json_object,0,properties=__properties)

            except Exception as err:
                print(growatt.name)
                print(err)
                inverter['error_sleep'] = __error_interval

        if online:
            time.sleep(__interval)
        else:
            # If all the inverters are not online because no power is being generated then we sleep for 1 min
            time.sleep(__offline_interval)

def main():
    print("Start growatt2mqtt")
    init()
    run()

if __name__ == "__main__":
    main()