#define JS_X 6
#define JS_Y 7
#define JS_Z 3


  int x = 0;

  int y = 0;

void setup() {

  Serial.begin(115200);
  pinMode(JS_Z, INPUT_PULLUP);

}

void loop() {


  x = analogRead(JS_X) -1930;
  y = analogRead(JS_Y ) -1947;

  x= -x;
  y = -y;
  //z = digitalRead(JS_Z);

  Serial.print("X analog read: ");
  Serial.print(x);
  Serial.print("\n\n");
  
  Serial.print("Y analog read: ");
  Serial.print(y, DEC);
  Serial.print("\n\n");


  delay(2000);

}
