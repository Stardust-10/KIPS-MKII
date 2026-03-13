import RPi.GPIO as GPIO
import time
import subprocess
import os
import sys

# ------------------ Configuration ------------------
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200
CHIP_TYPE = "esp32s3"
FLASH_ADDRESS = "0x0"
FIRMWARE_FILE = "PiListen.ino.bin"  # Updated filename

BOOT_PIN = 17  # Connected to ESP32 GPIO0
# ---------------------------------------------------

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BOOT_PIN, GPIO.OUT)

def trigger_manual_bootloader():
    print("\n--- BOOTLOADER PREPARATION ---")
    # Pull GPIO0 LOW to prepare for boot mode
    GPIO.output(BOOT_PIN, GPIO.LOW)
    print(f">> GPIO {BOOT_PIN} is now held LOW.")
    print(">> ACTION REQUIRED: Press the RESET button on the ESP32 now.")
    
    input(">> After resetting the ESP32, press ENTER to start flashing...")

def flash_firmware():
    if not os.path.isfile(FIRMWARE_FILE):
        print(f"Error: {FIRMWARE_FILE} not found.")
        return

    # Using modern dash-separated commands
    esptool_cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP_TYPE,
        "--port", SERIAL_PORT,
        "--baud", str(BAUD_RATE),
        "--before", "no-reset",
        "--after", "hard-reset",
        "write-flash", # Modern dash syntax
        "-z",
        FLASH_ADDRESS,
        FIRMWARE_FILE
    ]

    print(f"\nFlashing {FIRMWARE_FILE} to {CHIP_TYPE}...")
    try:
        subprocess.run(esptool_cmd, check=True)
        print("\n✨ Flashing successful!")
    except subprocess.CalledProcessError:
        print("\n❌ Flashing failed.")
        print("Check: TX/RX swap, Common Ground, or if Reset was pressed while BOOT was LOW.")

def main():
    try:
        setup_gpio()
        trigger_manual_bootloader()
        flash_firmware()
    finally:
        # Return BOOT pin to HIGH so the chip can run the new app
        GPIO.output(BOOT_PIN, GPIO.HIGH)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
