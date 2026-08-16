#pragma once
#include <Arduino.h>
namespace LockerController {
void begin();
void update();
void handleCardScan(const String& cardId);
void handleMqttPayload(const byte* payload, unsigned int length);
}
