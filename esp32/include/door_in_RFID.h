#pragma once
#include <Arduino.h>

namespace DoorInRfid {
void begin();
bool readCard(String& cardId);
}
