#include "../include/door_out_RFID.h"

#include <MFRC522.h>
#include <SPI.h>

#include "hardware_config.h"

namespace {
MFRC522 reader(HardwareConfig::RFID_DOOR_OUT_SS_PIN, HardwareConfig::RFID_RST_PIN);
unsigned long lastAcceptedAt = 0;
bool hasAcceptedCard = false;

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

namespace DoorOutRfid {
void begin() {
    SPI.begin();
    reader.PCD_Init();
    Serial.println("Door RC522 initialized.");
}

bool readCard(String& cardId) {
    const unsigned long now = millis();
    if (hasAcceptedCard && now - lastAcceptedAt < HardwareConfig::RFID_COOLDOWN_MS) return false;
    if (!reader.PICC_IsNewCardPresent() || !reader.PICC_ReadCardSerial()) return false;

    cardId = normalizeUid(reader.uid);
    reader.PICC_HaltA();
    reader.PCD_StopCrypto1();
    lastAcceptedAt = now;
    hasAcceptedCard = true;
    Serial.printf("RFID accepted: %s\n", cardId.c_str());
    return true;
}
}  // namespace DoorRfid
