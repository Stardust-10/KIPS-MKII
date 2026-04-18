#!/usr/bin/env python3
import serial
import time

def get_plug_status():
    try:
        # Open serial connection
        ser = serial.Serial('/dev/serial0', 115200, timeout=1)
        time.sleep(0.1)
        
        # Read the line from ESP32
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        ser.close()
        
        # Match your specific printf format
        if "PLUG_STAT:1" in line:
            return "wall"
    except Exception as e:
        # Log error to stderr for journalctl debugging
        import sys
        print(f"Serial Error: {e}", file=sys.stderr)
        
    return "battery"

if __name__ == "__main__":
    # Output for ui-switcher.sh
    print(get_plug_status())
