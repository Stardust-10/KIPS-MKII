#!/usr/bin/env python3
import serial
import uinput
import time
import os

# Initialize the virtual device with Mouse and Keyboard capabilities
# This talks directly to /dev/uinput (The Linux Kernel)
device = uinput.Device([
    uinput.REL_X,
    uinput.REL_Y,
    uinput.BTN_LEFT,
    uinput.KEY_ENTER,
    uinput.KEY_UP,
    uinput.KEY_DOWN,
    uinput.KEY_LEFT,
    uinput.KEY_RIGHT,
])

# Matches your CM4 Serial pinout
SERIAL_PORT = "/dev/ttyAMA4" 
BAUD_RATE = 115200

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
        print(f"Bridge Active. Listening on {SERIAL_PORT}...")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # Handle Mouse Movement (M,x,y)
                if line.startswith("M,"):
                    parts = line.split(',')
                    if len(parts) == 3:
                        dx = int(parts[1]) // 80 
                        dy = int(parts[2]) // 80
                        device.emit(uinput.REL_X, dx)
                        device.emit(uinput.REL_Y, dy)

                # Handle Digital Buttons
                elif line == "UP":
                    device.emit_click(uinput.KEY_UP)
                elif line == "DOWN":
                    device.emit_click(uinput.KEY_DOWN)
                elif line == "LEFT":
                    device.emit_click(uinput.KEY_LEFT)
                elif line == "RIGHT":
                    device.emit_click(uinput.KEY_RIGHT)
                elif line == "ENTER":
                    # Emit a Left Mouse Click
                    device.emit(uinput.BTN_LEFT, 1)
                    time.sleep(0.02)
                    device.emit(uinput.BTN_LEFT, 0)

            except Exception as e:
                continue

if __name__ == "__main__":
    main()
