#include "fan_controller.h"
#include <ArduinoJson.h>
#include "hardware_config.h"

namespace FanController {
void begin() {
    pinMode(HardwareConfig::FAN_PIN, OUTPUT);
    digitalWrite(HardwareConfig::FAN_PIN, LOW);
}

void handleMqttPayload(const byte* payload, unsigned int length) {
    JsonDocument document;
    const DeserializationError error = deserializeJson(document, payload, length);
    if (error) {
        Serial.printf("Invalid fan JSON: %s\n", error.c_str());
        return;
    }
    const char* command = document["fan"] | "";
    if (strcmp(command, "on") != 0 && strcmp(command, "off") != 0) {
        Serial.println("Invalid fan command.");
        return;
    }
    const bool fanOn = strcmp(command, "on") == 0;
    digitalWrite(HardwareConfig::FAN_PIN, fanOn ? HIGH : LOW);
    Serial.printf("Fan state set to: %s\n", fanOn ? "ON" : "OFF");
}
}
