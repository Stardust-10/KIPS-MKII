import serial
import uinput
import time
from pynput.keyboard import Key, Controller as KeyboardController

keyboard = KeyboardController()

# Initialize the virtual device with both Mouse and Keyboard capabilities
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

SERIAL_PORT = "/dev/ttyAMA4" 
BAUD_RATE = 115200

def main():
    try:
        # Added a longer timeout to ensure we don't drop half-lines
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
        print(f"Bridge Active. Listening for KIPS MKII on {SERIAL_PORT}...")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    while True:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                if not line:
                    continue

                # Handle Mouse Movement (M,x,y)
                if line.startswith("M,"):
                    parts = line.split(',')
                    if len(parts) == 3:
                        # Your values are large (e.g., -2165). 
                        # Dividing by 50-100 is usually good for a 800x480 screen.
                        dx = int(parts[1]) // 80 
                        dy = int(parts[2]) // 80
                        device.emit(uinput.REL_X, dx)
                        device.emit(uinput.REL_Y, dy)

                # Handle Digital Buttons [cite: 35, 41-45]
                elif line == "UP":
                    device.emit_click(uinput.KEY_UP)
                elif line == "DOWN":
                    device.emit_click(uinput.KEY_DOWN)
                elif line == "LEFT":
                    device.emit_click(uinput.KEY_LEFT)
                elif line == "RIGHT":
                    device.emit_click(uinput.KEY_RIGHT)
                elif line == "ENTER":
                    device.emit_click(uinput.KEY_ENTER)

            except Exception as e:
                # Silently catch decode errors from serial noise
                continue

if __name__ == "__main__":
    main()
