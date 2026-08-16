#include "environment_sensor.h"
#include <Arduino.h>
#include <DHTesp.h>
#include "hardware_config.h"
#include "mqtt_manager.h"

namespace {
constexpr char TOPIC[] = "gymtag/environment/reading";
constexpr unsigned long INTERVAL_MS = 5000;
DHTesp sensor;
unsigned long lastReadingAt = 0;
}

namespace EnvironmentSensor {
void begin() { sensor.setup(HardwareConfig::DHT_PIN, DHTesp::DHT22); }

void update() {
    const unsigned long now = millis();
    if (now - lastReadingAt < INTERVAL_MS) return;
    lastReadingAt = now;
    const TempAndHumidity reading = sensor.getTempAndHumidity();
    Serial.printf("Temperature: %.1f C, Humidity: %.1f %%\n", reading.temperature, reading.humidity);
    char payload[80];
    snprintf(payload, sizeof(payload), "{\"temperature\":%.1f,\"humidity\":%.1f}",
             reading.temperature, reading.humidity);
    MqttManager::publish(TOPIC, String(payload));
}
}
