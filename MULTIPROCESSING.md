# Multiprocessing Support

## Overview

The Python Protocol Gateway now supports **automatic multiprocessing** when multiple transports are configured. This provides true concurrency and complete isolation between transports, solving the "transport busy" issues that can occur with single-threaded operation.

## How It Works

### Automatic Detection
- **Single Transport**: Uses the original single-threaded approach
- **Multiple Transports**: Automatically switches to multiprocessing mode

### Process Isolation
Each transport runs in its own separate process, providing:
- **Complete isolation** of resources and state
- **True concurrent operation** - no waiting for other transports
- **Independent error handling** - one transport failure doesn't affect others
- **Automatic restart** of failed processes

### Transport Types

#### Input Transports (read_interval > 0)
- Modbus RTU, TCP, etc.
- Actively read data from devices
- Send data to output transports via bridging

#### Output Transports (read_interval <= 0)
- InfluxDB, MQTT, etc.
- Receive data from input transports via bridging
- Process and forward data to external systems

## Configuration Example

```ini
[transport.0]
transport = modbus_rtu
protocol_version = eg4_v58
address = 1
port = /dev/ttyUSB0
baudrate = 19200
bridge = influxdb_output
read_interval = 10

[transport.1]
transport = modbus_rtu
protocol_version = eg4_v58
address = 1
port = /dev/ttyUSB1
baudrate = 19200
bridge = influxdb_output
read_interval = 10

[influxdb_output]
transport = influxdb_out
host = influxdb.example.com
port = 8086
database = solar
measurement = eg4_data
```

## Inter-Process Communication

### Bridging
- Uses `multiprocessing.Queue` for communication
- Automatic message routing between processes
- Non-blocking communication
- Source transport information preserved

### Message Format
```python
{
    'source_transport': 'transport.0',
    'target_transport': 'influxdb_output',
    'data': {...},
    'source_transport_info': {
        'transport_name': 'transport.0',
        'device_identifier': '...',
        'device_manufacturer': '...',
        'device_model': '...',
        'device_serial_number': '...'
    }
}
```

## Benefits

### Performance
- **True concurrency** - no serialization delays
- **Independent timing** - each transport runs at its own interval
- **No resource contention** - each process has isolated resources

### Reliability
- **Process isolation** - one transport failure doesn't affect others
- **Automatic restart** - failed processes are automatically restarted
- **Independent error handling** - each process handles its own errors

### Scalability
- **Linear scaling** - performance scales with number of CPU cores
- **Resource efficiency** - only uses multiprocessing when needed
- **Memory isolation** - each process has its own memory space

## Troubleshooting

### Common Issues

#### "Register is Empty; transport busy?"
- **Cause**: Shared state between transports in single-threaded mode
- **Solution**: Use multiprocessing mode (automatic with multiple transports)

#### InfluxDB not receiving data
- **Cause**: Output transport not properly configured or started
- **Solution**: Ensure `influxdb_output` section has `transport = influxdb_out`

#### Process restarting frequently
- **Cause**: Transport configuration error or device connection issue
- **Solution**: Check logs for specific error messages

### Debugging

#### Enable Debug Logging
```ini
[general]
log_level = DEBUG
```

#### Monitor Process Status
The gateway logs process creation and status:
```
[2025-06-22 19:30:45] Starting multiprocessing mode with 3 transports
[2025-06-22 19:30:45] Input transports: 2, Output transports: 1
[2025-06-22 19:30:45] Bridging detected - enabling inter-process communication
[2025-06-22 19:30:45] Started process for transport.0 (PID: 12345)
[2025-06-22 19:30:45] Started process for transport.1 (PID: 12346)
[2025-06-22 19:30:45] Started process for influxdb_output (PID: 12347)
```

## Testing

Run the test script to verify multiprocessing functionality:
```bash
python pytests/test_multiprocessing.py
```

This will:
- Load your configuration
- Display transport information
- Run for 30 seconds to verify operation
- Show any errors or issues

## Limitations

1. **Memory Usage**: Each process uses additional memory
2. **Startup Time**: Slight delay when starting multiple processes
3. **Inter-Process Communication**: Bridge messages have small overhead
4. **Debugging**: More complex debugging due to multiple processes

## Migration

No migration required! Existing configurations will automatically benefit from multiprocessing when multiple transports are present.

## Performance Tips

1. **Stagger Read Intervals**: Use different read intervals to avoid resource contention
2. **Optimize Batch Sizes**: Adjust batch sizes for faster individual reads
3. **Monitor Logs**: Watch for process restarts indicating issues
4. **Resource Limits**: Ensure sufficient system resources for multiple processes 
