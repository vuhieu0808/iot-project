#include "DHTesp.h"
#include "PubSubClient.h"
#include <WiFi.h>
#include <ArduinoJson.h>

int DHT_PIN = 15;
int FAN_PIN = 12;

const char* ssid = "Wokwi-GUEST";
const char* pass = "";
const char* mqttServer = "test.mosquitto.org";
int port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

DHTesp dhtSensor;

void wifiConnect() {
  Serial.print("Attempting WiFi connection...");
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

void mqttReconnect() {
  while (!client.connected()) {
    Serial.println("Attempting MQTT connection...");
    if (client.connect("gymtag_backend_service_esp32")) {
      Serial.println("MQTT connected!");
      client.subscribe("gymtag/environment/fan_control");
    } else {
      Serial.println("Retrying...");
      delay(5000);
    }
  }
}

// Handle function
void hanldeFanControl(JsonDocument& doc) {
  bool fanState = doc["fan"] == "on";
  digitalWrite(FAN_PIN, fanState ? HIGH : LOW);
  Serial.printf("Fan state set to: %s\n", fanState ? "ON" : "OFF");
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.println(topic);
  String stMessage;
  for (int i = 0; i < length; i++) {
    stMessage += (char) message[i];
  }
  Serial.println(stMessage);

  // Parse JSON
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, stMessage);
  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc.containsKey("fan")) {
    hanldeFanControl(doc);
  }
}

void setup() {
  Serial.begin(115200);
  dhtSensor.setup(DHT_PIN, DHTesp::DHT22);
  
  // Fan
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(FAN_PIN, LOW);

  wifiConnect();
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqttServer, port);
  client.setCallback(callback);
}

unsigned long lastSend = 0;

void loop() {
  if (!client.connected()) {
    mqttReconnect();
  }
  client.loop();

  if (millis() - lastSend >= 5000) {
    lastSend = millis();

    char buffer[50];

    TempAndHumidity data = dhtSensor.getTempAndHumidity();
    Serial.printf("Temperature: %.1f °C, Humidity: %.1f %%\n", data.temperature, data.humidity);
    sprintf(buffer, "{\"temperature\":%s,\"humidity\":%s}", String(data.temperature), String(data.humidity));
    client.publish("gymtag/environment/reading", buffer);
  }
}
