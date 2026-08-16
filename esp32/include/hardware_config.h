#pragma once
#include <Arduino.h>

namespace HardwareConfig {
constexpr uint8_t DHT_PIN = 15;
constexpr uint8_t FAN_PIN = 12;
constexpr uint8_t RFID_SS_PIN = 21;
constexpr uint8_t RFID_RST_PIN = 4;

// Relay and release-button wiring is not defined in the repository.
// Disabled defaults prevent accidental activation of unknown GPIOs.
constexpr int8_t RELEASE_BUTTON_PIN = -1;
constexpr uint8_t LOCKER_RELAY_PINS[] = {0};
constexpr size_t LOCKER_RELAY_COUNT = 0;
constexpr bool LOCKER_RELAY_ACTIVE_HIGH = true;

constexpr unsigned long RELAY_PULSE_MS = 1000;
constexpr unsigned long BUTTON_DEBOUNCE_MS = 50;
constexpr unsigned long RFID_COOLDOWN_MS = 5000;
constexpr unsigned long BACKEND_TIMEOUT_MS = 8000;
constexpr unsigned long MEMBER_SESSION_TIMEOUT_MS = 30000;
}  // namespace HardwareConfig
