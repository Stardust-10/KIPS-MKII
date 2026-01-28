#include <Arduino.h>
#include <HardwareSerial.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"

// ======================================================== //
// UART setup
HardwareSerial SerialUART32_0(0); // UART0
HardwareSerial SerialUART32_1(1); // UART0

#define UART_TX_PIN 43
#define UART_RX_PIN 44
// ======================================================== //

Adafruit_AM2320 am2320 = Adafruit_AM2320();

void setup() {

  // USB Serial Monitor
  Serial.begin(9600);
  delay(2000);
  Serial.println("Beginning ESP32-S3 UART + AM2320 test.");

  // UART0 to Raspberry Pi
  SerialUART32_0.begin(9600, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(1000);
  Serial.println("UART0 initialized on TX=43 RX=44 @9600");

  // Sensor init
  if (!am2320.begin()) {
    Serial.println("AM2320 not detected!");
  } else {
    Serial.println("AM2320 ready.");
  }
}

void loop() {

  // Check for command from Pi
  if (SerialUART32_0.available()) {

    String incoming = SerialUART32_0.readStringUntil('\n');
    incoming.trim();

    Serial.print("From Pi: ");
    Serial.println(incoming);

    int command = incoming.toInt();

    if (command == 1) {
      float temp = am2320.readTemperature();
      float hum  = am2320.readHumidity();

      // Send sensor data ONCE
      SerialUART32_0.print("TEMP:");
      SerialUART32_0.println(temp);

      SerialUART32_0.print("HUM:");
      SerialUART32_0.println(hum);

      Serial.println("Sensor data sent once.");
    }
    else {
      SerialUART32_0.println("ERR:UNKNOWN_CMD");
    }
  }
}
