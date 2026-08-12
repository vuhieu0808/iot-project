# GymTag ESP32 Hardware & Firmware Integration Guide

## 1. Hardware Pinout Mapping (ESP32)

| Peripheral / Sensor | ESP32 Pin | Function / Description |
|---|---|---|
| MFRC522 RFID #1 (Door) | SPI (SDA: GPIO 5, SCK: GPIO 18, MOSI: GPIO 23, MISO: GPIO 19, RST: GPIO 22) | Door Access Check-in / Check-out |
| MFRC522 RFID #2 (Locker) | SPI (SDA: GPIO 21, shared SCK/MOSI/MISO, RST: GPIO 4) | Locker Assignment / Release |
| DHT22 Sensor | GPIO 15 | Temperature & Humidity reading |
| Servo Motor #1 | GPIO 13 | Door Lock Release Mechanism |
| Relay Module | GPIO 12 | Cooling Fan Power Control |

---

## 2. Firmware Execution Logic

1. **Initialization**:
   - Connect to Wi-Fi network.
   - Connect to MQTT Broker (`test.mosquitto.org:1883`).
   - Subscribe to MQTT response topics:
     - `gymtag/door/checkin_response`
     - `gymtag/locker/response`
     - `gymtag/environment/fan_control`

2. **Door Scan Loop**:
   - Detect card scan at MFRC522 #1.
   - Extract Card UID string (e.g. `"CARD001"`).
   - Publish JSON payload to `gymtag/door/checkin_request`.
   - Wait for `gymtag/door/checkin_response` callback.
   - If `status == "granted"`, actuate Door Servo for 5 seconds, then lock again.

3. **Locker Scan Loop**:
   - Detect card scan at MFRC522 #2.
   - Publish JSON payload to `gymtag/locker/request`.
   - Wait for `gymtag/locker/response` callback.
   - Display assigned locker number on LCD/OLED display (if available) or trigger indicator buzzer.

4. **Environment Monitoring Loop**:
   - Read DHT22 every 10 seconds.
   - Publish `{"temperature": temp, "humidity": hum}` to `gymtag/environment/reading`.
   - In `gymtag/environment/fan_control` callback, set Relay pin `HIGH` (if `"fan": "on"`) or `LOW` (if `"fan": "off"`).
