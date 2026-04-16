import RPi.GPIO as GPIO
import time
import subprocess
import os
import sys

# ------------------ Configuration ------------------
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 115200 
CHIP_TYPE = "esp32s3"
BOOT_PIN = 27       # Pi GPIO 27 -> ESP32-S3 GPIO 0
# ---------------------------------------------------

def get_firmware_choice():
    """Filters specifically for .merged.bin files."""
    files = [f for f in os.listdir('.') if f.endswith('.merged.bin')]
    
    if not files:
        print("Error: No '.merged.bin' files found in this directory.")
        sys.exit(1)
    
    print("\n--- Available Merged Firmware ---")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")
    
    try:
        choice = int(input("\nSelect file number: "))
        return files[choice]
    except (ValueError, IndexError):
        print("Invalid selection.")
        sys.exit(1)

def setup_gpio():
    """Sets up GPIO 27 to control the BOOT state."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BOOT_PIN, GPIO.OUT)
    # Start HIGH so the ESP stays in normal run mode
    GPIO.output(BOOT_PIN, GPIO.HIGH)

def flash_firmware(filename):
    print(f"\n[STEP 1] Pulling BOOT (GPIO {BOOT_PIN}) LOW...")
    GPIO.output(BOOT_PIN, GPIO.LOW)
    
    print("\n[STEP 2] ACTION REQUIRED:")
    print("    --> PRESS and RELEASE the physical RESET button on your board.")
    print("    --> The ESP32-S3 will now wait in Download Mode.")
    
    input("\n[STEP 3] Press ENTER here once you have clicked the button...")

    # esptool command with underscores and stability flags
    esptool_cmd = [
        sys.executable, "-m", "esptool",
        "--chip", CHIP_TYPE,
        "--port", SERIAL_PORT,
        "--baud", str(BAUD_RATE),
        "--before", "no_reset",    
        "--after", "hard_reset",
        "--no-stub",               # Bypasses missing .json/stub errors
        "write_flash",             # Corrected with underscore
        "-z",                      # Compress for faster transfer
        "--flash_mode", "keep",     # Most stable/compatible flash mode
        "--flash_freq", "keep",     # Standard frequency for S3
        "0x0",                     # Merged files MUST start at 0x0
        filename
    ]

    try:
        print(f"Uploading {filename} to address 0x0...")
        subprocess.run(esptool_cmd, check=True)
        print("\nSUCCESS: Flash complete!")
        print(">> Tap the Reset button one more time to start your application.")
    except subprocess.CalledProcessError:
        print("\nERROR: Flash failed.")
        print("If you still see MD5 mismatch, check your 3.3V power stability.")

def main():
    try:
        selected_file = get_firmware_choice()
        setup_gpio()
        flash_firmware(selected_file)
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    finally:
        # Crucial: Reset BOOT to HIGH so the chip can actually run
        GPIO.output(BOOT_PIN, GPIO.HIGH)
        GPIO.cleanup()
        print("GPIO cleaned up.")

if __name__ == "__main__":
    main()
