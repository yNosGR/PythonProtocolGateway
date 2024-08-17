## Custom / Editing Protocols
Custom protocols can be created by naming them with name.custom. this will ensure that they do not get overwritten when updating. 

for example, say that you want to modify the eg4_v58 protocol without having to worry about updates overwritting it: 

```
copy eg4_v58.json eg4_v58.custom.json
copy eg4_v58.input_registry_map.csv eg4_v58.input_registry_map.custom.csv
copy eg4_v58.holding_registry_map.csv eg4_v58.holding_registry_map.custom.csv
```

in the configuration for your transport:
```
protocol_version = eg4_v58.custom
```

## Protocol Configuration - CSV / JSON
{protocol_name}.json contains default settings, releated to the transport.
{protocol_name}.{registry_type}_registry_map.csv contains configuration for specific registry "type".
{protocol_name}.registry_map.csv contains configuration for generic "registers". 
 
### csv format:
https://github.com/HotNoob/PythonProtocolGateway/wiki/Creating-and-Editing-Protocols-%E2%80%90-JSON-%E2%80%90-CSV#csv

## egv_v58
```
protocol_version = eg4_v58
```
[Devices\EG4 to MQTT](https://github.com/HotNoob/PythonProtocolGateway/wiki/Devices%5CEG4-to-MQTT)

## v0.14
```
protocol_version = v0.14
```
[Devices\Growatt To MQTT](https://github.com/HotNoob/PythonProtocolGateway/wiki/Devices%5CGrowatt-To-MQTT)

## sigineer_v0.11

```
protocol_version = sigineer_v0.11
```
[Devices\Sigineer to MQTT](https://github.com/HotNoob/PythonProtocolGateway/wiki/Devices%5CSigineer-to-MQTT)

## pace_bms_v1.3
```
protocol_version = pace_bms_v1.3
```
[Devices\SOK to MQTT](https://github.com/HotNoob/PythonProtocolGateway/wiki/Devices%5CSOK-to-MQTT)