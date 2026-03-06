#include <Arduino.h>
#include <HardwareSerial.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"

// ================= UART =================
HardwareSerial SerialUART32_0(0);
HardwareSerial SerialUART32_1(1);
#define UART_TX_PIN 43
#define UART_RX_PIN 44
// ========================================

Adafruit_AM2320 am2320;

void setup() {
  Serial.begin(9600);  // USB debug
  SerialUART32_0.begin(9600, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

  Serial.println("ESP32 ready");
  am2320.begin();
}

void loop() {

  // Wait for command from Pi
  if (SerialUART32_0.available()) {

    String cmd = SerialUART32_0.readStringUntil('\n');
    cmd.trim();

    Serial.print("From Pi: ");
    Serial.println(cmd);

    if (cmd == "1") {

      float temp = am2320.readTemperature();
      float hum  = am2320.readHumidity();

      // ---- SEND RESPONSE BACK TO PI ----
      SerialUART32_0.println("OK");
      SerialUART32_0.print("TEMP:");
      SerialUART32_0.println(temp);
      SerialUART32_0.print("HUM:");
      SerialUART32_0.println(hum);
      SerialUART32_0.println("END");

      Serial.println("Data sent to Pi");
    }
    else {
      SerialUART32_0.println("ERR");
      
    }
    
  }
  \
}
