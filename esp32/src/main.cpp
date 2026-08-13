#include "DHTesp.h"
#include "PubSubClient.h"
#include <WiFi.h>

int DHT_PIN = 15;

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
    if (client.connect("24127xxx")) {
      Serial.println("MQTT connected!");
      client.subscribe("esp32/messageIn");
    } else {
      Serial.println("Retrying...");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.println(topic);
  String stMessage;
  for (int i = 0; i < length; i++) {
    stMessage += (char) message[i];
  }
  Serial.println(stMessage);
}

void setup() {
  Serial.begin(115200);
  dhtSensor.setup(DHT_PIN, DHTesp::DHT22);

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

  if (millis() - lastSend >= 1000) {
    lastSend = millis();

    char buffer[50];

    TempAndHumidity data = dhtSensor.getTempAndHumidity();
    sprintf(buffer, "{\"temperature\":%s,\"humidity\":%s}", String(data.temperature), String(data.humidity));
    client.publish("esp32/TempAndHumidity", buffer);
  }
}
