#pragma once
#include <Arduino.h>

namespace LockerRfid {
void begin();
bool readCard(String& cardId);
}
