import serial

ser = serial.Serial("/dev/serial0", 9600, timeout=2)

print("Type 1 and press Enter to request sensor data")
print("Type q to quit")

try:
    while True:
        user_input = input("> ").strip()

        if user_input.lower() == "q":
            break

        # Send input to ESP32
        ser.write((user_input + "\n").encode())
        print(f"Sent: {user_input}")

        # Read response from ESP32
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            print("From ESP32:", line)

            if line == "END":
                break

except KeyboardInterrupt:
    pass
finally:
    ser.close()
    print("Serial closed")
