#pragma once

#include <Arduino.h>

namespace DisplayController {
void begin();
void update();
void showIdle();
void showAssigned(const String& memberName, int lockerNumber);
void showAuthorized(const String& memberName);
void showDenied();
void showReleased();
}  // namespace DisplayController
