import serial
import RPi.GPIO as GPIO
import time
import os

# ---------- CONFIG ----------
UART_PORT = "/dev/serial0"  # Pi UART
BAUD = 115200
FIRMWARE_FILE = "firmware.bin"
BOOT_PIN = 17   # GPIO controlling ESP32 BOOT (GPIO0)
RESET_PIN = 27  # GPIO controlling ESP32 RESET (optional)
CHUNK_SIZE = 1024  # bytes per write
TX_DELAY = 0.01  # small delay to prevent buffer overflow
# -----------------------------

def enter_bootloader():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BOOT_PIN, GPIO.OUT)
    GPIO.setup(RESET_PIN, GPIO.OUT)
    
    # Pull BOOT low
    GPIO.output(BOOT_PIN, GPIO.LOW)
    
    # Toggle RESET
    GPIO.output(RESET_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(RESET_PIN, GPIO.HIGH)
    
    # Release BOOT
    time.sleep(0.1)
    GPIO.output(BOOT_PIN, GPIO.HIGH)
    time.sleep(0.2)

def flash_firmware():
    # Open UART
    ser = serial.Serial(UART_PORT, BAUD, timeout=1)
    time.sleep(0.5)
    
    print("Sending START_UPDATE command...")
    ser.write(b'START_UPDATE\n')
    
    # Wait for ACK
    ack = ser.readline().decode().strip()
    if ack != "ACK_START":
        print("ESP32 did not acknowledge start command. Got:", ack)
        ser.close()
        return
    
    print("ESP32 ready. Sending firmware...")
    
    # Send firmware in chunks
    with open(FIRMWARE_FILE, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            ser.write(chunk)
            time.sleep(TX_DELAY)
    
    ser.flush()
    print("Firmware sent. Waiting for ESP32 confirmation...")
    
    # Wait for final update result
    while True:
        line = ser.readline().decode().strip()
        if line:
            print("ESP32:", line)
            if line in ["UPDATE_OK", "UPDATE_FAIL"]:
                break
    
    ser.close()
    print("Flashing complete.")

if __name__ == "__main__":
    print("Entering bootloader mode...")
    enter_bootloader()
    flash_firmware()
    GPIO.cleanup()
