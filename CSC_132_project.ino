#include <WiFi.h>
#include <WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// —— Phone Hotspot credentials ——
const char* SSID = "Luke";    // ← replace with your hotspot’s SSID
const char* PASS = "Password";    // ← replace with your hotspot’s password

// —— Pins ——
#define ONE_WIRE_BUS 4
const int heaterPin = 5;

// —— OneWire + DS18B20 setup ——
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// —— HTTP server on port 80 ——
WebServer server(80);

// store a target temperature
float targetTemp = 0.0;

// —— Handlers ——  
void handleOn()  {
  digitalWrite(heaterPin, HIGH);
  server.send(200, "application/json", "{\"status\":\"on\"}");
}

void handleOff() {
  digitalWrite(heaterPin, LOW);
  server.send(200, "application/json", "{\"status\":\"off\"}");
}

void handleSet() {
  if (!server.hasArg("temp")) {
    server.send(400, "application/json", "{\"error\":\"missing temp\"}");
    return;
  }
  targetTemp = server.arg("temp").toFloat();
  server.send(200, "application/json",
              String("{\"target\":") + String(targetTemp, 1) + "}");
}

void handleTemp() {
  sensors.requestTemperatures();
  float tempF = sensors.getTempCByIndex(0) * 9.0 / 5.0 + 32.0;
  server.send(200, "application/json",
              String("{\"temp\":") + String(tempF, 1) + "}");
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  // Initialize heater pin
  pinMode(heaterPin, OUTPUT);
  digitalWrite(heaterPin, LOW);

  // Initialize DS18B20 sensor
  sensors.begin();
  Serial.println("DS18B20 initialized.");

  // 1) Scan for available Wi-Fi networks
  Serial.println("Scanning for Wi-Fi networks...");
  int n = WiFi.scanNetworks();
  if (n == 0) {
    Serial.println("  ► No networks found");
  } else {
    for (int i = 0; i < n; i++) {
      String auth;
      switch (WiFi.encryptionType(i)) {
        case WIFI_AUTH_OPEN:         auth = "[OPEN]";    break;
        case WIFI_AUTH_WEP:          auth = "[WEP]";     break;
        case WIFI_AUTH_WPA_PSK:      auth = "[WPA]";     break;
        case WIFI_AUTH_WPA2_PSK:     auth = "[WPA2]";    break;
        case WIFI_AUTH_WPA_WPA2_PSK: auth = "[WPA/WPA2]";break;
        default:                     auth = "[?]";       break;
      }
      Serial.printf("  ► %s (RSSI %d) %s\n",
                    WiFi.SSID(i).c_str(),
                    WiFi.RSSI(i),
                    auth.c_str());
      delay(10);
    }
  }
  Serial.println("End scan.\n");

  // 2) Attempt to connect to your hotspot
  Serial.printf("Connecting to SSID: '%s'\n", SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASS);

  unsigned long start = millis();
  const unsigned long timeout = 20000; // 20 seconds
  while (WiFi.status() != WL_CONNECTED && millis() - start < timeout) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("✅ Connected in %.2fs – IP: %s\n",
                  (millis() - start) / 1000.0,
                  WiFi.localIP().toString().c_str());
  } else {
    Serial.printf("❌ Failed after %.2fs, status=%d\n",
                  (millis() - start) / 1000.0,
                  WiFi.status());
  }

  // 3) Register HTTP routes
  server.on("/on",   HTTP_POST, handleOn);
  server.on("/off",  HTTP_POST, handleOff);
  server.on("/set",  HTTP_POST, handleSet);
  server.on("/temp", HTTP_GET,  handleTemp);

  // 4) Start the HTTP server
  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  server.handleClient();
}
