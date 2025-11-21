#include <Arduino.h>
#include <HardwareSerial.h>

// ======================================================== //
HardwareSerial SerialUART32_0(0); //UART0
HardwareSerial SerialUART32_1(1); //UART1

#define UART_TX_PIN 43 //GPIO UART transmit pin
#define UART_RX_PIN 44 //GPIO UART recieve pin
// ======================================================== //

void setup() {

  //Serial Monitor Initialization
  Serial.begin(115200);
  delay(5000);
  Serial.println("Beginning ESP32-S3 UART test.");
  
  //UART0 initialization 
  SerialUART32_0.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(5000);
  Serial.println("UART0 initialized on TX = 43, and RX = 44 @ 115200 baud."); 

}

void loop() {

  //Print from UART0 in ESP32
  SerialUART32_0.println("Hello from UARTSerial0 in ESP32!");
  delay(5000);

  Serial.println("Hello message sent on UART0.");
  
  // Check if Pi sent anything
  while (SerialUART32_0.available()) {
      String incoming = SerialUART32_0.readStringUntil('\n');
      Serial.print("From Pi: ");
      Serial.println(incoming);
}
}
