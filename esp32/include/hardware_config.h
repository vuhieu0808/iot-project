#pragma once
#include <Arduino.h>

namespace HardwareConfig {
constexpr uint8_t DHT_PIN = 15;
constexpr uint8_t FAN_PIN = 12;
constexpr uint8_t RFID_SS_PIN = 21;
constexpr uint8_t RFID_RST_PIN = 4;

constexpr uint8_t LOCKER_SERVO_PINS[] = {25, 26, 27, 32};
constexpr uint8_t LOCKER_DOOR_SWITCH_PINS[] = {13, 14, 16, 17};
constexpr size_t LOCKER_COUNT = 4;
constexpr uint8_t RELEASE_BUTTON_PIN = 33;

constexpr int SERVO_LOCKED_ANGLE = 0;
constexpr int SERVO_UNLOCKED_ANGLE = 90;
constexpr int SERVO_MIN_PULSE_US = 500;
constexpr int SERVO_MAX_PULSE_US = 2400;
constexpr unsigned long BUTTON_DEBOUNCE_MS = 50;
constexpr unsigned long RFID_COOLDOWN_MS = 5000;
constexpr unsigned long BACKEND_TIMEOUT_MS = 8000;
constexpr unsigned long DOOR_ACTION_TIMEOUT_MS = 30000;
}  // namespace HardwareConfig
