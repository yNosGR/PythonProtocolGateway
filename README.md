Originally from andiburger/growatt2mqtt, heavily modified to easily work with new and multiple protocols, configurable protocols, and added propper mqtt discovery / functionality to work with home assistant

### Rebranding to InverterModBusToMQTT
Sorry, better now than later. 
if you installed this when it was called growatt2mqtt-hotnoob, you'll need to reinstall if you want to update. 

# InverterModBusToMQTT

InverterModBusToMQTT is a small python-based service which connects via usb to the Modbus Over Serial interface of your solar inverters and published the collected data on MQTT.
The python service can be configured via a small config file.

with the addition of other brands, this will need to be renamed eventually to something... maybe ModBusInverterToMQTT


# Installation
Connect the USB-B port on the inverter into your computer / device
When connected, the device will show up as a serial port. 

### install requirements
```
apt install pip python3 -y
pip install -r requirements.txt
```

### Config file (config.cfg) - rename .example.cfg to .cfg
Edit configuration.
```
cp config.example.cfg  config.cfg
nano config.cfg
```

### inverters / protocols
manually select protocol in .cfg
protocol_version = {{version}}
```
v0.14 = growatt inverters 2020+
growatt_2020_v1.24 = alt protocol for growatt inverters 2020+ - currently untested
sigineer_v0.11 = sigineer inverters - currently untested
eg4_v58 = eg4 inverters - comming soon
```

### protocol analyzer
this is a new feature, currently in the making. probably needs some fine tuning, but is usable. 
update the configuration:
```
[inverter]
analyze_protocol = true
```

![Results Example](https://raw.githubusercontent.com/HotNoob/InverterModBusToMQTT/main/images/protocol_analyzer_results.jpg)

when this mode runs, it will read the registers of your inverter and attempt to determine which protocol best fits. 
the higher the value, the more likely that the protocol matches. the results above suggests that "growatt_2020_v1.24" is the most likely protocol for the inverter

### run as script
```python3 -u invertermodbustomqtt.py```


### install as service
```
cp invertermodbustomqtt.example.service  /etc/systemd/system/invertermodbustomqtt.service
nano /etc/systemd/system/invertermodbustomqtt.service
```
edit working directory in service file to wherever you put the files
```
nano /etc/systemd/system/invertermodbustomqtt.service
```
reload daemon, enable and start service
```
sudo systemctl daemon-reload
sudo systemctl enable invertermodbustomqtt.service
sudo systemctl start invertermodbustomqtt.service
systemctl status invertermodbustomqtt.service
```

### install mqtt on home assistant
![HA Demo](https://raw.githubusercontent.com/HotNoob/InverterModBusToMQTT/main/images/home%20assistant%20example2.png)

```Settings -> Add-Ons -> Add-On Store -> Mosquitto broker```

setup Mosquitto broker

```Settings -> People -> Users -> Add User -> Can only log in from the local network -> Fill Details ```

once installed; the device should show up on home assistant under mqtt

```Settings -> Devices & Services -> MQTT ```

more docs on setting up mqtt here: https://www.home-assistant.io/integrations/mqtt
i probably might have missed something. ha is new to me.

### update procedure
update files and restart script / service
```
git pull
systemctl restart invertermodbustomqtt.service
```

**if you installed this when it was called growatt2mqtt-hotnoob, you'll need to reinstall if you want to update. **


### Unknown Status MQTT Home Assistant 
If all values appear as "Unknown"
This is a bug with home assistant's discovery that some times happens when adding for the first time. just restart the service / script and it will fix itself. 

### variable names
variable names have been modified for greater readability. if it's confusing you can change them via protocols/{version}_input_registry_map.csv
you can also find the original documented variable names there; to use the original names, empty the variable name column
the csvs are using ";" as the delimeter, because that is what open office uses. 

### variable_mask.txt
if you want to only send/get specific variables, put them in this file. one variable per line. if list is empty all variables will be sent
```
variable1
variable2
```

### donate
this took me a while to make; and i had to make it because there werent any working solutions. 
donations would be appreciated.
![BitCoin Donation](https://github.com/HotNoob/growatt2mqtt-hotnoob/blob/main/images/donate_to_hotnoob.png?raw=true)

```(btc) bc1qh394vazcguedkw2rlklnuhapdq7qgpnnz9c3t0```

### Use Docker - untested
- ```docker build -t invertermodbustomqtt ```
- ```docker run --device=/dev/ttyUSB0 invertermodbustomqtt```
