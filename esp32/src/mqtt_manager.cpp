#include "mqtt_manager.h"
#include <PubSubClient.h>
#include <WiFi.h>

namespace {
constexpr char WIFI_SSID[] = "Wokwi-GUEST";
constexpr char WIFI_PASSWORD[] = "";
constexpr char MQTT_HOST[] = "broker.hivemq.com";
constexpr uint16_t MQTT_PORT = 1883;
constexpr char FAN_TOPIC[] = "gymtag/environment/fan_control";
constexpr char LOCKER_TOPIC[] = "gymtag/locker/response";
constexpr unsigned long WIFI_RETRY_MS = 10000;
constexpr unsigned long MQTT_RETRY_MS = 5000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
MqttManager::MessageHandler messageHandler = nullptr;
unsigned long lastWifiAttempt = 0;
unsigned long lastMqttAttempt = 0;

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    if (messageHandler) messageHandler(topic, payload, length);
}

void startWifi(unsigned long now) {
    lastWifiAttempt = now;
    Serial.println("Connecting to Wi-Fi...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void connectMqtt(unsigned long now) {
    lastMqttAttempt = now;
    const uint64_t chipId = ESP.getEfuseMac();
    char clientId[40];
    snprintf(clientId, sizeof(clientId), "gymtag_locker_%04X%08X",
             static_cast<uint16_t>(chipId >> 32), static_cast<uint32_t>(chipId));
    if (!mqttClient.connect(clientId)) {
        Serial.printf("MQTT connection failed, state=%d\n", mqttClient.state());
        return;
    }
    mqttClient.subscribe(FAN_TOPIC, 0);
    mqttClient.subscribe(LOCKER_TOPIC, 0);
    Serial.printf("MQTT connected as %s.\n", clientId);
}
}  // namespace

namespace MqttManager {
void begin(MessageHandler handler) {
    messageHandler = handler;
    WiFi.mode(WIFI_STA);
    mqttClient.setServer(MQTT_HOST, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    startWifi(millis());
}

void update() {
    const unsigned long now = millis();
    if (WiFi.status() != WL_CONNECTED) {
        if (now - lastWifiAttempt >= WIFI_RETRY_MS) startWifi(now);
        return;
    }
    if (!mqttClient.connected()) {
        if (now - lastMqttAttempt >= MQTT_RETRY_MS) connectMqtt(now);
        return;
    }
    mqttClient.loop();
}

bool publish(const char* topic, const String& payload) {
    if (!mqttClient.connected()) {
        Serial.printf("MQTT publish skipped while disconnected: %s\n", topic);
        return false;
    }
    return mqttClient.publish(topic, payload.c_str(), false);
}

bool connected() { return mqttClient.connected(); }
}  // namespace MqttManager
