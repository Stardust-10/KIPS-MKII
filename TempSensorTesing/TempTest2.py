import serial

ser = serial.Serial("/dev/serial0", 9600, timeout=2)

# Send command
ser.write(b"1\n")
print("Sent command 1")

# Read response
while True:
    line = ser.readline().decode(errors="ignore").strip()
    if not line:
        continue

    print("From ESP32:", line)

    if line == "END":
        break

ser.close()
