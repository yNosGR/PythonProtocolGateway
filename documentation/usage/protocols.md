## Overriding protocols
Protocols CSVs can be overriden, so that specific entries can be modified. 
Protocols CSV overrides can be created naming them with name.override.csv

For example, creating a file called: v0.14.input_registry_map.override.csv
will allow the v0.14 protocol to be modified while preseving the main csv. 

"documented name" is used as the primary key. the "register" is a secondary key. 

only non-empty values will overwrite; not all columns need to be specified. 

| documented name  | data type |
| ------------- | ------------- |
| product id  | ASCII  |

if both the "documented name" and "register" are unqiue, the row will be treated as a new entry. 

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
[creating_and_editing_protocols.md](creating_and_editing_protocols.md) - Creating and editing protocolss

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
