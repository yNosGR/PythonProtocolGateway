## Hardware
1. USB-B or USB-A cable
2. Connect usb cable.

## Configuration
Follow configuration example for ModBus RTU to MQTT
https://github.com/HotNoob/PythonProtocolGateway/wiki/Configuration-Examples#modbus-rtu-to-mqtt

```
protocol_version = sigineer_v0.11
```


## Home Assistant Cards

### Voltage Card
![sigineer output](https://github.com/HotNoob/PythonProtocolGateway/assets/2180145/55900744-6aaf-4b44-bf3e-46976fdffce2)

<details>
<summary>code</summary>

```
type: horizontal-stack
cards:
  - type: gauge
    needle: false
    name: Battery
    entity: sensor.sigineer_battery_voltage
  - type: gauge
    entity: sensor.sigineer_output_voltage
    name: Output
  - type: gauge
    needle: false
    entity: sensor.sigineer_bus_voltage
    name: Bus
  - type: gauge
    entity: sensor.sigineer_grid_voltage
    name: Grid
    severity:
      green: 750
      yellow: 250
      red: 0

```
</details>