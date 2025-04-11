const int heaterPin = 5;     // PWM pin to MOSFET gate
const int maxPWM = 255;      // Max power level (0-255)
const int rampDelay = 50;   // Delay between steps (in milliseconds)

void setup() {
  pinMode(heaterPin, OUTPUT);
}

void loop() {
  // Ramp from 0 up to maxPWM
  for (int pwm = 0; pwm <= maxPWM; pwm++) {
    analogWrite(heaterPin, pwm);
    delay(rampDelay);  // Small delay between steps
  }

  // After ramping up, hold at maxPWM
  analogWrite(heaterPin, maxPWM);

  // Keep it running forever
  while (true);  // Stops the loop here
}