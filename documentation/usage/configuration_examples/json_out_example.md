# JSON Output Transport

The `json_out` transport outputs data in JSON format to either a file or stdout. This is useful for logging, debugging, or integrating with other systems that consume JSON data.

## Configuration

### Basic Configuration

```ini
[transport.json_output]
transport = json_out
# Output to stdout (default)
output_file = stdout
# Pretty print the JSON (default: true)
pretty_print = true
# Include timestamp in output (default: true)
include_timestamp = true
# Include device information (default: true)
include_device_info = true
```

### File Output Configuration

```ini
[transport.json_output]
transport = json_out
# Output to a file
output_file = /path/to/output.json
# Append to file instead of overwriting (default: false)
append_mode = false
pretty_print = true
include_timestamp = true
include_device_info = true
```

### Bridged Configuration Example

```ini
[transport.modbus_input]
# Modbus input transport
protocol_version = v0.14
address = 1
port = /dev/ttyUSB0
baudrate = 9600
bridge = transport.json_output
read_interval = 10

[transport.json_output]
# JSON output transport
transport = json_out
output_file = /var/log/inverter_data.json
pretty_print = false
append_mode = true
include_timestamp = true
include_device_info = true
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_file` | string | `stdout` | Output destination. Use `stdout` for console output or a file path |
| `pretty_print` | boolean | `true` | Whether to format JSON with indentation |
| `append_mode` | boolean | `false` | Whether to append to file instead of overwriting |
| `include_timestamp` | boolean | `true` | Whether to include Unix timestamp in output |
| `include_device_info` | boolean | `true` | Whether to include device metadata in output |

## Output Format

The JSON output includes the following structure:

```json
{
  "device": {
    "identifier": "device_serial",
    "name": "Device Name",
    "manufacturer": "Manufacturer",
    "model": "Model",
    "serial_number": "Serial Number",
    "transport": "transport_name"
  },
  "timestamp": 1703123456.789,
  "data": {
    "variable_name": "value",
    "another_variable": "another_value"
  }
}
```

### Compact Output Example

With `pretty_print = false` and `include_device_info = false`:

```json
{"timestamp":1703123456.789,"data":{"battery_voltage":"48.5","battery_current":"2.1"}}
```

### File Output with Append Mode

When using `append_mode = true`, each data read will be written as a separate JSON object on a new line, making it suitable for log files or streaming data processing.

## Use Cases

1. **Debugging**: Output data to console for real-time monitoring
2. **Logging**: Write data to log files for historical analysis
3. **Integration**: Feed data to other systems that consume JSON
4. **Data Collection**: Collect data for analysis or backup purposes

## Examples

### Console Output for Debugging

```ini
[transport.debug_output]
transport = json_out
output_file = stdout
pretty_print = true
include_timestamp = true
include_device_info = true
```

### Log File for Data Collection

```ini
[transport.data_log]
transport = json_out
output_file = /var/log/inverter_data.log
pretty_print = false
append_mode = true
include_timestamp = true
include_device_info = false
```

### Compact File Output

```ini
[transport.compact_output]
transport = json_out
output_file = /tmp/inverter_data.json
pretty_print = false
append_mode = false
include_timestamp = true
include_device_info = false
``` 