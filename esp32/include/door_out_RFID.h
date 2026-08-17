#pragma once
#include <Arduino.h>

namespace DoorOutRfid {
void begin();
bool readCard(String& cardId);
}
