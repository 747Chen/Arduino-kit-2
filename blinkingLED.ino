//int pin = 13; //io13/D7
int pin = 9;  //io9/D5

void setup() {
  // put your setup code here, to run once:
pinMode(pin, OUTPUT);

}

void loop() {
  // put your main code here, to run repeatedly:
digitalWrite(pin, HIGH);
delay(100)
digitalWrite(pin, LOW);
delay(100)
}
