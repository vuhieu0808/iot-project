#include "locker_controller.h"

#include <ArduinoJson.h>
#include <ESP32Servo.h>

#include "display_controller.h"
#include "hardware_config.h"
#include "mqtt_manager.h"

namespace {
constexpr char REQUEST_TOPIC[] = "gymtag/locker/request";

enum class LockerState {
    IDLE,
    WAIT_DOOR_OPEN,
    WAIT_DOOR_CLOSE,
    WAITING_RELEASE_RESPONSE,
};

struct DebouncedInput {
    bool raw = HIGH;
    bool stable = HIGH;
    unsigned long changedAt = 0;
};

struct LockerSession {
    LockerState state = LockerState::IDLE;
    String cardId;
    String memberName;
    bool releasePending = false;
    bool doorClosedObserved = false;
    bool doorTimeoutWarningLogged = false;
    unsigned long stateStartedAt = 0;
};

struct PendingScan {
    bool active = false;
    String cardId;
    unsigned long startedAt = 0;
};

Servo lockerServos[HardwareConfig::LOCKER_COUNT];
DebouncedInput doorInputs[HardwareConfig::LOCKER_COUNT];
DebouncedInput releaseInput;
LockerSession lockers[HardwareConfig::LOCKER_COUNT];
PendingScan pendingScan;
int releaseTargetLockerNumber = 0;

bool validLockerNumber(int lockerNumber) {
    return lockerNumber > 0 && static_cast<size_t>(lockerNumber) <= HardwareConfig::LOCKER_COUNT;
}

size_t lockerIndex(int lockerNumber) { return static_cast<size_t>(lockerNumber - 1); }

LockerSession& lockerSession(int lockerNumber) { return lockers[lockerIndex(lockerNumber)]; }

void setLockerState(LockerSession& session, LockerState next) {
    session.state = next;
    session.stateStartedAt = millis();
    session.doorTimeoutWarningLogged = false;
}

void setLockerAngle(int lockerNumber, int angle) {
    if (!validLockerNumber(lockerNumber)) return;
    lockerServos[lockerIndex(lockerNumber)].write(angle);
}

void lockLocker(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return;
    setLockerAngle(lockerNumber, HardwareConfig::SERVO_LOCKED_ANGLE);
    Serial.printf("Locker #%d locked.\n", lockerNumber);
}

void unlockLocker(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return;
    setLockerAngle(lockerNumber, HardwareConfig::SERVO_UNLOCKED_ANGLE);
    Serial.printf("Locker #%d unlocked.\n", lockerNumber);
}

void updateInput(DebouncedInput& input, bool raw, unsigned long now) {
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

bool isDoorOpen(int lockerNumber) { return !isDoorClosed(lockerNumber); }

bool releaseButtonPressed(unsigned long now) {
    const bool previous = releaseInput.stable;
    updateInput(releaseInput, digitalRead(HardwareConfig::RELEASE_BUTTON_PIN), now);
    return previous == HIGH && releaseInput.stable == LOW;
}

bool publishOperation(const String& cardId, const char* operation, int lockerNumber = 0) {
    JsonDocument document;
    document["card_id"] = cardId;
    document["operation"] = operation;
    if (strcmp(operation, "release") == 0) {
        document["locker_number"] = lockerNumber;
    }
    String payload;
    serializeJson(document, payload);
    return MqttManager::publish(REQUEST_TOPIC, payload);
}

void clearLockerSession(int lockerNumber) {
    if (!validLockerNumber(lockerNumber)) return;
    LockerSession& session = lockerSession(lockerNumber);
    session.cardId = "";
    session.memberName = "";
    session.releasePending = false;
    session.doorClosedObserved = false;
    setLockerState(session, LockerState::IDLE);

    if (releaseTargetLockerNumber == lockerNumber) {
        releaseTargetLockerNumber = 0;
    }
}

int findReleaseResponseLocker(const String& cardId) {
    for (int lockerNumber = 1; lockerNumber <= static_cast<int>(HardwareConfig::LOCKER_COUNT); ++lockerNumber) {
        const LockerSession& session = lockerSession(lockerNumber);
        if (session.state == LockerState::WAITING_RELEASE_RESPONSE && session.cardId == cardId) {
            return lockerNumber;
        }
    }
    return 0;
}

void finishPhysicalSession(int lockerNumber) {
    LockerSession& session = lockerSession(lockerNumber);
    lockLocker(lockerNumber);

    if (session.releasePending) {
        if (publishOperation(session.cardId, "release", lockerNumber)) {
            Serial.printf("Publishing release request for Locker #%d.\n", lockerNumber);
            setLockerState(session, LockerState::WAITING_RELEASE_RESPONSE);
            return;
        }
        Serial.println("Locker release publish failed; ownership remains unchanged.");
    }

    clearLockerSession(lockerNumber);
}

void updateLockerSession(int lockerNumber, unsigned long now) {
    LockerSession& session = lockerSession(lockerNumber);
    if (session.state == LockerState::IDLE || session.state == LockerState::WAITING_RELEASE_RESPONSE) {
        return;
    }

    const bool closed = isDoorClosed(lockerNumber);
    if (session.state == LockerState::WAIT_DOOR_OPEN) {
        if (closed) {
            session.doorClosedObserved = true;
        } else if (session.doorClosedObserved) {
            Serial.printf("Door #%d opened. Waiting for it to close.\n", lockerNumber);
            setLockerState(session, LockerState::WAIT_DOOR_CLOSE);
            return;
        }

        if (now - session.stateStartedAt >= HardwareConfig::DOOR_ACTION_TIMEOUT_MS) {
            if (closed) {
                Serial.printf("Door #%d was not opened before timeout; locking locker.\n", lockerNumber);
                lockLocker(lockerNumber);
                clearLockerSession(lockerNumber);
            } else if (!session.doorTimeoutWarningLogged) {
                Serial.printf("Door #%d is still open; waiting without forcing the servo lock.\n", lockerNumber);
                session.doorTimeoutWarningLogged = true;
            }
        }
        return;
    }

    if (session.state == LockerState::WAIT_DOOR_CLOSE) {
        if (closed) {
            Serial.printf("Door #%d closed.\n", lockerNumber);
            finishPhysicalSession(lockerNumber);
        } else if (now - session.stateStartedAt >= HardwareConfig::DOOR_ACTION_TIMEOUT_MS &&
                   !session.doorTimeoutWarningLogged) {
            Serial.printf("Door #%d is still open; waiting without forcing the servo lock.\n", lockerNumber);
            session.doorTimeoutWarningLogged = true;
        }
    }
}

void handleReleaseButton() {
    if (!validLockerNumber(releaseTargetLockerNumber)) {
        Serial.println("Release button ignored: no selected active locker session.");
        return;
    }

    LockerSession& session = lockerSession(releaseTargetLockerNumber);
    if (session.state != LockerState::WAIT_DOOR_OPEN && session.state != LockerState::WAIT_DOOR_CLOSE) {
        Serial.println("Release button ignored: selected locker is not in a door session.");
        return;
    }

    if (!session.releasePending) {
        session.releasePending = true;
        Serial.printf("Release marked pending for Locker #%d; waiting for door close.\n", releaseTargetLockerNumber);
    }
}

void clearPendingScan() {
    pendingScan.active = false;
    pendingScan.cardId = "";
    pendingScan.startedAt = 0;
}

void beginLockerSession(int lockerNumber, const String& cardId, const String& memberName, const String& action) {
    LockerSession& session = lockerSession(lockerNumber);
    if (session.state != LockerState::IDLE && session.cardId != cardId) {
        Serial.printf("Locker #%d already has an active physical session.\n", lockerNumber);
        return;
    }

    session.cardId = cardId;
    session.memberName = memberName;
    session.releasePending = false;
    session.doorClosedObserved = isDoorClosed(lockerNumber);
    releaseTargetLockerNumber = lockerNumber;

    if (action == "assign") {
        DisplayController::showAssigned(memberName, lockerNumber);
    } else {
        DisplayController::showAuthorized(memberName);
    }

    Serial.printf("%s - Locker #%d (%s).\n", memberName.c_str(), lockerNumber, action.c_str());
    unlockLocker(lockerNumber);
    Serial.printf("Waiting for Door #%d to open.\n", lockerNumber);
    setLockerState(session, LockerState::WAIT_DOOR_OPEN);
}
}  // namespace

namespace LockerController {
void begin() {
    for (size_t index = 0; index < HardwareConfig::LOCKER_COUNT; ++index) {
        lockerServos[index].setPeriodHertz(50);
        lockerServos[index].attach(HardwareConfig::LOCKER_SERVO_PINS[index], HardwareConfig::SERVO_MIN_PULSE_US,
                                   HardwareConfig::SERVO_MAX_PULSE_US);
        lockLocker(static_cast<int>(index + 1));

        const uint8_t doorPin = HardwareConfig::LOCKER_DOOR_SWITCH_PINS[index];
        pinMode(doorPin, INPUT_PULLUP);
        doorInputs[index].raw = digitalRead(doorPin);
        doorInputs[index].stable = doorInputs[index].raw;
    }

    pinMode(HardwareConfig::RELEASE_BUTTON_PIN, INPUT_PULLUP);
    releaseInput.raw = digitalRead(HardwareConfig::RELEASE_BUTTON_PIN);
    releaseInput.stable = releaseInput.raw;
    Serial.println("Three independent locker sessions initialized in LOCKED position.");
}

void update() {
    const unsigned long now = millis();
    for (size_t index = 0; index < HardwareConfig::LOCKER_COUNT; ++index) {
        updateInput(doorInputs[index], digitalRead(HardwareConfig::LOCKER_DOOR_SWITCH_PINS[index]), now);
    }

    if (releaseButtonPressed(now)) {
        handleReleaseButton();
    }

    if (pendingScan.active && now - pendingScan.startedAt >= HardwareConfig::BACKEND_TIMEOUT_MS) {
        Serial.println("Locker backend scan response timed out.");
        clearPendingScan();
    }

    for (int lockerNumber = 1; lockerNumber <= static_cast<int>(HardwareConfig::LOCKER_COUNT); ++lockerNumber) {
        LockerSession& session = lockerSession(lockerNumber);
        if (session.state == LockerState::WAITING_RELEASE_RESPONSE &&
            now - session.stateStartedAt >= HardwareConfig::BACKEND_TIMEOUT_MS) {
            Serial.printf("Locker #%d release response timed out; physical locker remains locked.\n", lockerNumber);
            clearLockerSession(lockerNumber);
            continue;
        }
        updateLockerSession(lockerNumber, now);
    }
}

void handleCardScan(const String& cardId) {
    if (pendingScan.active) {
        Serial.println("RFID scan ignored while another backend scan request is pending.");
        return;
    }

    pendingScan.active = true;
    pendingScan.cardId = cardId;
    pendingScan.startedAt = millis();
    if (!publishOperation(cardId, "scan")) {
        Serial.println("Locker scan publish failed.");
        clearPendingScan();
    }
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
    const int releaseLockerNumber = findReleaseResponseLocker(cardId);

    if (action == "release" && releaseLockerNumber != 0) {
        if (!document["locker_number"].is<int>() || document["locker_number"].as<int>() != releaseLockerNumber) {
            Serial.println("Ignored invalid locker release response.");
            return;
        }
        Serial.printf("Locker #%d released successfully; backend ownership cleared.\n", releaseLockerNumber);
        DisplayController::showReleased();
        clearLockerSession(releaseLockerNumber);
        return;
    }

    if (action == "denied") {
        if (pendingScan.active && cardId == pendingScan.cardId) {
            Serial.printf("Locker request denied: %s\n", document["reason"] | "Unknown reason");
            DisplayController::showDenied();
            clearPendingScan();
            return;
        }
        if (releaseLockerNumber != 0) {
            Serial.printf("Locker release denied: %s\n", document["reason"] | "Unknown reason");
            DisplayController::showDenied();
            clearLockerSession(releaseLockerNumber);
            return;
        }
    }

    if ((action != "assign" && action != "access") || !pendingScan.active || cardId != pendingScan.cardId ||
        !document["locker_number"].is<int>()) {
        Serial.println("Ignored stale or unrelated locker response.");
        return;
    }

    const int lockerNumber = document["locker_number"].as<int>();
    if (!validLockerNumber(lockerNumber)) {
        Serial.printf("Locker #%d is outside the three-locker hardware mapping.\n", lockerNumber);
        clearPendingScan();
        return;
    }

    const String memberName = String(document["member_name"] | "Unknown member");
    clearPendingScan();
    beginLockerSession(lockerNumber, cardId, memberName, action);
}
}  // namespace LockerController
