#include <Arduino.h>

#include <cstring>

#include "../include/lockerRFID.h"
#include "../include/door_in_RFID.h"
#include "../include/door_out_RFID.h"
#include "environment_sensor.h"
#include "fan_controller.h"
#include "locker_controller.h"
#include "door_controller.h"
#include "mqtt_manager.h"

namespace {
constexpr char FAN_CONTROL_TOPIC[] = "gymtag/environment/fan_control";
constexpr char LOCKER_RESPONSE_TOPIC[] = "gymtag/locker/response";
constexpr char DOOR_RESPONSE_TOPIC[] = "gymtag/door/response";

void routeMqttMessage(const char* topic, const byte* payload, unsigned int length) {
    if (strcmp(topic, FAN_CONTROL_TOPIC) == 0) {
        FanController::handleMqttPayload(payload, length);
    } else if (strcmp(topic, LOCKER_RESPONSE_TOPIC) == 0) {
        LockerController::handleMqttPayload(payload, length);
    } else if (strcmp(topic, DOOR_RESPONSE_TOPIC) == 0) {
        DoorController::handleMqttPayload(payload, length);
    }
}
}  // namespace

void setup() {
    Serial.begin(115200);
    FanController::begin();
    EnvironmentSensor::begin();
    LockerRfid::begin();
    LockerController::begin();
    DoorInRfid::begin();
    DoorOutRfid::begin();
    DoorController::begin();
    MqttManager::begin(routeMqttMessage);
}

void loop() {
    MqttManager::update();
    EnvironmentSensor::update();

    String cardId;
    if (LockerRfid::readCard(cardId)) LockerController::handleCardScan(cardId);
    if (DoorInRfid::readCard(cardId)) DoorController::handleCardScan(cardId, "in");
    if (DoorOutRfid::readCard(cardId)) DoorController::handleCardScan(cardId, "out");
    LockerController::update();
    DoorController::update();
}
