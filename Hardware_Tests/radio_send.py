import serial
import sys
import time

"""
Python GUI shouldn't keep the serial port open (which can cause locks), 
So this opens the port, sends the command, and exits. 
KEEP IN SAME FOLDER AS MOBILE_GUI_1 AND RADIO_MASTER
"""

# Update this to the actual port connecting your Pi CM4 to the ESP32
SERIAL_PORT = "/dev/ttyAMA0" 
BAUD_RATE = 115200

if len(sys.argv) > 1:
    
    command = sys.argv[1] + "\n"
    
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(command.encode('utf-8'))
            time.sleep(0.1) # Small delay to ensure buffer sends
    
    except Exception as e:
        print(f"Serial Error: {e}")
