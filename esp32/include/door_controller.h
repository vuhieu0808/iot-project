#pragma once
#include <Arduino.h>
namespace DoorController {
void begin();
void update();
void handleCardScan(const String& cardId, const char* typ);
void handleMqttPayload(const byte* payload, unsigned int length);
}
