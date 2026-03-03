import serial
import argparse

ser = serial.Serial("/dev/serial0", 112500, timeout = 2)

def call_data(tempHum, lux, hb, temp_internal):
	
	# If temp request is present, inquire to ESP
	if tempHum:
		ser.write(b"1\n") #bytes literal
		# expects two lines of data, first is temp, second is humidity
		# values returned as TEMP:XX.XX and HUM:XX.XX
		# strip off the leading text and return just the value
		temp_val = ser.readline().decode(errors = "ignore").strip().split(":")[1]
		hum_val = ser.readline().decode(errors = "ignore").strip().split(":")[1]
		print(f"Temperature: {temp_val}")
		print(f"Humidity: {hum_val}")
		return temp_val, hum_val
	
	# If ldr request is present, inquire to ESP
	if lux:
		ser.write(b"2\n")
		lux_val = ser.readline().decode(errors = "ignore").strip().split(":")[1]
		print(f"Brightness:{lux_val}")
		return lux_val
		
	# If heartbeat request is present, inquire to ESP	
	if hb:
		ser.write(b"3\n")
		hb_val = ser.readline().decode(errors = "ignore").strip().split(":")[1]
		print(f"Heartbeat Measurement: {hb_val}")
		return hb_val
	
	# If internal temp request is present, inquire to ESP
	if temp_internal:
		ser.write(b"4\n")
		temp_internal_val = ser.readline().decode(errors = "ignore").strip().split(":")[1]
		print(f"Internal Temperature: {temp_internal_val}")
		return temp_internal_val
		
	return None
		

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
