const int heaterPin = 5;     // PWM pin to MOSFET gate
const int maxPWM = 255;      // Max power level (0-255)
const int rampDelay = 50;   // Delay between steps (in milliseconds)

const int heaterPin = 9;  // digital pin to MOSFET gate

void setup() {
  pinMode(heaterPin, OUTPUT);
  digitalWrite(heaterPin, LOW);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '1') {
      digitalWrite(heaterPin, HIGH);  // Heater ON
    }
    else if (cmd == '0') {
      digitalWrite(heaterPin, LOW);   // Heater OFF
    }
  }
}
