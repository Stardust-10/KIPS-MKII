#!/usr/bin/env python3

#put in /usr/local/bin/power_detect.py
import serial
import time

# CONFIGURATION
SERIAL_PORT = '/dev/serial0' 
BAUD_RATE = 115200

def get_esp32_data():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.1) 
        ser.flushInput()
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()

        if "VOLT:" in line:
            parts = line.split(',')
            volt_part = parts[0].split(':')[1]
            return float(volt_part)
    except Exception:
        return 0.0 # Default to battery mode on error
    return 0.0

if __name__ == "__main__":
    v = get_esp32_data()
    # Threshold: Wall > 4.15V
    if v > 4.15:
        print("wall")
    else:
        print("battery")
