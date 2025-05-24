''' simulate modbus tcp server for testing ppg '''
import sys
from modbus_tk import modbus_tcp, hooks, utils
from modbus_tk.defines import HOLDING_REGISTERS

def on_write_request(request):
    print(f"Write request: {request}")


server = modbus_tcp.TcpServer(address="0.0.0.0", port=5020)
slave = server.add_slave(1)
slave.add_block('0', HOLDING_REGISTERS, 0, 100)  # 100 registers
slave.set_values('0', 40, [1] * (55 - 40 + 1)) #regiters 40-55 set to 1. for emulating hdhk_16ch_ac_module

server.start()
print("Modbus server is running on port 5020...")

hooks.install_hook("modbus.Server.before_handle_request", on_write_request)

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping server...")
    server.stop()
