## Hardware
1. USB-B or USB-A cable
2. for models with a DB9 port a DB9 RS232 adapter is required. "Before use RS232 communication, you should make sure the follow PIN1 and PIN2 are OFF"
3. Connect cable to wifi dongle port; if a alternative usb port exists, try connecting to that one first. 

## Configuration
Follow configuration example for ModBus RTU to MQTT
https://github.com/HotNoob/PythonProtocolGateway/wiki/Configuration-Examples#modbus-rtu-to-mqtt

```
protocol_version = v0.14
```

## HomeAssistant Cards
Here are some example cards. If you want to use them, you will have to change the variable names and others to reflect your configs. 

## PV1 & PV2 Card
![pv watts](https://github.com/HotNoob/PythonProtocolGateway/assets/2180145/372980f9-f2d6-48e5-9acd-ee519badb61f)
<details>
  <summary>code</summary>

```
type: horizontal-stack
cards:
  - type: gauge
    needle: false
    name: PV1 Voltage
    entity: sensor.growatt_inverter_pv1_voltage
    severity:
      green: 150
      yellow: 50
      red: 0
  - type: gauge
    entity: sensor.growatt_inverter_pv2_voltage
    name: PV2 Voltage
    severity:
      green: 125
      yellow: 50
      red: 0
  - type: gauge
    needle: false
    entity: sensor.growatt_inverter_pv1_watts
    name: PV1 Watts
    severity:
      green: 750
      yellow: 250
      red: 0
  - type: gauge
    entity: sensor.growatt_inverter_pv2_watts
    name: PV2 Watts
    severity:
      green: 750
      yellow: 250
      red: 0
```
</details>

## Output Card
![output](https://github.com/HotNoob/PythonProtocolGateway/assets/2180145/9a129dad-73bc-4401-9746-d7a0dd22cf0a)
<details>
  <summary>code</summary>

```
type: horizontal-stack
cards:
  - type: gauge
    needle: true
    entity: sensor.growatt_inverter_output_voltage
    name: Output Voltage
    max: 270
    min: 210
    segments:
      - from: 0
        color: '#db4437'
      - from: 220
        color: '#ffa600'
      - from: 235
        color: '#43a047'
      - from: 245
        color: '#ffa600'
      - from: 250
        color: '#db4437'
  - type: gauge
    entity: sensor.growatt_inverter_output_hz
    name: Output Hertz
    unit: hz
    needle: true
    max: 62
    min: 58
    segments:
      - from: 0
        color: '#db4437'
      - from: 59
        color: '#ffa600'
      - from: 59.5
        color: '#43a047'
      - from: 60.5
        color: '#ffa600'
      - from: 61
        color: '#db4437'
  - type: gauge
    needle: false
    entity: sensor.growatt_inverter_output_wattage
    name: Output Watts
    severity:
      green: 0
      yellow: 1200
      red: 8000
    max: 12000
  - type: gauge
    entity: sensor.growatt_inverter_output_current
    name: Output Current
    severity:
      green: 0
      yellow: 10
      red: 40
    max: 50

```
</details>