#pragma once
#include <Arduino.h>

namespace HardwareConfig {
constexpr uint8_t DHT_PIN = 15;
constexpr uint8_t FAN_PIN = 12;
constexpr uint8_t RFID_LOCKER_SS_PIN = 21;
constexpr uint8_t RFID_DOOR_IN_SS_PIN = 22;
constexpr uint8_t RFID_DOOR_OUT_SS_PIN = 2;
constexpr uint8_t RFID_RST_PIN = 4;

constexpr size_t LOCKER_COUNT = 3;
constexpr uint8_t I2C_SDA_PIN = 22;
constexpr uint8_t I2C_SCL_PIN = 25;
constexpr uint8_t LCD_I2C_ADDRESS = 0x27;
constexpr uint8_t LOCKER_SERVO_PINS[] = {26, 27, 32};
constexpr uint8_t LOCKER_DOOR_SWITCH_PINS[] = {13, 14, 16};
constexpr uint8_t RELEASE_BUTTON_PIN = 33;

constexpr uint8_t DOOR_SERVO_PIN = 5;

constexpr int SERVO_LOCKED_ANGLE = 0;
constexpr int SERVO_UNLOCKED_ANGLE = 90;
constexpr int DOOR_SERVO_CLOSE_ANGLE = 90;
constexpr int DOOR_SERVO_OPEN_IN_ANGLE = 0;
constexpr int DOOR_SERVO_OPEN_OUT_ANGLE = 180;
constexpr int SERVO_MIN_PULSE_US = 500;
constexpr int SERVO_MAX_PULSE_US = 2400;
constexpr unsigned long BUTTON_DEBOUNCE_MS = 50;
constexpr unsigned long RFID_COOLDOWN_MS = 1000;
constexpr unsigned long BACKEND_TIMEOUT_MS = 8000;
constexpr unsigned long DOOR_ACTION_TIMEOUT_MS = 30000;
constexpr unsigned long DISPLAY_MESSAGE_MS = 4000;
constexpr unsigned long MAIN_DOOR_TIMEOUT_MS = 5000;
}  // namespace HardwareConfig
