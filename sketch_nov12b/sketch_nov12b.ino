#include <Arduino.h>

// Define the pin where the LDR is connected (e.g., GPIO 34)
const int ldrPin = 4; 

void setup() {

  // Initialize serial communication at a baud rate of 115200
  Serial.begin(9600);

  // Set the pin mode (though analogRead works without explicit pinMode for ADC pins)
  pinMode(ldrPin, INPUT);
}

void loop() {
  // Read the analog value from the LDR pin (value between 0 and 4095)
  int ldrValue = analogRead(ldrPin); 

  // Print the value to the Serial Monitor
  Serial.print("LDR Value: ");
  Serial.println(ldrValue); 

  // Add a small delay before the next reading
  delay(500); // Wait for 0.5 seconds
}
