# EG4 to MQTT

## Hardware
1. USB to RS485 Adapter (RJ45) from EG4 **or** USB to RS485 Adapter & RJ45 Ethernet cable ( or 3 wires ) 
2. Connect RJ45 ethernet cable to an avaiable RS485/Modbus port:

![image](https://github.com/HotNoob/PythonProtocolGateway/assets/2180145/c387d8af-5864-4795-9958-3161d23501f1)

<details>
  <summary>Example Image</summary>
  
![327825986-94315fea-abad-4c9c-942d-aa5ad4b47802](https://github.com/HotNoob/PythonProtocolGateway/assets/2180145/f8bee2f2-4f7c-4fd8-a437-2f03af1ba2b0)

</details>

3. Connect appropriate wires to USB RS485 Adapter

## Raspberry Pi Can Hat
If using a Raspberry Pi Can Hat, The expected pinout RS485 A/B configuration maybe be reversed.

If you get the following error while using a Raspberry Pi Can Hat swap your A/B wires:

```
ERROR:.transport_base[transport.0]:<bound method ModbusException.__str__ of ModbusIOException()>
```


## Configuration
Follow configuration example for ModBus RTU to MQTT
https://github.com/HotNoob/PythonProtocolGateway/wiki/Configuration-Examples#modbus-rtu-to-mqtt

#### EG4 6000XP, EG4 18Kpv
```
protocol_version = eg4_v58
baud = 19200
```

#### EG4 3000EHV inverters
```
protocol_version = eg4_3000ehv_v1
```

protocols may not be limited to the models listed.

