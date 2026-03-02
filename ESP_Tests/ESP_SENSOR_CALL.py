import serial
import argparse

ser = serial.Serial("/dev/serial0", 112500, timeout = 2)

def call_data(tempHum, lux, hb):
	
	#If temp request is present, inquire to ESP
	#If no request, temp val is set to none
	if tempHum:
		ser.write(b"1\n") #bytes literal
		temp_val = ser.readline().decode(errors = "ignore").strip()
		hum_val = ser.readline().decode(errors = "ignore").strip()
	
	else:
		temp_val: Any = None
		hum_val: Any = None
	
	#If lux request is present, inquire to ESP
	#If no request,lux is set to none
	if lux:
		ser.write(b"2\n").encode
		lux_val = ser.readline().decode(errors = "ignore").strip()
	
	else:
		lux_val: Any = None
		
	if hb:
		ser.write(b"3\n")
		hb_val = ser.readline().decode(errors = "ignore").strip()
		
	else:
		hb_val: None
		
	print(temp_val, hum_val, lux_val, hb_val)
	return(temp_val, hum_val, lux_val, hb_val)
		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = "Sensor data parser")
	parser.add_argument("--temphum", action = "store_true", help = "Reads temperature and humidity")
	parser.add_argument("--lux", action = "store_true", help = "Reads light level")
	parser.add_argument("--hb", action = "store_true", help = "Reads heartbeat value.")
	
	args = parser.parse_args()
		
	ret_vals = call_data(
		args.temphum,
		args.lux,
		args.hb
	)
