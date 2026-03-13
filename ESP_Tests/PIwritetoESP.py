import serial
import time
import os
import RPi.GPIO as GPIO

UART_PORT = "/dev/serial0"
BAUD = 115200
FIRMWARE_FILE = "firmware.bin"

BOOT_PIN = 17
RESET_PIN = 27

CHUNK_SIZE = 1024

GPIO.setmode(GPIO.BCM)
GPIO.setup(BOOT_PIN, GPIO.OUT)
GPIO.setup(RESET_PIN, GPIO.OUT)


def enter_bootloader():

    GPIO.output(BOOT_PIN, GPIO.LOW)

    GPIO.output(RESET_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(RESET_PIN, GPIO.HIGH)

    time.sleep(0.1)
    GPIO.output(BOOT_PIN, GPIO.HIGH)


def flash():

    ser = serial.Serial(UART_PORT, BAUD, timeout=5)

    print("Sending START_UPDATE")

    ser.write(b"START_UPDATE\n")

    ack = ser.readline().decode().strip()

    if ack != "ACK_START":
        print("ESP did not acknowledge start command")
        return

    print("ESP acknowledged update")

    size = os.path.getsize(FIRMWARE_FILE)

    print("Firmware size:", size)

    ser.write(f"{size}\n".encode())

    time.sleep(0.2)

    with open(FIRMWARE_FILE, "rb") as f:

        while True:

            data = f.read(CHUNK_SIZE)

            if not data:
                break

            ser.write(data)

    ser.flush()

    print("Firmware sent, waiting for response...")

    while True:

        line = ser.readline().decode().strip()

        if line:

            print("ESP:", line)

            if line in ["UPDATE_OK", "UPDATE_FAIL"]:
                break

    ser.close()


enter_bootloader()
flash()

GPIO.cleanup()
