// Example for DS18B20 on pin 2; adapt if you use a different sensor
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_PIN 2
OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);
  sensors.begin();
}

void loop() {
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  float tempF = tempC * 9.0 / 5.0 + 32.0;
  Serial.println(tempF, 1);   // e.g. "72.5"
  delay(1000);
}
