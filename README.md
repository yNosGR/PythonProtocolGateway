# growatt2mqtt

Growatt2MQTT is a small python-based service which connects via usb to the Modbus interface of Growatt inverters and published the collected data on MQTT.
The python service can be configured via a small config file.

The config file is structured as follows:

### Config file (growatt2mqtt.cfg)
[query] -- all values in seconds  
interval = 10  
offline_interval = 60  
error_interval = 60

[solarmon]  
port = /dev/ttyACM0  
baudrate = 9600  

[inverters.main]  
unit = 1  
measurement = inverter  

[mqtt]  
host = YOUR MQTT BROKER IP  
port = 1883  
topic = inverter/growatt/MIC-600TL-X  
error_topic = inverter/growatt/MIC-600TL-X/error  

### Supported Inverters  
- Growatt MIC-600TL-X  
- more to come ...  

### Install growatt2mqtt service
- ```cp growatt2mqtt.service file to /etc/systemc/system/```
- ```sudo systemctl daemon-reload```
- ```sudo systemctl enable growatt2mqtt.service```
- ```sudo systemctl start growatt2mqtt.service```
- ```systemctl status growatt2mqtt.service```
