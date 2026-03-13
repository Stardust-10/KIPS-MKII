import RPi.GPIO as GPIO
import time
import subprocess
import os
import sys
import serial

# ------------------ Configuration ------------------
SERIAL_PORT = "/dev/serial0"
BAUD_RATE_FLASH = 460800      # High speed for flashing
BAUD_RATE_TALK = 115200       # Match your Arduino Serial.begin()
CHIP_TYPE = "esp32s3"
BOOT_PIN = 17                 # The "Direct" wire to the node
# ---------------------------------------------------

def get_firmware_choice():
    """Finds all .bin files and lets you pick one."""
    files = [f for f in os.listdir('.') if f.endswith('.bin')]
    if not files:
        print("❌ Error: No .bin files found in this folder.")
        sys.exit(1)
    
    print("\n--- Select Firmware ---")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")
    
    try:
        choice = int(input("\nChoice #: "))
        return files[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)

def setup_hardware():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Start with GPIO 17 as an INPUT so it doesn't interfere yet
    GPIO.setup(BOOT_PIN, GPIO.IN)

def run_flash_sequence(filename):
    print("\n--- 1. FLASHING PHASE ---")
    # Pull the node LOW to override the TX pin
    GPIO.setup(BOOT_PIN, GPIO.OUT)
    GPIO.output(BOOT_PIN, GPIO.LOW)
    print(f">> Node held LOW by GPIO {BOOT_PIN}.")
    print(">> ACTION: Press/Release RESET button on the ESP32.")
    
    input(">> Once reset, press ENTER to start the upload...")

    # Modern dash-syntax esptool command
    cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP_TYPE,
        "--port", SERIAL_PORT,
        "--baud", str(BAUD_RATE_FLASH),
        "--before", "no-reset",
        "--after", "no-reset",
        "write-flash", "-z", "0x0", filename
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✨ Flash successful!")
    except subprocess.CalledProcessError:
        print("\n❌ Flash failed. Check wiring/reset timing.")
        return False
    return True

def run_monitor_phase():
    print("\n--- 2. COMMUNICATION PHASE ---")
    # CRITICAL: Set GPIO 17 to HIGH then INPUT so it "releases" the node
    GPIO.output(BOOT_PIN, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.setup(BOOT_PIN, GPIO.IN) 
    print(">> GPIO 17 released. Node is now controlled by TX pin.")
    print(">> ACTION: Press RESET on ESP32 to start your app.")
    
    print(f">> Opening Monitor on {SERIAL_PORT} at {BAUD_RATE_TALK}...")
    print(">> (Press Ctrl+C to exit)\n")

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE_TALK, timeout=0.1) as ser:
            while True:
                if ser.in_waiting:
                    # Read and decode the incoming data
                    line = ser.readline().decode('utf-8', errors='ignore')
                    print(line, end='')
    except KeyboardInterrupt:
        print("\n\nMonitor closed.")

def main():
    selected_file = get_firmware_choice()
    setup_hardware()
    
    if run_flash_sequence(selected_file):
        run_monitor_phase()
    
    GPIO.cleanup()

if __name__ == "__main__":
    main()
