#include <Arduino.h>
#include <Wire.h>
#include <SI4735.h>
#include <SparkFun_MAX1704x_Fuel_Gauge_Arduino_Library.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"
#include "DFRobot_Heartrate.h"

// ---------------- UART Config ----------------
#define UART_BAUD 115200
#define UART0_TX 43
#define UART0_RX 44
#define UART4_TX 17
#define UART4_RX 18

// ---------------- Radio & Audio Pins ----------------
#define RADIO_RESET_PIN 5
#define RADIO_SDA 7
#define RADIO_SCL 6
#define FM_FUNCTION 0
#define SPEAKER_EN 37     
#define HEADPHONE_EN 10
#define HEADPHONE_STATUS 35

// ---------------- Sensor Pins ----------------
#define S1_SDA 8
#define S1_SCL 9
#define S2_SDA 13
#define S2_SCL 14
#define hbRatePin 4
#define hbPowerPin 3   
const int ldrPin = 1;
#define PLUG_STATUS_PIN 48

// ---------------- Control Pins ----------------
#define JS_X 11
#define JS_Y 12
#define BTN_UP 40
#define BTN_DOWN 39
#define BTN_LEFT 38
#define BTN_RIGHT 41
#define BTN_ENTER 42
#define DEADZONE 800
#define BAT_SDA 47
#define BAT_SCL 21

// ---------------- Objects & State ----------------
Adafruit_AM2320 am2320 = Adafruit_AM2320();
DFRobot_Heartrate heartrate(DIGITAL_MODE);
SI4735 radio;
SFE_MAX1704X lipo(MAX1704X_MAX17049);

HardwareSerial serial0(0); // AMA0 - Sensors/Radio/Heartbeat/Battery
HardwareSerial serial4(1); // AMA4 - Real-time Controller

unsigned long lastButtonTime = 0;
bool currentModeFM = true;
bool lastJackState = -1;

// ---------------- Radio Helpers ----------------

bool isValidFrequency(uint16_t freq) {
  if (currentModeFM) return (freq >= 6400 && freq <= 10800); // 64.00 - 108.00 MHz
  return (freq >= 520 && freq <= 1710);                      // 520 - 1710 kHz
}

uint16_t getDefaultStep() {
  return currentModeFM ? 10 : 10; // FM = 0.10 MHz, AM = 10 kHz
}

void printRadioStatus() {
  radio.getStatus();
  radio.getCurrentReceivedSignalQuality();

  uint16_t freq = radio.getCurrentFrequency();

  serial0.print("RADIO_STATUS MODE=");
  serial0.print(currentModeFM ? "FM" : "AM");
  serial0.print(" FREQ=");

  if (currentModeFM) {
    serial0.print(String(freq / 100.0, 2));
    serial0.print(" UNIT=MHz");
  } else {
    serial0.print(freq);
    serial0.print(" UNIT=kHz");
  }

  serial0.print(" SNR=");
  serial0.print(radio.getCurrentSNR());
  serial0.print(" RSSI=");
  serial0.println(radio.getCurrentRSSI());
}

void tuneToFrequency(uint16_t freq) {
  if (!isValidFrequency(freq)) {
    serial0.println("RADIO_ERR INVALID_FREQ");
    return;
  }

  if (currentModeFM) {
    radio.setFM(8400, 10800, freq, 10);
  } else {
    radio.setAM(570, 1710, freq, 10);
  }

  serial0.print("RADIO_OK TUNE ");
  if (currentModeFM) {
    serial0.println(String(freq / 100.0, 2));
  } else {
    serial0.println(freq);
  }
}

void stepFrequency(int delta) {
  uint16_t current = radio.getCurrentFrequency();
  int32_t nextFreq = (int32_t)current + delta;

  if (currentModeFM) {
    if (nextFreq < 6400) nextFreq = 6400;
    if (nextFreq > 10800) nextFreq = 10800;
  } else {
    if (nextFreq < 520) nextFreq = 520;
    if (nextFreq > 1710) nextFreq = 1710;
  }

  tuneToFrequency((uint16_t)nextFreq);
}

void handleRadioCommand(String cmdLine) {
  cmdLine.trim();
  if (cmdLine.length() == 0) {
    serial0.println("RADIO_ERR EMPTY");
    return;
  }

  int spaceIndex = cmdLine.indexOf(' ');
  String cmd = (spaceIndex != -1) ? cmdLine.substring(0, spaceIndex) : cmdLine;
  String arg = (spaceIndex != -1) ? cmdLine.substring(spaceIndex + 1) : "";

  cmd.trim();
  arg.trim();
  cmd.toUpperCase();
  arg.toUpperCase();

  if (cmd == "VOLUP") {
    radio.volumeUp();
    serial0.println("RADIO_OK VOLUP");
  }
  else if (cmd == "VOLDN") {
    radio.volumeDown();
    serial0.println("RADIO_OK VOLDN");
  }
  else if (cmd == "MODE") {
    if (arg == "FM") {
      currentModeFM = true;
      radio.setFM(8400, 10800, 8990, 10);
      radio.setFmNoiseBlankThreshold(5);
      serial0.println("RADIO_OK MODE FM");
      printRadioStatus();
    }
    else if (arg == "AM") {
      currentModeFM = false;
      radio.setAM(570, 1710, 810, 10);
      serial0.println("RADIO_OK MODE AM");
      printRadioStatus();
    }
    else {
      serial0.println("RADIO_ERR BAD_MODE");
    }
  }
  else if (cmd == "TUNE") {
    if (arg.length() == 0) {
      serial0.println("RADIO_ERR NO_FREQ");
      return;
    }

    uint16_t freq = (uint16_t)arg.toInt();
    if (freq == 0) {
      serial0.println("RADIO_ERR BAD_FREQ");
      return;
    }

    tuneToFrequency(freq);
    printRadioStatus();
  }
  else if (cmd == "STEPUP") {
    uint16_t step = (arg.length() > 0) ? (uint16_t)arg.toInt() : getDefaultStep();
    if (step == 0) step = getDefaultStep();
    stepFrequency(step);
    printRadioStatus();
  }
  else if (cmd == "STEPDN") {
    uint16_t step = (arg.length() > 0) ? (uint16_t)arg.toInt() : getDefaultStep();
    if (step == 0) step = getDefaultStep();
    stepFrequency(-((int)step));
    printRadioStatus();
  }
  else if (cmd == "SEEKUP") {
    radio.seekStationUp();
    serial0.println("RADIO_OK SEEKUP");
    printRadioStatus();
  }
  else if (cmd == "SEEKDN") {
    radio.seekStationDown();
    serial0.println("RADIO_OK SEEKDN");
    printRadioStatus();
  }
  else if (cmd == "STATUS") {
    printRadioStatus();
  }
  else if (cmd == "HELP") {
    serial0.println("RADIO_OK CMDS MODE,TUNE,STEPUP,STEPDN,SEEKUP,SEEKDN,VOLUP,VOLDN,STATUS");
  }
  else {
    serial0.println("RADIO_ERR UNKNOWN_CMD");
  }
}
// ---------------- Sensor Helpers ----------------

void readAM2320(int sda, int scl, String label) {
  Wire.end(); delay(10);
  Wire.begin(sda, scl);
  delay(50); 
  bool success = false;
  for (int i = 0; i < 3; i++) {
    Wire.beginTransmission(0x5C); Wire.endTransmission();
    delay(20); 
    if (am2320.begin()) {
      float t = am2320.readTemperature();
      float h = am2320.readHumidity();
      if (!isnan(t) && !isnan(h)) {
        serial0.printf("%s_TEMP:%.2f\n%s_HUM:%.2f\n", label.c_str(), t, label.c_str(), h);
        success = true; break;
      }
    }
    delay(100); 
  }
  if (!success) serial0.println(label + "_ERR");
}

void runHeartbeat() {
  serial0.println("HB_START");
  digitalWrite(hbPowerPin, HIGH);
  unsigned long start = millis();
  while (millis() - start < 20000) { 
    heartrate.getValue(hbRatePin);
    uint8_t rate = heartrate.getRate();
    if (rate) { serial0.printf("HB:%d\n", rate); }
    delay(20);
  }
  digitalWrite(hbPowerPin, LOW); 
  serial0.println("HB_END");
}

// ---------------- Main ----------------
void setup() {
  Serial.begin(115200);
  serial0.begin(UART_BAUD, SERIAL_8N1, UART0_RX, UART0_TX);
  serial4.begin(UART_BAUD, SERIAL_8N1, UART4_RX, UART4_TX);

  serial0.println("SETUP_A");

  pinMode(RADIO_RESET_PIN, OUTPUT);
  digitalWrite(RADIO_RESET_PIN, HIGH);
  pinMode(hbPowerPin, OUTPUT);
  pinMode(hbRatePin, INPUT);
  // Configure output pins
  pinMode(SPEAKER_EN, OUTPUT);
  pinMode(HEADPHONE_EN, OUTPUT);

  // Configure status pin as input
  // Note: Pin 36 (VP) on ESP32 does not have internal pull-ups
  pinMode(HEADPHONE_STATUS, INPUT);


  serial0.println("SETUP_B");

  Wire.begin(BAT_SDA, BAT_SCL);
  delay(50);

  if (!lipo.begin()) {
    serial0.println("BAT_FAIL");
  } else {
    lipo.quickStart();
    lipo.setThreshold(20);
    serial0.println("BAT_OK");
  }

  serial0.println("SETUP_C");

  Wire.end();
  delay(10);

  serial0.println("SETUP_D");

  Wire.begin(RADIO_SDA, RADIO_SCL);
  delay(20);

  serial0.println("SETUP_E");

  // radio.setup(RADIO_RESET_PIN, 0);
  // radio.setVolume(45);

  serial0.println("RADIO_SKIPPED");
  // Initial Plug and Audio Status
  lastJackState = digitalRead(HEADPHONE_STATUS);
  serial0.printf("INIT_JACK:%s\n", lastJackState == LOW ? "SPEAKER" : "PHONES");
  serial0.println("SETUP_G");
}

  

void loop() {
  // 1. Audio Auto-Switcher (Fixed logic)
  bool currentJackEmpty = digitalRead(HEADPHONE_STATUS);
  if (currentJackEmpty == LOW) {
    digitalWrite(SPEAKER_EN, LOW);
    digitalWrite(HEADPHONE_EN, HIGH);
  } else {
    digitalWrite(SPEAKER_EN, HIGH);
    digitalWrite(HEADPHONE_EN, LOW);
  }

  // Report Audio Change Event
  if (currentJackEmpty != lastJackState) {
    serial0.printf("EVENT_AUDIO:%s\n", currentJackEmpty == LOW ? "SPEAKER" : "PHONES");
    lastJackState = currentJackEmpty;
  }
 
  // --- 2. CONTROLS (AMA4) ---
  int x = -(analogRead(JS_X) - 1930);
  int y = (analogRead(JS_Y) - 1900);

  delay(10);

  if (abs(x) > DEADZONE || abs(y) > DEADZONE) { serial4.printf("M,%d,%d\n", x, y); }

  if (millis() - lastButtonTime > 200) {
    if      (digitalRead(BTN_UP) == LOW)    { serial4.println("UP");    lastButtonTime = millis(); }
    else if (digitalRead(BTN_DOWN) == LOW)  { serial4.println("DOWN");  lastButtonTime = millis(); }
    else if (digitalRead(BTN_LEFT) == LOW)  { serial4.println("LEFT");  lastButtonTime = millis(); }
    else if (digitalRead(BTN_RIGHT) == LOW) { serial4.println("RIGHT"); lastButtonTime = millis(); }
    else if (digitalRead(BTN_ENTER) == LOW) { serial4.println("ENTER"); lastButtonTime = millis(); }
  }

  // --- 3. SENSORS, RADIO & POWER (AMA0) ---
  if (serial0.available()) {
    String incoming = serial0.readStringUntil('\n');
    incoming.trim();

    if (incoming == "RADIO") {
      Wire.end(); delay(10); // Reset for Radio pins 
      Wire.begin(RADIO_SDA, RADIO_SCL);
      delay(20);
      unsigned long entry = millis();
      while (millis() - entry < 1500) { 
        if (serial0.available()) {
          handleRadioCommand(serial0.readStringUntil('\n'));
          break;
        }
      }
    } 
    else {
      int cmd = incoming.toInt();
      switch (cmd) {
        case 1: readAM2320(S1_SDA, S1_SCL, "S1"); break;
        case 2: readAM2320(S2_SDA, S2_SCL, "S2"); break;
        case 3: runHeartbeat(); break;
        case 4: serial0.printf("LDR:%d\n", analogRead(ldrPin)); break;
        case 5: // Battery Status
          Wire.end(); delay(10);
          Wire.begin(BAT_SDA, BAT_SCL);
          delay(50);
          // Don't call lipo.begin() here, just read values
          serial0.printf("BAT_V:%.3f\n", lipo.getVoltage());
          serial0.printf("BAT_P:%.1f\n", lipo.getSOC());
          break;
        case 6: // Plug Status
          int plugState = digitalRead(PLUG_STATUS_PIN);
          serial0.printf("PLUG_STAT:%d\n", plugState);
          break;
      }
    }
  }
  delay(5);
}
