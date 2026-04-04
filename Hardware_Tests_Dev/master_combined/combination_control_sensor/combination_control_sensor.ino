#include <Arduino.h>
#include <HardwareSerial.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"
#include "DFRobot_Heartrate.h"
#include <Wire.h>

// ---------------- UART Setup ----------------
HardwareSerial SerialUART32_0(0); // UART0
HardwareSerial SerialUART32_1(1); // UART1 (unused for now)

// ---------------- Pins / Constants (DEVELOPMENT - on dev-boards) ----------------
#define UART_TX_PIN 43 
#define UART_RX_PIN 44 
#define UART_BAUD 115200

#define JS_X 6
#define JS_Y 7
#define BTN_UP 10
#define BTN_DOWN 11
#define BTN_LEFT 12
#define BTN_RIGHT 13
#define BTN_ENTER 46

#define hbRatePin 4 
#define hbPowerPin 16 
#define tempsda 3 
#define tempscl 8 

/////////////PRODUCTION///////////////////////////////////
/*
#define UART_TX_PIN 37 
#define UART_RX_PIN 36 
#define UART_BAUD 115200

#define JS_X 20
#define JS_Y 19
#define BTN_UP 33
#define BTN_DOWN 32
#define BTN_LEFT 31
#define BTN_RIGHT 34
#define BTN_ENTER 35

#define hbRatePin 4 
#define hbPowerPin 3
#define tempsda 12 
#define tempscl 17
// added for internal temp/hum
#define tempsda1 8
#define tempscl1 9

*/
/////////////////////////////////////////////////

const int ldrPin = 1;

#define DEADZONE 800

unsigned long lastButtonTime = 0;
bool commandActive = false;

// ---------------- Sensor Objects ----------------
DFRobot_Heartrate heartrate(DIGITAL_MODE);
Adafruit_AM2320 am2320 = Adafruit_AM2320();

// ---------------- Helper Functions ----------------

//Turns heartbeat sensor on or off
void sensorOn() {
  digitalWrite(hbPowerPin, HIGH);
  delay(1000);
}

void sensorOff() {
  digitalWrite(hbPowerPin, LOW);
}

//Takes temperature and humidity readings, then displays them.
void sendTempHum() {
  float temp = NAN;
  float hum = NAN;

  for (int i = 0; i < 3; i++) {
    temp = am2320.readTemperature();
    hum  = am2320.readHumidity();

    if (!isnan(temp) && !isnan(hum)) {
      break;
    }

    delay(200);
  }

  if (isnan(temp) || isnan(hum)) {
    SerialUART32_0.println("TEMP:ERR");
    SerialUART32_0.println("HUM:ERR");

    Serial.println("AM2320 read failed");
    return;
  }

  SerialUART32_0.print("TEMP:");
  SerialUART32_0.println(temp, 2);

  SerialUART32_0.print("HUM:");
  SerialUART32_0.println(hum, 2);

  Serial.print("TEMP: ");
  Serial.println(temp, 2);
  Serial.print("HUM: ");
  Serial.println(hum, 2);
}

//Takes LDR readings
void sendLDR() {
  int ldr = analogRead(ldrPin);

  SerialUART32_0.print("LDR:");
  SerialUART32_0.println(ldr);

  Serial.print("LDR: ");
  Serial.println(ldr);
}

//Attempts to read heartbeat by activating 
//the sensor for 30 seconds to take a reading 
void sendHeartbeatSession() {
  sensorOn();

  SerialUART32_0.println("HB_START");
  Serial.println("Heartbeat session started");

  unsigned long start = millis();

  while (millis() - start < 30000) {
    heartrate.getValue(hbRatePin);
    uint8_t rateValue = heartrate.getRate();

    if (rateValue) {
      SerialUART32_0.print("HB:");
      SerialUART32_0.println(rateValue);

      Serial.print("HB: ");
      Serial.println(rateValue);
    }

    delay(20);
  }

  SerialUART32_0.println("HB_END");
  Serial.println("Heartbeat session ended");

  sensorOff();
}

//Takes commands from the CM4 according 
//to user input and sends them to the appropriate sensor function 
void processPiCommand(String incoming) {
  incoming.trim();
  int command = incoming.toInt();

  Serial.print("Received command: ");
  Serial.println(command);

  switch (command) {
    case 1:
      sendTempHum();
      break;

    case 2:
      sendLDR();
      break;

    case 3:
      sendHeartbeatSession();
      break;

    case 4:
      // Right now this is the same as command 1.
      // Replace this later if you add a true internal-temp sensor.
      sendTempHum();
      break;

    default:
      Serial.print("Unknown command: ");
      Serial.println(incoming);
      break;
  }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);

  //Activate UART0 on ESP32
  SerialUART32_0.begin(UART_BAUD, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);

  //Setting up pullup resistors on buttons
  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_LEFT, INPUT_PULLUP);
  pinMode(BTN_RIGHT, INPUT_PULLUP);
  pinMode(BTN_ENTER, INPUT_PULLUP);

  //Setting up heartbeat sensor pins
  pinMode(hbPowerPin, OUTPUT);
  pinMode(hbRatePin, INPUT);

  sensorOff();

  //Temperature setup
  Wire.begin(tempsda, tempscl);

  if (!am2320.begin()) {
    Serial.println("AM2320 not detected!");
  } else {
    Serial.println("AM2320 ready.");
  }

  Serial.println("System Initialized.");
}

// ---------------- Main Loop ----------------
void loop() {
  
  // -------- PART 1: Check for Pi command first --------
  if (SerialUART32_0.available()) {
    commandActive = true;

    //Read an incoming string until a \n is seen, then send it to the processPiCommand function
    String incoming = SerialUART32_0.readStringUntil('\n');
    processPiCommand(incoming);

    commandActive = false;
  }

  // -------- PART 2: Joystick / button traffic --------
  // Suppress this while a command is being serviced so it does not pollute replies.
  if (!commandActive) {
    int x = -(analogRead(JS_X) - 1930);
    int y =  (analogRead(JS_Y) - 1947);

    //Make sure the cursor does not continued to be registered off screen.
    if (abs(x) > DEADZONE || abs(y) > DEADZONE) {
      SerialUART32_0.print("M,");
      SerialUART32_0.print(x);
      SerialUART32_0.print(",");
      SerialUART32_0.println(y);
    }

    //How to interpret button input, plus print if successfully registered
    if (millis() - lastButtonTime > 200) {
      if (digitalRead(BTN_UP) == LOW) {
        SerialUART32_0.println("UP");
        lastButtonTime = millis();
      }
      else if (digitalRead(BTN_DOWN) == LOW) {
        SerialUART32_0.println("DOWN");
        lastButtonTime = millis();
      }

      if (digitalRead(BTN_LEFT) == LOW) {
        SerialUART32_0.println("LEFT");
        lastButtonTime = millis();
      }
      else if (digitalRead(BTN_RIGHT) == LOW) {
        SerialUART32_0.println("RIGHT");
        lastButtonTime = millis();
      }

      if (digitalRead(BTN_ENTER) == LOW) {
        SerialUART32_0.println("ENTER");
        lastButtonTime = millis();
      }
    }
  }

  delay(10);
}
