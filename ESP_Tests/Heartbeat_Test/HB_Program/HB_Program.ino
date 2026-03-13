#include <Arduino.h>
#include <HardwareSerial.h>
#include "DFRobot_Heartrate.h"
#define hbRatePin 4
#define hbPowerPin 16

/*

  Pinout:
    black wire = GND
    Red wire = PWR (3V3 on ESP32S3)
    Green wire = Signal 

*/

DFRobot_Heartrate heartrate(DIGITAL_MODE);   // ANALOG_MODE or DIGITAL_MODE

//UART
HardwareSerial SerialUART32_0(0);
HardwareSerial SerialUART32_1(1);
#define UART_TX_PIN 43
#define UART_RX_PIN 44 

void sensorOn() {
  digitalWrite(hbPowerPin, HIGH);
  delay(1000); //Gives sensor time to fully activate
}

void sensorOff() {
  digitalWrite(hbPowerPin, LOW);
}

void setup() {
  Serial.begin(115200);
  SerialUART32_0.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

  pinMode(hbPowerPin, OUTPUT);
  pinMode(hbRatePin, INPUT);

  sensorOff(); //HB sensor off by default

  Serial.print("Sensor off. You may attempt to measure heart rate.\n");

}

void loop() {

  if(SerialUART32_0.available()) {
    
    String cmd = SerialUART32_0.readStringUntil('\n');
    cmd.trim();

    Serial.print("From CM4: ");
    Serial.println(cmd);

    if(cmd == "3") {

      sensorOn();

      SerialUART32_0.println("HB_START");

      unsigned long start = millis();
      uint8_t rateValue = 0;

      while (millis() - start < 30000) {
        /*
        int raw = digitalRead(hbRatePin);
        Serial.print("pulse: ");
        Serial.println(raw);
        */

        heartrate.getValue(hbRatePin);   // ESP32-S3 pin 18 foot sampled values
        rateValue = heartrate.getRate();   // Get heart rate value 

        if(rateValue)  {
          //Print to serial monitor
          Serial.print("hb: ");
          Serial.println(rateValue);

          //Then print to UART
          SerialUART32_0.print("HB:");
          SerialUART32_0.println(rateValue);
        }

        delay(20);
      }

    Serial.println("Heartbeat session ended.");   // debug message
    SerialUART32_0.println("HB_END");              // message for CM4
    sensorOff();
    Serial.println("HB sensor shut down.");

    }

    else {
      SerialUART32_0.println("Serial UART Line 0 unavailable.");
      sensorOff();
    }

  }
}
