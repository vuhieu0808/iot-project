#include "locker_controller.h"

#include <ArduinoJson.h>

#include "hardware_config.h"
#include "mqtt_manager.h"

namespace {
constexpr char REQUEST_TOPIC[] = "gymtag/locker/request";
enum class State { IDLE, WAITING_SCAN, MEMBER_SESSION, WAITING_RELEASE, COOLDOWN };

State state = State::IDLE;
String currentCardId;
String currentMemberName;
int currentLockerNumber = 0;
unsigned long stateStartedAt = 0;
int activeRelayIndex = -1;
unsigned long relayActivatedAt = 0;
bool lastRawButtonState = HIGH;
bool stableButtonState = HIGH;
unsigned long buttonChangedAt = 0;

void setState(State next) {
    state = next;
    stateStartedAt = millis();
}

void deactivateRelay() {
    if (activeRelayIndex < 0) return;
    const uint8_t pin = HardwareConfig::LOCKER_RELAY_PINS[activeRelayIndex];
    digitalWrite(pin, HardwareConfig::LOCKER_RELAY_ACTIVE_HIGH ? LOW : HIGH);
    activeRelayIndex = -1;
}

bool openLocker(int lockerNumber) {
    if (lockerNumber <= 0 || static_cast<size_t>(lockerNumber) > HardwareConfig::LOCKER_RELAY_COUNT) {
        Serial.printf("Locker #%d has no validated relay mapping; no GPIO activated.\n", lockerNumber);
        return false;
    }
    deactivateRelay();
    activeRelayIndex = lockerNumber - 1;
    const uint8_t pin = HardwareConfig::LOCKER_RELAY_PINS[activeRelayIndex];
    digitalWrite(pin, HardwareConfig::LOCKER_RELAY_ACTIVE_HIGH ? HIGH : LOW);
    relayActivatedAt = millis();
    Serial.printf("Opening locker #%d.\n", lockerNumber);
    return true;
}

bool publishOperation(const char* operation) {
    JsonDocument document;
    document["card_id"] = currentCardId;
    document["operation"] = operation;
    if (strcmp(operation, "release") == 0) document["locker_number"] = currentLockerNumber;
    String payload;
    serializeJson(document, payload);
    return MqttManager::publish(REQUEST_TOPIC, payload);
}

bool releaseButtonPressed(unsigned long now) {
    if (HardwareConfig::RELEASE_BUTTON_PIN < 0) return false;
    const bool raw = digitalRead(HardwareConfig::RELEASE_BUTTON_PIN);
    if (raw != lastRawButtonState) {
        lastRawButtonState = raw;
        buttonChangedAt = now;
    }
    if (now - buttonChangedAt < HardwareConfig::BUTTON_DEBOUNCE_MS || raw == stableButtonState) return false;
    stableButtonState = raw;
    return stableButtonState == LOW;
}

void clearSession() {
    currentCardId = "";
    currentMemberName = "";
    currentLockerNumber = 0;
}
}  // namespace

namespace LockerController {
void begin() {
    for (size_t index = 0; index < HardwareConfig::LOCKER_RELAY_COUNT; ++index) {
        const uint8_t pin = HardwareConfig::LOCKER_RELAY_PINS[index];
        pinMode(pin, OUTPUT);
        digitalWrite(pin, HardwareConfig::LOCKER_RELAY_ACTIVE_HIGH ? LOW : HIGH);
    }
    if (HardwareConfig::RELEASE_BUTTON_PIN >= 0) {
        pinMode(HardwareConfig::RELEASE_BUTTON_PIN, INPUT_PULLUP);
        lastRawButtonState = digitalRead(HardwareConfig::RELEASE_BUTTON_PIN);
        stableButtonState = lastRawButtonState;
    } else {
        Serial.println("Release button disabled: GPIO mapping is not defined.");
    }
    if (HardwareConfig::LOCKER_RELAY_COUNT == 0) Serial.println("Locker relays disabled: GPIO mapping is not defined.");
}

void update() {
    const unsigned long now = millis();
    if (activeRelayIndex >= 0 && now - relayActivatedAt >= HardwareConfig::RELAY_PULSE_MS) deactivateRelay();

    if ((state == State::WAITING_SCAN || state == State::WAITING_RELEASE) &&
        now - stateStartedAt >= HardwareConfig::BACKEND_TIMEOUT_MS) {
        Serial.println("Locker backend response timed out.");
        setState(state == State::WAITING_RELEASE ? State::MEMBER_SESSION : State::COOLDOWN);
    }

    if (state == State::MEMBER_SESSION) {
        if (releaseButtonPressed(now)) {
            if (publishOperation("release")) {
                Serial.printf("Release requested for locker #%d.\n", currentLockerNumber);
                setState(State::WAITING_RELEASE);
            }
        } else if (now - stateStartedAt >= HardwareConfig::MEMBER_SESSION_TIMEOUT_MS) {
            Serial.println("Locker member session expired without release.");
            clearSession();
            setState(State::IDLE);
        }
    }

    if (state == State::COOLDOWN && now - stateStartedAt >= HardwareConfig::RFID_COOLDOWN_MS) {
        clearSession();
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
        setState(State::COOLDOWN);
        return;
    }
    setState(State::WAITING_SCAN);
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
    if ((state != State::WAITING_SCAN && state != State::WAITING_RELEASE) || cardId != currentCardId) {
        Serial.println("Ignored stale or unrelated locker response.");
        return;
    }

    if (action == "denied") {
        Serial.printf("Locker request denied: %s\n", document["reason"] | "Unknown reason");
        setState(state == State::WAITING_RELEASE ? State::MEMBER_SESSION : State::COOLDOWN);
        return;
    }
    if (!document["locker_number"].is<int>()) {
        Serial.println("Locker response has an invalid locker_number.");
        setState(State::COOLDOWN);
        return;
    }
    const int lockerNumber = document["locker_number"].as<int>();
    if (lockerNumber <= 0) {
        Serial.println("Locker response locker_number is out of range.");
        setState(State::COOLDOWN);
        return;
    }

    if ((action == "assign" || action == "access") && state == State::WAITING_SCAN) {
        currentLockerNumber = lockerNumber;
        currentMemberName = String(document["member_name"] | "Unknown member");
        Serial.printf("%s - Locker #%d (%s).\n", currentMemberName.c_str(), lockerNumber, action.c_str());
        openLocker(lockerNumber);
        setState(State::MEMBER_SESSION);
    } else if (action == "release" && state == State::WAITING_RELEASE) {
        if (lockerNumber != currentLockerNumber) {
            Serial.println("Release response does not match active locker session.");
            setState(State::MEMBER_SESSION);
            return;
        }
        Serial.printf("%s released locker #%d.\n", currentMemberName.c_str(), lockerNumber);
        openLocker(lockerNumber);
        setState(State::COOLDOWN);
    } else {
        Serial.printf("Unexpected locker response action: %s\n", action.c_str());
    }
}
}  // namespace LockerController
