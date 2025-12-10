#include <Wire.h>

// SI4735 I2C address
#define SI4735_ADDR 0x11  

// SI4735 commands
#define POWER_UP      0x01
#define FM_TUNE_FREQ  0x20
#define GET_REV       0x10

// ESP32 I2C pins
#define SDA_PIN 18
#define SCL_PIN 19

// ESP32 pin connected to SI4735 RST
#define RST_PIN 21

void setup() {
  Serial.begin(115200);
  delay(100);

  // Initialize I2C with custom pins
  Wire.begin(SDA_PIN, SCL_PIN);

  // Initialize RST pin
  pinMode(RST_PIN, OUTPUT);

  // Pulse RST HIGH → LOW for 2 ms
  Serial.println("Resetting SI4735...");
  digitalWrite(RST_PIN, HIGH);
  delay(2);                // 1–2 ms pulse
  digitalWrite(RST_PIN, LOW);
  delay(50);               // wait for chip to stabilize

  // Power up in FM mode (analog audio)
  Wire.beginTransmission(SI4735_ADDR);
  Wire.write(POWER_UP);    // Power Up command
  Wire.write(0x05);        // FM mode, analog audio
  Wire.write(0x00);        // CTS interrupt disabled
  Wire.endTransmission();
  delay(50);

  // Optional: get chip revision
  Wire.beginTransmission(SI4735_ADDR);
  Wire.write(GET_REV);
  Wire.endTransmission();
  delay(10);

  // Tune to 89.9 MHz
  uint16_t freq = 8990;    // SI4735 uses 10 kHz steps: 89.9 MHz = 8990
  Wire.beginTransmission(SI4735_ADDR);
  Wire.write(FM_TUNE_FREQ);
  Wire.write((freq >> 8) & 0xFF); // high byte
  Wire.write(freq & 0xFF);        // low byte
  Wire.write(0x00);               // antenna capacitance = 0
  Wire.endTransmission();

  Serial.println("Tuned to 89.9 MHz FM!");
}

void loop() {
  // Nothing required here for simple FM tuning
  // You can read status or implement scanning later
}
