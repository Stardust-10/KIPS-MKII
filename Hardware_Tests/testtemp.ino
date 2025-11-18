#include <Wire.h>

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9); // SDA=8, SCL=9
  Serial.println("I2C Scanner on ESP32-S3");
}

void loop() {
  byte error, address;
  int nDevices = 0;

  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at 0x");
      Serial.println(address, HEX);
      nDevices++;
    }
  }

  if (nDevices == 0)
    Serial.println("No I2C devices found.");

  delay(2000);
}
