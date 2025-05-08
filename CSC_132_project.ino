#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// Pin defs
#define ONE_WIRE_BUS 4
#define MOSFET_PIN   5

// Wi-Fi & Flask
const char* ssid      = "Luke";
const char* password  = "Password";
const char* flaskHost = "172.20.10.9";
const uint16_t flaskPort = 5000;

// Globals
WebServer server(80);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

float currentTemp = 0.0;
float targetTemp  = 60.0;
bool  isOn        = false;

void handleOn() { isOn = true;  server.send(200,"application/json","{\"status\":\"on\"}"); }
void handleOff(){ isOn = false; server.send(200,"application/json","{\"status\":\"off\"}"); }
void handleSet(){
  if(server.hasArg("target")){
    targetTemp = server.arg("target").toFloat();
    server.send(200,"application/json", String("{\"target\":") + targetTemp + "}");
  } else {
    server.send(400,"application/json","{\"error\":\"missing target\"}");
  }
}
void handleTemp(){
  sensors.requestTemperatures();
  float tC = sensors.getTempCByIndex(0);
  if(tC == DEVICE_DISCONNECTED_C){
    server.send(500,"application/json","{\"error\":\"sensor disconnected\"}");
  } else {
    float tF = sensors.toFahrenheit(tC);
    server.send(200,"application/json", String("{\"current\":") + tF + "}");
  }
}

void setup(){
  Serial.begin(115200);
  pinMode(MOSFET_PIN, OUTPUT);
  digitalWrite(MOSFET_PIN, LOW);
  sensors.begin();
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){ delay(500); Serial.print('.'); }
  Serial.println("\nWi-Fi connected: " + WiFi.localIP().toString());

  server.on("/on",  HTTP_GET, handleOn);
  server.on("/off", HTTP_GET, handleOff);
  server.on("/set", HTTP_GET, handleSet);
  server.on("/temp",HTTP_GET, handleTemp);
  server.begin();
  Serial.println("Control HTTP server started");
}

void loop(){
  server.handleClient();
  static unsigned long last=0;
  if(millis()-last<1000) return;
  last = millis();

  // Read sensor
  sensors.requestTemperatures();
  float tC = sensors.getTempCByIndex(0);
  if(tC == DEVICE_DISCONNECTED_C){
    Serial.println("⚠️  DS18B20 read failed");
    return; // skip MOSFET & POST until valid
  }
  currentTemp = sensors.toFahrenheit(tC);

  // Drive MOSFET
  bool gate = isOn && (currentTemp < targetTemp);
  digitalWrite(MOSFET_PIN, gate ? HIGH : LOW);

  // Push update to Flask
  if(WiFi.isConnected()){
    HTTPClient http;
    String url = String("http://") + flaskHost + ":" + flaskPort + "/api/heater/update";
    http.begin(url);
    http.addHeader("Content-Type","application/json");
    String body = String("{\"current\":") + String(currentTemp,1) + "}";
    int code = http.POST(body);
    Serial.printf("POST /update → %d\n", code);
    http.end();
  }
}
