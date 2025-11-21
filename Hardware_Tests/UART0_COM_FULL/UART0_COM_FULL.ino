#include <DFRobot_Heartrate.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_AM2320.h>
#include <Arduino.h>
#include <HardwareSerial.h>

//DEFINITIONS
// ======================================================== //
#define HEARTRATE_PIN 4
#define SAMPLING 10

//Beat detection parameters
#define THRESHOLD 20
#define BASE_ALPHA 5 //Baseline smoothing (% per sample)

//Acceptable beat interval range (ms)
#define MIN_INTV 350 //~171 BPM upper bound
#define MAX_INTV 2000 //~30 BPM lower bound

Adafruit_AM2320 am2320 = Adafruit_AM2320();

int lastSample, lastBeat, baseline, bpm = 0;
bool above = false;

// Define the pin where the LDR is connected (e.g., GPIO 34)
const int ldrPin = 5; 

HardwareSerial SerialUART32_0(0); //UART0
HardwareSerial SerialUART32_1(1); //UART1

#define UART_TX_PIN 43 //GPIO UART transmit pin
#define UART_RX_PIN 44 //GPIO UART recieve pin
// ======================================================== //

void setup() {

  //Serial Monitor Initialization
  Serial.begin(115200);
  delay(5000);

  Serial.println("Beginning ESP32-S3 -> CM4 UART with sensors test.");
  
  //UART0 initialization 
  SerialUART32_0.begin(115200, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  delay(5000);
  Serial.println("UART0 initialized on TX = 43, and RX = 44 @ 115200 baud."); 

  //Heartbeat Monitor Initialization
  // ======================================================== //
  analogReadResolution(12); //0-4095 on the ESP32
  analogSetPinAttenuation(HEARTRATE_PIN, ADC_11db);

  //Take samples to initialize a baseline
  long sum = 0;
  const int N = 200;
  
  for (int i = 0; i < N; i++) {
    sum += analogRead(HEARTRATE_PIN);
    delay(5);
  } 

  baseline = sum / N;
  
  // Set the pin mode (though analogRead works without explicit pinMode for ADC pins)
  pinMode(ldrPin, INPUT);
  am2320.begin();
  // ======================================================== //

}

void loop() {

  //Heartbeat Monitor Readings and Calculations (Analog)
  //NOTE: Currently does not work beyond printing. Will always print a BPM of zero even when against skin
  // ======================================================== //
  unsigned long now = millis();

  if(now - lastSample < SAMPLING) {
    return; //Wait until the next sample time
  }

  lastSample = now;

  int raw = analogRead(HEARTRATE_PIN);

  //Exponential moving average for baseline
  baseline = (BASE_ALPHA * raw + (100 - BASE_ALPHA) * baseline) / 100;

  int diff = raw - baseline; //Will be positive when above baseline

  //Peak detection
  //If it crosses ABOVE the threshold, its a "beat"
  if(!above && diff > THRESHOLD) {
    above = true;

    if(lastBeat != 0) {
      unsigned long interval = now - lastBeat;

      if(interval > MIN_INTV && interval < MAX_INTV) {
        bpm = 60000 / interval;
      }
    }
    lastBeat = now;
  }

  if(above && diff < 0) {
    
    //if it falls back below the baseline -> end of beat window
    above = false;
  
  }
  // ======================================================== //

  //Heartbeat Monitor Terminal Print Outs
  // ======================================================== //
  SerialUART32_0.printf("Raw: %d", raw);
  SerialUART32_0.println(" ");
  SerialUART32_0.printf("Baseline: %d", baseline);
  SerialUART32_0.println(" ");
  SerialUART32_0.printf("Difference: %d", diff);
  SerialUART32_0.println(" ");
  SerialUART32_0.printf("BPM: %d", bpm);
  SerialUART32_0.println(" ");


  Serial.printf("Raw: %d", raw);
  Serial.println(" ");
  Serial.printf("Baseline: %d", baseline);
  Serial.println(" ");
  Serial.printf("Difference: %d", diff);
  Serial.println(" ");
  Serial.printf("BPM: %d", bpm);
  Serial.println(" ");

  // ======================================================== //

  delay(200);

  //LDR Readings and Terminal Output
  // ======================================================== //
  int ldrValue = analogRead(ldrPin); 
  SerialUART32_0.println(" ");

  SerialUART32_0.printf("LDR Value: %d", ldrValue);
  SerialUART32_0.println(" ");
  // ======================================================== //

  delay(500); // Wait for 0.5 seconds

  //Temp and Humidity Readings and Terminal Output
  // ======================================================== //
  SerialUART32_0.printf("Temp: %.2f", am2320.readTemperature()); 
  SerialUART32_0.println(" ");
  //SerialUART32_0.println(am2320.readTemperature());
  SerialUART32_0.printf("Hum: %.2f", am2320.readHumidity());
  SerialUART32_0.println(" ");
  //SerialUART32_0.println(am2320.readHumidity()); 
  // ======================================================== //

  delay(2000);

}
