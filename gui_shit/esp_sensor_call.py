import serial
import argparse
import math

ser = serial.Serial("/dev/serial0", 115200, timeout=2)

def _read_until_prefix(prefix, max_lines=20):
    for _ in range(max_lines):
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        print("RX:", line)

        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()

    raise RuntimeError(f"Timed out waiting for {prefix}")

def call_data(tempHum, lux, hb, temp_internal):
    if tempHum:
        ser.reset_input_buffer()
        ser.write(b"1\n")
        ser.flush()

        temp_val = _read_until_prefix("TEMP:")
        hum_val = _read_until_prefix("HUM:")

        print(f"Temperature: {temp_val}")
        print(f"Humidity: {hum_val}")
        return temp_val, hum_val

    if lux:
        ser.reset_input_buffer()
        ser.write(b"2\n")
        ser.flush()

        lux_val = _read_until_prefix("LDR:")
        print(f"Brightness: {lux_val}")
        return lux_val

    if hb:
        ser.reset_input_buffer()
        ser.write(b"3\n")
        ser.flush()

        active = False
        readings = []

        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            print("RX:", line)

            if line == "HB_START":
                active = True
                readings = []

            elif line == "HB_END":
                if readings:
                    return sum(readings) / len(readings)
                return None

            elif active and line.startswith("HB:"):
                try:
                    bpm = int(line.split(":", 1)[1])
                    readings.append(bpm)
                except ValueError:
                    print("Invalid heartbeat reading received.")


    # If temp request is present, inquire to ESP
    if temp_internal:
        ser.reset_input_buffer()
        ser.write(b"1\n")
        ser.flush()

        temp_val = _read_until_prefix("TEMP:")
        hum_val = _read_until_prefix("HUM:")

        print(f"Temperature: {temp_val}")
        print(f"Humidity: {hum_val}")
        return temp_val, hum_val
        
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Sensor data parser")
	parser.add_argument("--temphum", action = "store_true", help = "Reads temperature and humidity")
	parser.add_argument("--lux", action = "store_true", help = "Reads light level")
	parser.add_argument("--hb", action = "store_true", help = "Reads heartbeat value.")
	parser.add_argument("--internaltemp", action = "store_true", help = "Reads internal temperature of KIPS")
	
	args = parser.parse_args()
		
	ret_vals = call_data(
		args.temphum,
		args.lux,
		args.hb,
		args.internaltemp
	)
