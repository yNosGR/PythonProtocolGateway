# SOK to MQTT

```
transport=modbus_rtu
protocol_version=pace_bms_v1.3
```
The Battery's RS485 Protocol must be set to: `PACE_MODBUS` 

Plugs into the RS485A port

This protocol is only able to read the battery that is directly connected to it; a modbus hub can be used to help fix this limitation. 

SOK, jakiper 48v100AH battery and other PACE BMS batteries.

![pace-bms](https://github.com/HotNoob/InverterModBusToMQTT/assets/2180145/1ea28956-5d74-4bdb-9732-341d492d15c3)

### rs485a pinout ### 
Pin 1,2,3 or Pin 8,7,6