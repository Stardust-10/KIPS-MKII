#define JS_X 5
#define JS_Y 4
#define JS_Z 3

void setup() {

  Serial.begin(115200);
  pinMode(JS_Z, INPUT_PULLUP);

}

void loop() {
  int x, y, z;

  x = analogRead(JS_X);
  y = analogRead(JS_Y);
  z = digitalRead(JS_Z);

  Serial.print("X analog read: ");
  Serial.print(x);
  Serial.print("\n\n");
  
  Serial.print("Y analog read: ");
  Serial.print(y, DEC);
  Serial.print("\n\n");

  Serial.print("Z analog read: ");
  Serial.print(z, DEC);
  Serial.print("\n\n");

  delay(2000);

}
