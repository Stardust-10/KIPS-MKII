import serial
import argparse

ser = serial.Serial("/dev/serial0", 112500, timeout = 2)

def call_data(tempHum, lux, hb):
	ESP_Tests/AllSensors/AllSensors.ino
	ESP_Tests/AllSensors/Readme.md
	ESP_Tests/Heartbeat_Test/Heartbeat_Test/Heartbeat_Test.ino
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/DFRobot_Heartrate.cpp
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/DFRobot_Heartrate.h
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/LICENSE
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/README_CN.md
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/ReadMe.md
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/examples/LCDDisplayHeartrate/LCDDisplayHeartrate.ino
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/examples/heartrateAnalogMode/heartrateAnalogMode.ino
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/examples/heartrateDigitalMode/heartrateDigitalMode.ino
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/keywords.txt
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/library.properties
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/resources/Hardware/Layout.pdf
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/resources/Hardware/SEN0203 Heart Rate Sensor Schematic.pdf
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/resources/Hardware/SON1303 Datasheet.pdf
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/resources/Hardware/SON3130-V1.2.pdf
	ESP_Tests/Heartbeat_Test/libraries/DFRobot_Heartrate/resources/images/Heartrate.png
	ESP_Tests/LDR_TEST/LDR_TEST.ino
	ESP_Tests/Master_Sensor_Program/Master_Sensor_Program.ino
	ESP_Tests/TempSensorTesing/TempTest.py
	ESP_Tests/TempSensorTesing/TempTest2.py
	ESP_Tests/TempSensorTesing/TempTest3.py
	ESP_Tests/TempSensorTesing/files
	ESP_Tests/TempSensorTesing/testtempback.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_AM2320_sensor_library/Adafruit_AM2320.cpp
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_AM2320_sensor_library/Adafruit_AM2320.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_AM2320_sensor_library/README.md
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_AM2320_sensor_library/examples/basic_am2320/basic_am2320.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_AM2320_sensor_library/library.properties
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_BusIO_Register.cpp
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_BusIO_Register.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_GenericDevice.cpp
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_GenericDevice.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_I2CDevice.cpp
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_I2CDevice.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_I2CRegister.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_SPIDevice.cpp
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/Adafruit_SPIDevice.h
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/CMakeLists.txt
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/LICENSE
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/README.md
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/component.mk
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/genericdevice_uartregtest/genericdevice_uartregtest.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/genericdevice_uarttest/genericdevice_uarttest.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/i2c_address_detect/i2c_address_detect.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/i2c_readwrite/i2c_readwrite.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/i2c_registers/i2c_registers.ino
	ESP_Tests/TempSensorTesing/testtempesp/libraries/Adafruit_BusIO/examples/i2corspi_register/i2corspi_register.ino
	ESP
Aborting
Merge with strategy ort failed.
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
