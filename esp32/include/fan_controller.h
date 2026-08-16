#pragma once
#include <Arduino.h>
namespace FanController {
void begin();
void handleMqttPayload(const byte* payload, unsigned int length);
}
