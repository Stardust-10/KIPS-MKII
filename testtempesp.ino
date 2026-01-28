#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"

Adafruit_AM2320 am2320 = Adafruit_AM2320();

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    delay(10);
  }

  Serial.println("ESP32 ready");
  am2320.begin();
}

void loop() {

  // Wait for command from Pi
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    int command = input.toInt();

    if (command == 1) {
      float temp = am2320.readTemperature();
      float hum  = am2320.readHumidity();

      // Send data ONCE
      Serial.print("TEMP:");
      Serial.println(temp);

      Serial.print("HUM:");
      Serial.println(hum);
    }
    else {
      Serial.println("ERR:UNKNOWN_CMD");
    }
  }
}
