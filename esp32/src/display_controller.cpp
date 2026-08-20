#include "display_controller.h"

#include <LiquidCrystal_I2C.h>
#include <Wire.h>

#include "hardware_config.h"

namespace {
constexpr uint8_t LCD_COLUMNS = 16;
constexpr uint8_t LCD_ROWS = 2;

LiquidCrystal_I2C lcd(HardwareConfig::LCD_I2C_ADDRESS, LCD_COLUMNS, LCD_ROWS);
unsigned long returnToIdleAt = 0;

String fit(const String& value, size_t maxLength = LCD_COLUMNS) {
    return value.length() <= maxLength ? value : value.substring(0, maxLength);
}

void showLines(const String& line1, const String& line2) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(fit(line1));
    lcd.setCursor(0, 1);
    lcd.print(fit(line2));
}

void showTemporary(const String& line1, const String& line2) {
    showLines(line1, line2);
    returnToIdleAt = millis() + HardwareConfig::DISPLAY_MESSAGE_MS;
}
}  // namespace

namespace DisplayController {
void begin() {
    Wire.begin(HardwareConfig::I2C_SDA_PIN, HardwareConfig::I2C_SCL_PIN);
    lcd.init();
    lcd.backlight();
    showIdle();
}

void update() {
    if (returnToIdleAt != 0 && static_cast<long>(millis() - returnToIdleAt) < 0) {
        return;
    }
    if (returnToIdleAt != 0) showIdle();
}

void showIdle() {
    returnToIdleAt = 0;
    showLines("GymTag", "Scan Your Card");
}

void showAssigned(const String& memberName, int lockerNumber) {
    const String lockerText = " L#" + String(lockerNumber);
    showTemporary("Access Granted", fit(memberName, LCD_COLUMNS - lockerText.length()) + lockerText);
}

void showAuthorized(const String& memberName) {
    showTemporary("Authorized", memberName);
}

void showDenied() {
    showTemporary("Access Denied", "Try Again");
}

void showReleased() {
    showTemporary("Locker Released", "Thank You");
}
}  // namespace DisplayController
