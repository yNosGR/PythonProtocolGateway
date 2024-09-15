# AOLithium To MQTT

## Battery Protocols

AOLithium has multiple protocols, which are set via the dip switches. 

## SMA / Victron CanBus - dip5 off, dip 6 off
```
protocol_version = victron_gx_generic_canbus
```

sma_sunny_island_v1 can also be used, but provides less information

### CanBus pinout
see manual

### hardware
1. USB Canbus adapter -- see canbus transport
2. rj45 ethernet cable cut in half

