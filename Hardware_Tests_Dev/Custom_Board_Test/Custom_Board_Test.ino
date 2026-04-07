#define UART_TX_PIN 37 

void setup() {

  digitalWrite(UART_TX_PIN, LOW);

  Serial.begin(115200);
  delay(5000);
  Serial.println("Test start.");

}
void loop() {
  delay(1000);
  Serial.println("alive");
}