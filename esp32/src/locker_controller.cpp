#include "locker_controller.h"

#include <ArduinoJson.h>
#include <ESP32Servo.h>

#include "hardware_config.h"
#include "mqtt_manager.h"

namespace {
constexpr char REQUEST_TOPIC[] = "gymtag/locker/request";

enum class State {
    IDLE,
    WAITING_BACKEND,
    WAIT_DOOR_OPEN,
    WAIT_DOOR_CLOSE,
    WAITING_RELEASE_RESPONSE,
    COOLDOWN,
};

struct DebouncedInput {
    bool raw = HIGH;
    bool stable = HIGH;
    unsigned long changedAt = 0;
};

State state = State::IDLE;
String currentCardId;
String currentMemberName;
int currentLockerNumber = 0;
bool releasePending = false;
bool doorClosedObserved = false;
bool doorTimeoutWarningLogged = false;
unsigned long stateStartedAt = 0;

Servo lockerServos[HardwareConfig::LOCKER_COUNT];
DebouncedInput doorInputs[HardwareConfig::LOCKER_COUNT];
DebouncedInput releaseInput;

void setState(State next) {
    state = next;
    stateStartedAt = millis();
    doorTimeoutWarningLogged = false;
}

bool validLockerNumber(int lockerNumber) {
    return lockerNumber > 0 &&
           static_cast<size_t>(lockerNumber) <= HardwareConfig::LOCKER_COUNT;
}

size_t lockerIndex(int lockerNumber) {
    return static_cast<size_t>(lockerNumber - 1);
}

void lockLocker(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return;
    lockerServos[lockerIndex(lockerNumber)].write(HardwareConfig::SERVO_LOCKED_ANGLE);
    Serial.printf("Locker #%d locked.\n", lockerNumber);
}

void unlockLocker(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return;
    lockerServos[lockerIndex(lockerNumber)].write(HardwareConfig::SERVO_UNLOCKED_ANGLE);
    Serial.printf("Locker #%d unlocked.\n", lockerNumber);
}

void updateInput(DebouncedInput& input, uint8_t pin, unsigned long now) {
    const bool raw = digitalRead(pin);
    if (raw != input.raw) {
        input.raw = raw;
        input.changedAt = now;
    }
    if (raw != input.stable && now - input.changedAt >= HardwareConfig::BUTTON_DEBOUNCE_MS) {
        input.stable = raw;
    }
}

bool isDoorClosed(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return false;
    return doorInputs[lockerIndex(lockerNumber)].stable == LOW;
}

bool releaseButtonPressed(unsigned long now) {
    const bool previous = releaseInput.stable;
    updateInput(releaseInput, HardwareConfig::RELEASE_BUTTON_PIN, now);
    return previous == HIGH && releaseInput.stable == LOW;
}

bool publishOperation(const char* operation) {
    JsonDocument document;
    document["card_id"] = currentCardId;
    document["operation"] = operation;
    if (strcmp(operation, "release") == 0) {
        document["locker_number"] = currentLockerNumber;
    }
    String payload;
    serializeJson(document, payload);
    return MqttManager::publish(REQUEST_TOPIC, payload);
}

void clearSession() {
    currentCardId = "";
    currentMemberName = "";
    currentLockerNumber = 0;
    releasePending = false;
    doorClosedObserved = false;
}

void finishPhysicalSession() {
    lockLocker(currentLockerNumber);

    if (releasePending) {
        if (publishOperation("release")) {
            Serial.printf("Publishing release request for Locker #%d.\n", currentLockerNumber);
            setState(State::WAITING_RELEASE_RESPONSE);
            return;
        }
        Serial.println("Locker release publish failed; ownership remains unchanged.");
    }

    clearSession();
    setState(State::COOLDOWN);
}

void updateActiveDoor(unsigned long now) {
    if (!validLockerNumber(currentLockerNumber)) return;

    const bool closed = isDoorClosed(currentLockerNumber);
    if (state == State::WAIT_DOOR_OPEN) {
        if (closed) {
            doorClosedObserved = true;
        } else if (doorClosedObserved) {
            Serial.printf("Door #%d opened. Waiting for it to close.\n", currentLockerNumber);
            setState(State::WAIT_DOOR_CLOSE);
            return;
        }

        if (now - stateStartedAt >= HardwareConfig::DOOR_ACTION_TIMEOUT_MS) {
            if (closed) {
                Serial.printf("Door #%d was not opened before timeout; locking locker.\n",
                              currentLockerNumber);
                lockLocker(currentLockerNumber);
                clearSession();
                setState(State::COOLDOWN);
            } else if (!doorTimeoutWarningLogged) {
                Serial.printf("Door #%d is still open; waiting without forcing the servo lock.\n",
                              currentLockerNumber);
                doorTimeoutWarningLogged = true;
            }
        }
    } else if (state == State::WAIT_DOOR_CLOSE) {
        if (closed) {
            Serial.printf("Door #%d closed.\n", currentLockerNumber);
            finishPhysicalSession();
        } else if (now - stateStartedAt >= HardwareConfig::DOOR_ACTION_TIMEOUT_MS &&
                   !doorTimeoutWarningLogged) {
            Serial.printf("Door #%d is still open; waiting without forcing the servo lock.\n",
                          currentLockerNumber);
            doorTimeoutWarningLogged = true;
        }
    }
}
}  // namespace

namespace LockerController {
void begin() {
    for (size_t index = 0; index < HardwareConfig::LOCKER_COUNT; ++index) {
        lockerServos[index].setPeriodHertz(50);
        lockerServos[index].attach(HardwareConfig::LOCKER_SERVO_PINS[index],
                                   HardwareConfig::SERVO_MIN_PULSE_US,
                                   HardwareConfig::SERVO_MAX_PULSE_US);
        lockerServos[index].write(HardwareConfig::SERVO_LOCKED_ANGLE);

        const uint8_t doorPin = HardwareConfig::LOCKER_DOOR_SWITCH_PINS[index];
        pinMode(doorPin, INPUT_PULLUP);
        doorInputs[index].raw = digitalRead(doorPin);
        doorInputs[index].stable = doorInputs[index].raw;
    }

    pinMode(HardwareConfig::RELEASE_BUTTON_PIN, INPUT_PULLUP);
    releaseInput.raw = digitalRead(HardwareConfig::RELEASE_BUTTON_PIN);
    releaseInput.stable = releaseInput.raw;

    Serial.println("Four servo lockers initialized in LOCKED position.");
}

void update() {
    const unsigned long now = millis();
    for (size_t index = 0; index < HardwareConfig::LOCKER_COUNT; ++index) {
        updateInput(doorInputs[index], HardwareConfig::LOCKER_DOOR_SWITCH_PINS[index], now);
    }

    const bool releasePressed = releaseButtonPressed(now);
    if (releasePressed && (state == State::WAIT_DOOR_OPEN || state == State::WAIT_DOOR_CLOSE)) {
        if (!releasePending) {
            releasePending = true;
            Serial.printf("Release marked pending for Locker #%d; waiting for door close.\n",
                          currentLockerNumber);
        }
    } else if (releasePressed && state == State::IDLE) {
        Serial.println("Release button ignored: no active locker session.");
    }

    if (state == State::WAITING_BACKEND &&
        now - stateStartedAt >= HardwareConfig::BACKEND_TIMEOUT_MS) {
        Serial.println("Locker backend response timed out.");
        clearSession();
        setState(State::COOLDOWN);
    } else if (state == State::WAITING_RELEASE_RESPONSE &&
               now - stateStartedAt >= HardwareConfig::BACKEND_TIMEOUT_MS) {
        Serial.println("Locker release response timed out; physical locker remains locked.");
        clearSession();
        setState(State::COOLDOWN);
    }

    if (state == State::WAIT_DOOR_OPEN || state == State::WAIT_DOOR_CLOSE) {
        updateActiveDoor(now);
    }

    if (state == State::COOLDOWN &&
        now - stateStartedAt >= HardwareConfig::RFID_COOLDOWN_MS) {
        setState(State::IDLE);
    }
}

void handleCardScan(const String& cardId) {
    if (state != State::IDLE) {
        Serial.println("RFID scan ignored while locker session is active.");
        return;
    }

    currentCardId = cardId;
    if (!publishOperation("scan")) {
        Serial.println("Locker scan publish failed.");
        clearSession();
        setState(State::COOLDOWN);
        return;
    }
    setState(State::WAITING_BACKEND);
}

void handleMqttPayload(const byte* payload, unsigned int length) {
    JsonDocument document;
    const DeserializationError error = deserializeJson(document, payload, length);
    if (error) {
        Serial.printf("Invalid locker response JSON: %s\n", error.c_str());
        return;
    }

    const String cardId = document["card_id"] | "";
    const String action = document["action"] | "";
    if ((state != State::WAITING_BACKEND && state != State::WAITING_RELEASE_RESPONSE) ||
        cardId != currentCardId) {
        Serial.println("Ignored stale or unrelated locker response.");
        return;
    }

    if (action == "denied") {
        Serial.printf("Locker request denied: %s\n", document["reason"] | "Unknown reason");
        clearSession();
        setState(State::COOLDOWN);
        return;
    }

    if (state == State::WAITING_RELEASE_RESPONSE) {
        if (action != "release" || !document["locker_number"].is<int>() ||
            document["locker_number"].as<int>() != currentLockerNumber) {
            Serial.println("Ignored invalid locker release response.");
            return;
        }
        Serial.printf("Locker #%d released successfully; backend ownership cleared.\n",
                      currentLockerNumber);
        clearSession();
        setState(State::COOLDOWN);
        return;
    }

    if ((action != "assign" && action != "access") ||
        !document["locker_number"].is<int>()) {
        Serial.println("Locker response has an invalid action or locker_number.");
        clearSession();
        setState(State::COOLDOWN);
        return;
    }

    const int lockerNumber = document["locker_number"].as<int>();
    if (!validLockerNumber(lockerNumber)) {
        Serial.printf("Locker #%d is outside the four-locker hardware mapping.\n", lockerNumber);
        clearSession();
        setState(State::COOLDOWN);
        return;
    }

    currentLockerNumber = lockerNumber;
    currentMemberName = String(document["member_name"] | "Unknown member");
    releasePending = false;
    doorClosedObserved = isDoorClosed(lockerNumber);

    Serial.printf("%s - Locker #%d (%s).\n", currentMemberName.c_str(), lockerNumber,
                  action.c_str());
    unlockLocker(lockerNumber);
    Serial.printf("Waiting for Door #%d to open.\n", lockerNumber);
    setState(State::WAIT_DOOR_OPEN);
}
}  // namespace LockerController
