#include <Arduino.h>
#include <HardwareSerial.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"
#include "DFRobot_Heartrate.h"
#include <Wire.h>

// ---------------- UART Setup ----------------
// UART 0: Communications with Pi (Commands/Sensors)
HardwareSerial SerialUART32_0(0); 
// UART 1: Communications with Pi (Joystick/Buttons)
HardwareSerial SerialUART32_1(1); 

// ---------------- Pins / Constants ----------------
#define UART_TX_PIN 43
#define UART_RX_PIN 44
#define Uart_RX2_pin 18
#define Uart_Tx2_pin 17
#define UART_BAUD 115200

// I2C Bus 1 Pins (Sensor 1)
#define tempsda 8
#define tempscl 9

// I2C Bus 2 Pins (Sensor 2)
#define SDA2 13
#define SCL2 14

#define JS_X 12
#define JS_Y 11
#define BTN_UP 40
#define BTN_DOWN 39
#define BTN_LEFT 38
#define BTN_RIGHT 41
#define BTN_ENTER 42

#define hbRatePin 4
#define hbPowerPin 10 
const int ldrPin = 1;

#define DEADZONE 800

unsigned long lastButtonTime = 0;
bool commandActive = false;

// ---------------- Sensor Objects ----------------
DFRobot_Heartrate heartrate(DIGITAL_MODE);
Adafruit_AM2320 am2320 = Adafruit_AM2320(); // Single object used for both buses

// ---------------- Helpers ----------------

void sendTempHum(int sda, int scl, String label) {
  // Dynamically re-assign I2C pins before reading
  Wire.begin(sda, scl); 
  
  // Re-init sensor on the current pins
  if (!am2320.begin()) {
    SerialUART32_0.println(label + "_ERR:NOT_FOUND");
    return;
  }

  float temp = NAN;
  float hum = NAN;

  // Attempt to read 3 times
  for (int i = 0; i < 3; i++) {
    temp = am2320.readTemperature();
    hum  = am2320.readHumidity();
    if (!isnan(temp) && !isnan(hum)) break;
    delay(200);
  }

  if (isnan(temp) || isnan(hum)) {
    SerialUART32_0.println(label + "_TEMP:ERR");
    SerialUART32_0.println(label + "_HUM:ERR");
  } else {
    SerialUART32_0.print(label + "_TEMP:");
    SerialUART32_0.println(temp, 2);
    SerialUART32_0.print(label + "_HUM:");
    SerialUART32_0.println(hum, 2);
  }
}

void sendLDR() {
  int ldr = analogRead(ldrPin);
  SerialUART32_0.print("LDR:");SDA2, SCL2, "S2");
  SerialUART32_0.println(ldr);
}

void sendHeartbeatSession() {
  digitalWrite(hbPowerPin, HIGH);
  SerialUART32_0.println("HB_START");
  
  unsigned long start = millis();
  while (millis() - start < 30000) { // 30 second session
    heartrate.getValue(hbRatePin);
    uint8_t rateValue = heartrate.getRate();
    if (rateValue) {
      SerialUART32_0.print("HB:");
      SerialUART32_0.println(rateValue);
    }
    delay(20);
  }
  
  SerialUART32_0.println("HB_END");
  digitalWrite(hbPowerPin, LOW);
}

void processPiCommand(String incoming) {
  incoming.trim();
  int command = incoming.toInt();

  switch (command) {
    case 1:
      sendTempHum(tempsda, tempscl, "S1");
      break;
    case 2:
      sendLDR();
      break;
    case 3:
      sendHeartbeatSession();
      break;
    case 4:
      sendTempHum(SDA2, SCL2, "S2");
      break;
    default:
      SerialUART32_0.println("CMD_UNKNOWN");
      break;
  }
}

// ---------------- Setup ------incoming----------
void setup() {
  // Local USB Debugging
  Serial.begin(115200);

  // Initialize UART0 (Pins 37/36)
  SerialUART32_0.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  
  // Initialize UART1 (Pins 18/17)
  SerialUART32_1.begin(UART_BAUD, SERIAL_8N1, Uart_RX2_pin, Uart_Tx2_pin);

  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_LEFT, INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_ENTER, INPUT_PULLUP);

  pinMode(hbPowerPin, OUTPUT);
  pinMode(hbRatePin, INPUT);
  digitalWrite(hbPowerPin, LOW);

  // Note: Wire.begin() is handled dynamically in sendTempHum()
  
  Serial.println("System Initialized.");
}

// ---------------- Main Loop ----------------
void loop() {
  // -------- PART 1: Check for Pi commands on UART 0 --------
  if (SerialUART32_0.available()) {
    commandActive = true;
    String incoming = SerialUART32_0.readStringUntil('\n');
    processPiCommand(incoming);
    commandActive = false;
  }
  /*
  // -------- PART 2: Joystick / Button Traffic on UART 1 --------
  // Suppress while a sensor command is running to ensure smooth execution
  if (!commandActive) {
    // Read Joystick
    int x = -(analogRead(JS_X) - 1930);
    int y =  (analogRead(JS_Y) - 1947);

    if (abs(x) > DEADZONE || abs(y) > DEADZONE) {
      SerialUART32_1.print("M,");
      SerialUART32_1.print(x);
      SerialUART32_1.print(",");
      SerialUART32_1.println(y);
    }

    // Read Buttons (Debounced via 200ms timer)
    if (millis() - lastButtonTime > 200) {
      if (digitalRead(BTN_UP) == LOW) {
        SerialUART32_1.println("UP");
        lastButtonTime = millis();
      }
      else if (digitalRead(BTN_DOWN) == LOW) {
        SerialUART32_1.println("DOWN");
        lastButtonTime = millis();
      }

      if (digitalRead(BTN_LEFT) == LOW) {
        SerialUART32_1.println("LEFT");
        lastButtonTime = millis();
      }
      else if (digitalRead(BTN_RIGHT) == LOW) {
        SerialUART32_1.println("RIGHT");
        lastButtonTime = millis();
      }

      if (digitalRead(BTN_ENTER) == LOW) {
        SerialUART32_1.println("ENTER");
        lastButtonTime = millis();
      }
    }
  }
  */
  delay(10);
}
