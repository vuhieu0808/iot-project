#include <Arduino.h>

#include <cstring>

#include "display_controller.h"
#include "../include/lockerRFID.h"
#include "environment_sensor.h"
#include "fan_controller.h"
#include "locker_controller.h"
#include "mqtt_manager.h"

namespace {
constexpr char FAN_CONTROL_TOPIC[] = "gymtag/environment/fan_control";
constexpr char LOCKER_RESPONSE_TOPIC[] = "gymtag/locker/response";

void routeMqttMessage(const char* topic, const byte* payload, unsigned int length) {
    if (strcmp(topic, FAN_CONTROL_TOPIC) == 0) {
        FanController::handleMqttPayload(payload, length);
    } else if (strcmp(topic, LOCKER_RESPONSE_TOPIC) == 0) {
        LockerController::handleMqttPayload(payload, length);
    }
}
}  // namespace

void setup() {
    Serial.begin(115200);
    FanController::begin();
    EnvironmentSensor::begin();
    LockerRfid::begin();
    DisplayController::begin();
    LockerController::begin();
    MqttManager::begin(routeMqttMessage);
}

void loop() {
    MqttManager::update();
    EnvironmentSensor::update();

    String cardId;
    if (LockerRfid::readCard(cardId)) LockerController::handleCardScan(cardId);
    LockerController::update();
    DisplayController::update();
}
