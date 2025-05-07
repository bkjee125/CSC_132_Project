#include <WiFi.h>
#include <WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// —— Wi-Fi credentials ——
const char* SSID = "YOUR_SSID";
const char* PASS = "YOUR_PASSWORD";

// —— Pins ——
#define ONE_WIRE_BUS 2
const int heaterPin = 5;

// —— OneWire + DS18B20 setup ——
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// —— HTTP server on port 80 ——
WebServer server(80);

// (Optional) store a target temperature
float targetTemp = 0.0;

// —— Handlers ——

// Turn heater ON
void handleOn() {
  digitalWrite(heaterPin, HIGH);
  server.send(200, "application/json", "{\"status\":\"on\"}");
}

// Turn heater OFF
void handleOff() {
  digitalWrite(heaterPin, LOW);
  server.send(200, "application/json", "{\"status\":\"off\"}");
}

// Set target temperature via query string: /set?temp=72.5
void handleSet() {
  if (!server.hasArg("temp")) {
    server.send(400, "application/json", "{\"error\":\"missing temp\"}");
    return;
  }
  targetTemp = server.arg("temp").toFloat();
  // You can now use targetTemp in your control logic
  String resp = String("{\"target\":") + String(targetTemp,1) + "}";
  server.send(200, "application/json", resp);
}

// Read and return current temperature
void handleTemp() {
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  float tempF = tempC * 9.0 / 5.0 + 32.0;
  String resp = String("{\"temp\":") + String(tempF,1) + "}";
  server.send(200, "application/json", resp);
}

void setup() {
  Serial.begin(115200);
  pinMode(heaterPin, OUTPUT);
  digitalWrite(heaterPin, LOW);

  // Start DS18B20
  sensors.begin();
  Serial.println("DS18B20 initialized.");

  // Connect to Wi-Fi
  WiFi.begin(SSID, PASS);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Setup HTTP routes
  server.on("/on",  HTTP_POST, handleOn);
  server.on("/off", HTTP_POST, handleOff);
  server.on("/set", HTTP_POST, handleSet);
  server.on("/temp", HTTP_GET, handleTemp);

  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}
