import RPi.GPIO as GPIO
import time

BOOT_PIN = 17
TX_PIN = 14

GPIO.setmode(GPIO.BCM)
GPIO.setup(BOOT_PIN, GPIO.OUT)

print("Testing Node Voltage...")
# Pull LOW
GPIO.output(BOOT_PIN, GPIO.LOW)
print("Node should be 0V. Check with a multimeter or LED.")
time.sleep(5)

# Pull HIGH
GPIO.output(BOOT_PIN, GPIO.HIGH)
print("Node should be 3.3V.")
time.sleep(5)

GPIO.cleanup()
