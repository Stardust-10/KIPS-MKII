// ESP32 TX and RX Pins
#define ESP32_TX_PIN 37   // ESP32 TX (pin 37) -> Pi RX (pin 10)
#define ESP32_RX_PIN 36   // ESP32 RX (pin 36) -> Pi TX (pin 8)

#define ESP32_RTS_PIN 15 //ESP32 RTS (pin 15) -> Pi RTS (pin 11)
#define ESP32_CTS_PIN 16 //ESP32 CTS (pin 16) -> Pi CTS (pin 36)

void setup() {
  Serial.begin(115200);  // Baud Rate, Serial is also ESP32 -> Serial Monitor
  Serial.println("Serial for ESP32 started.");
  delay(1000);
  Serial.println("Booting...");

  // Tell Serial2 (CM4) which pins to use
  Serial2.setPins(ESP32_TX_PIN, ESP32_RX_PIN, ESP32_CTS_PIN, ESP32_RTS_PIN);
  Serial.println("Serial2 for Pi started.");

  //Start UART, baud + 8N1
  Serial2.begin(115200, SERIAL_8N1, ESP32_RX_PIN, ESP32_TX_PIN);
  Serial2.println("Serial2 for Pi started w/ RTS/CTS.");
}

void loop() {

  //SERIAL IS FROM ESP
  //SERIAL2 IS FROM CM4

  // Send a test message every second
  Serial.println("Sent from ESP32: Hello from ESP32 w/ RTS/CTS!");
  delay(5000);

  int c = Serial2.read();
  Serial2.print("Sent from Pi: Hello from Pi CM4! ");
  Serial2.println(c);
  delay(5000);
}