#include "locker_controller.h"

#include <ArduinoJson.h>
#include <ESP32Servo.h>

#include "hardware_config.h"
#include "mqtt_manager.h"

namespace {
constexpr char REQUEST_IN_TOPIC[] = "gymtag/door/checkin_request";
constexpr char REQUEST_OUT_TOPIC[] = "gymtag/door/checkout_request";

enum class State {
    CLOSE,
    OPEN_IN,
    OPEN_OUT
};

State state = State::CLOSE;
String currentCardId;
unsigned long lastServoSpin = 0;

Servo servo;

bool publish(const char* operation) {
    JsonDocument document;
    document["card_id"] = currentCardId;
    String payload;
    serializeJson(document, payload);
    if (strcmp(operation, "in") == 0) {
        return MqttManager::publish(REQUEST_IN_TOPIC, payload);
    }
    return MqttManager::publish(REQUEST_OUT_TOPIC, payload);
}

void clearSession() {
    currentCardId = "";
}

}  // namespace

namespace DoorController {
void begin() {
    servo.setPeriodHertz(50);
    servo.attach(HardwareConfig::DOOR_SERVO_PIN);
    servo.write(90);
}

void update() {
    const unsigned long now = millis();
    
    if (now - lastServoSpin >= HardwareConfig::MAIN_DOOR_TIMEOUT_MS && state != State::CLOSE) {
        servo.write(90);
        state = State::CLOSE;
        lastServoSpin = millis();
    }
}

void handleCardScan(const String& cardId, const char* typ) {
    currentCardId = cardId;
    if (!publish(typ)) {
        clearSession();
        return;
    }
}

void handleMqttPayload(const byte* payload, unsigned int length) {
    JsonDocument document;
    const DeserializationError error = deserializeJson(document, payload, length);
    if (error) {
        Serial.printf("Invalid locker response JSON: %s\n", error.c_str());
        return;
    }
    
    const String action = document["action"] | "";
    const String status = document["status"] | "";

    if (status == "denied") return; 

    if (action == "checkin") {
        servo.write(HardwareConfig::DOOR_SERVO_OPEN_IN_ANGLE);
        state = State::OPEN_IN;
        lastServoSpin = millis();
    } else if (action == "checkout") {
        servo.write(HardwareConfig::DOOR_SERVO_OPEN_OUT_ANGLE);
        state = State::OPEN_OUT;
        lastServoSpin = millis();
    }
}
}
