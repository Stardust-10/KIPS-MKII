// ESP32 TX and RX Pins
#define ESP32_TX_PIN 37   // ESP32 TX -> Pi RX
#define ESP32_RX_PIN 36   // ESP32 RX -> Pi TX

void setup() {
  Serial.begin(115200);           // Baud Rate
  delay(1000);
  Serial.println("Booting...");

  // UART to Raspberry Pi CM4
  Serial2.begin(115200, SERIAL_8N1, ESP32_RX_PIN, ESP32_TX_PIN);
  Serial.println("Serial2 (to Pi) started.");
}

void loop() {

  // Send a test message every second
  Serial2.println("Hello from ESP32!");
  Serial.println("Sent: Hello from ESP32!");
  delay(1000);

  // (Optional) Read anything the Pi sends back
  while (Serial2.available()) {
    int c = Serial2.read();
    Serial.print("From Pi: ");
    Serial.println((char)c);
  }
}