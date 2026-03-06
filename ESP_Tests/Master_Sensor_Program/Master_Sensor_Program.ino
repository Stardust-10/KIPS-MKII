#include <Arduino.h>
#include <HardwareSerial.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"
#include <Wire.h>


// ======================================================== //

// UART Variable Setup
HardwareSerial SerialUART32_0(0); // UART0
HardwareSerial SerialUART32_1(1); // UART1

const int ldrPin = 5;

#define UART_TX_PIN 43
#define UART_RX_PIN 44

// ======================================================== //

Adafruit_AM2320 am2320 = Adafruit_AM2320();

void setup() {

  // USB Serial Monitor output setuhump
  Serial.begin(115200);
  delay(2000);
  Serial.println("Beginning ESP32-S3 UART + AM2320 test.");

  //Pin for LDR
  // Set the pin mode (though analogRead works without explicit pinMode for ADC pins)
  pinMode(ldrPin, INPUT);

  // UART0 to Raspberry Pi
  SerialUART32_0.begin(112500, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(1000);

  Serial.println("UART0 initialized on TX=43 RX=44 @ 112500");
  am2320.begin();

  // Temp + Humidity Sensor detection check
  if (!am2320.begin()) {
    Serial.println("AM2320 not detected!");
  } 
  
  else {
    Serial.println("AM230 ready.");
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

    //If integer 1 recieved from CM4,
    //ESP signals sensor to send readings
    //then prints results to serial monitor + UART print 
    if (command == 1) {
      float temp = am2320.readTemperature();
      float hum  = am2320.readHumidity();

      //Send sensor data ONCE
      //Prints over UART
      SerialUART32_0.print("TEMP:");
      SerialUART32_0.println(temp);

      SerialUART32_0.print("HUM:");
      SerialUART32_0.println(hum);

      //Prints to serial monitor
      Serial.println("Sensor data sent once.");
      Serial.print("Temp: "); Serial.println(temp);
      Serial.print("Hum: "); Serial.println(hum);

      delay(2000);
    }

    //If integer 2 is recieved from CM4
    //Sends back LDR value (LUX)
    else if(command == 2) {
      
      int ldr = analogRead(ldrPin);
      
      //Print to UART first
      SerialUART32_0.print("LDR: ");
      SerialUART32_0.println(ldr);

      //Then serial monitor
      Serial.print("LDR: "); Serial.println(ldr);

      delay(2000);
    }

    //For heartbeat monitor
    else if (command == 3) {

    }
    
    else {
      SerialUART32_0.println("ERR:UNKNOWN_CMD");
      delay(20000);
    }
  }
}
