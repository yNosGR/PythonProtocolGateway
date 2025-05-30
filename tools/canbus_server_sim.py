import subprocess
import can
import time
import atexit
import signal
import sys
import os
from pathlib import Path



VCAN_IFACE = 'vcan0'
vcan_messages = []


def load_candump_file(filepath):
    os.chdir(Path(__file__).resolve().parent)

    messages = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or '#' not in line:
                continue

            try:
                can_id_str, data_str = line.split('#')
                can_id = int(can_id_str, 16)
                data = bytes.fromhex(data_str)

                msg = can.Message(
                    arbitration_id=can_id,
                    data=data,
                    is_extended_id=False
                )
                messages.append(msg)
            except Exception as e:
                print(f"Failed to parse line '{line}': {e}")

    return messages


def emulate_device():
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

    while True:
        for msg in vcan_messages:
            try:
                bus.send(msg)
                print(f"Sent message: {msg}")
            except can.CanError:
                print("Message NOT sent")
            time.sleep(1)  # Send message every 1 second

def setup_vcan(interface=VCAN_IFACE):
    try:
        # Load vcan kernel module
        subprocess.run(['sudo', 'modprobe', 'vcan'], check=True)

        # Add virtual CAN interface
        subprocess.run(['sudo', 'ip', 'link', 'add', 'dev', interface, 'type', 'vcan'], check=True)

        # Bring the interface up
        subprocess.run(['sudo', 'ip', 'link', 'set', 'up', interface], check=True)

        print(f"Virtual CAN interface {interface} is ready.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set up {interface}: {e}")


def cleanup_vcan(interface=VCAN_IFACE):
    try:
        subprocess.run(['sudo', 'ip', 'link', 'delete', interface], check=True)
        print(f"Removed {interface}")
    except subprocess.CalledProcessError as e:
        print(f"Error removing {interface}: {e}")

# Register cleanup to run at program exit
atexit.register(cleanup_vcan)

# Optional: Handle Ctrl+C gracefully
signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))


if __name__ == "__main__":
    setup_vcan()
    vcan_messages = load_candump_file("candump.txt")
    emulate_device()

