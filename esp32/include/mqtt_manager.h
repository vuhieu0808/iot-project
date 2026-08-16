#pragma once
#include <Arduino.h>

namespace MqttManager {
using MessageHandler = void (*)(const char*, const byte*, unsigned int);
void begin(MessageHandler handler);
void update();
bool publish(const char* topic, const String& payload);
bool connected();
}  // namespace MqttManager
