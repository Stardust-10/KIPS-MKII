import RPi.GPIO as GPIO
import time
import subprocess
import os
import sys

# ------------------ Configuration ------------------
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200  # Increased for efficiency; lower to 115200 if it fails
CHIP_TYPE = "esp32s3"
BOOT_PIN = 17


# ---------------------------------------------------

def get_firmware_choice():
    """Lists .bin files in the directory and asks the user to pick one."""
    files = [f for f in os.listdir('.') if f.endswith('merged.bin')]
    if not files:
        print("❌ No .bin files found in the current directory.")
        sys.exit(1)

    print("\n--- Available Firmware Files ---")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")

    try:
        choice = int(input("\nSelect file number to upload: "))
        return files[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BOOT_PIN, GPIO.OUT)


def flash_firmware(filename):
    # Hold BOOT LOW
    GPIO.output(BOOT_PIN, GPIO.LOW)
    print(f"\n>> Holding BOOT (GPIO {BOOT_PIN}) LOW.")
    print(">> ACTION: Press and release the RESET button on the ESP32.")
    input(">> Once reset, press ENTER to start flashing...")

    # Modern esptool command with dash-syntax
    esptool_cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP_TYPE,
        "--port", SERIAL_PORT,
        "--baud", str(BAUD_RATE),
        "--before", "no-reset",
        "--after", "hard-reset",
        "write-flash",
        "-z",
        "0x0",  # Flash address
        filename
    ]

    try:
        print(f"\n🚀 Uploading {filename}...")
        subprocess.run(esptool_cmd, check=True)
        print("\n✨ SUCCESS: Firmware uploaded and chip rebooted.")
    except subprocess.CalledProcessError:
        print("\n❌ ERROR: Flash failed. Ensure the ESP is in bootloader mode.")


def main():
    try:
        selected_file = get_firmware_choice()
        setup_gpio()
        flash_firmware(selected_file)
    finally:
        GPIO.output(BOOT_PIN, GPIO.HIGH)
        GPIO.cleanup()
        print("GPIO cleaned up. System ready.")


if __name__ == "__main__":
    main()