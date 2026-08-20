#include "../include/lockerRFID.h"

#include <MFRC522.h>
#include <SPI.h>

#include "hardware_config.h"

namespace {
MFRC522 reader(HardwareConfig::RFID_LOCKER_SS_PIN, HardwareConfig::RFID_RST_PIN);
unsigned long lastAcceptedAt = 0;
bool hasAcceptedCard = false;
String lastAcceptedCardId;

String normalizeUid(const MFRC522::Uid& uid) {
    String value;
    value.reserve(uid.size * 2);
    for (byte index = 0; index < uid.size; ++index) {
        if (uid.uidByte[index] < 0x10) value += '0';
        value += String(uid.uidByte[index], HEX);
    }
    value.toUpperCase();
    return value;
}
}  // namespace

namespace LockerRfid {
void begin() {
    SPI.begin();
    reader.PCD_Init();
    Serial.println("Locker RC522 initialized.");
}

bool readCard(String& cardId) {
    const unsigned long now = millis();
    if (!reader.PICC_IsNewCardPresent() || !reader.PICC_ReadCardSerial()) return false;

    cardId = normalizeUid(reader.uid);
    reader.PICC_HaltA();
    reader.PCD_StopCrypto1();

    if (hasAcceptedCard && cardId == lastAcceptedCardId &&
        now - lastAcceptedAt < HardwareConfig::RFID_COOLDOWN_MS) {
        return false;
    }

    lastAcceptedAt = now;
    hasAcceptedCard = true;
    lastAcceptedCardId = cardId;
    Serial.printf("RFID accepted: %s\n", cardId.c_str());
    return true;
}
}  // namespace LockerRfid
