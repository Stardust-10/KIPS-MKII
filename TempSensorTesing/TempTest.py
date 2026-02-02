import serial
import time

ser = serial.Serial("/dev/serial0", 9600, timeout=1)

def send_number(num: int):
    message = f"{num}\n"
    ser.write(message.encode("utf-8"))
    ser.flush()
    print(f"Sent: {num}")

try:
    while True:
        send_number(1)
        time.sleep(2)
        send_number(2)
        time.sleep(2)
        send_number(3)
        time.sleep(2)

except KeyboardInterrupt:
    ser.close()
