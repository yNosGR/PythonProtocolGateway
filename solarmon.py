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

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)

print('Setup Serial Connection... ', end='')
port = settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
print('Dome!')

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

print("start connection mqtt ...")
mqtt_host = settings.get('mqtt', 'host', fallback='mqtt.eclipseprojects.io')
mqtt_port = settings.get('mqtt', 'port', fallback=1883)
mqtt_topic = settings.get('mqtt', 'topic', fallback='home/inverter')
print("mqtt settings: ")
print("mqtt host "+mqtt_host)
print("mqtt port "+mqtt_port)
print("mqtt_topic "+mqtt_topic)
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(str(mqtt_host),int(mqtt_port),60)
mqtt_client.loop_start()

properties=Properties(PacketTypes.PUBLISH)
properties.MessageExpiryInterval=30 # in seconds

print('Loading inverters... ')
inverters = []
for section in settings.sections():
    if not section.startswith('inverters.'):
        continue

    name = section[10:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    growatt = Growatt(client, name, unit)
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
            inverter['error_sleep'] -= interval
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

            print(growatt.name)
            print(points)
            # Serializing json  
            json_object = json.dumps(points[0], indent = 4)
    
            mqtt_client.publish(mqtt_topic,json_object,0,properties=properties)

        except Exception as err:
            print(growatt.name)
            print(err)
            inverter['error_sleep'] = error_interval

    if online:
        time.sleep(interval)
    else:
        # If all the inverters are not online because no power is being generated then we sleep for 1 min
        time.sleep(offline_interval)
