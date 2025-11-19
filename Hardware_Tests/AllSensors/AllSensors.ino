
/*!
 * @file  heartrateAnalogMode.h
 * @brief  This is written for the heart rate sensor the company library. Mainly used for real 
 * @n  time measurement of blood oxygen saturation, based on measured values calculate heart rate values.
 * @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license  The MIT License (MIT)
 * @author  [linfeng](Musk.lin@dfrobot.com)
 * @maintainer  [qsjhyy](yihuan.huang@dfrobot.com)
 * @version  V1.0
 * @date  2022-04-26
 * @url  https://github.com/DFRobot/DFRobot_Heartrate
 */
#include "DFRobot_Heartrate.h"
#define HEARTRATE_PIN 4
#define SAMPLING 10

//Beat detection parameters
#define THRESHOLD 20
#define BASE_ALPHA 5 //Baseline smoothing (% per sample)

//Acceptable beat interval range (ms)
#define MIN_INTV 350 //~171 BPM upper bound
#define MAX_INTV 2000 //~30 BPM lower bound

int lastSample, lastBeat, baseline, bpm = 0;
bool above = false;


#include <Arduino.h>

// Define the pin where the LDR is connected (e.g., GPIO 34)
const int ldrPin = 5; 


#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"

Adafruit_AM2320 am2320 = Adafruit_AM2320();

void setup() {
  Serial.begin(115200);
  delay(1000);

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

}

void loop() {

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

  //Serial plotter output
  Serial.print(raw);
  Serial.print(" ");
  Serial.print(baseline);
  Serial.print(" ");
  Serial.print(diff);
  Serial.print(" ");
  Serial.println(bpm);

  delay(200);

    // Read the analog value from the LDR pin (value between 0 and 4095)
  int ldrValue = analogRead(ldrPin); 

  // Print the value to the Serial Monitor
  Serial.print("LDR Value: ");
  Serial.println(ldrValue); 

  // Add a small delay before the next reading
  delay(500); // Wait for 0.5 seconds

    Serial.print("Temp: "); Serial.println(am2320.readTemperature());
  Serial.print("Hum: "); Serial.println(am2320.readHumidity());

  delay(2000);

}