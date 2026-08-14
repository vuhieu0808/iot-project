# GymTag ESP32 Hardware & Firmware Integration Guide

## 1. Hardware Pinout Specification (ESP32 DevKit V1)

### 1.1 Pin Configuration Table

| Peripheral / Sensor / Actuator | ESP32 Pin | Protocol / Interface | Function / Description |
|---|---|---|---|
| **DHT22 Sensor** | GPIO 15 | 1-Wire Digital | Ambient Temperature & Relative Humidity measurement |
| **Cooling Fan Relay / LED Indicator** | GPIO 12 | Digital Output | Activates ventilation fan / cooling system |
| **Door Access RFID Reader (RC522 #1)** | SPI (SDA: GPIO 5, SCK: GPIO 18, MOSI: GPIO 23, MISO: GPIO 19, RST: GPIO 22) | SPI Bus | Scans member card at gym entrance / exit door |
| **Door Lock Mechanism (Servo #1)** | GPIO 13 | PWM Output | Actuates door bolt/lock latch (0° = Locked, 90° = Unlocked) |
| **Locker RFID Reader (RC522 #2)** | SPI (SDA: GPIO 21, Shared SCK/MOSI/MISO, RST: GPIO 4) | SPI Bus | Scans member card at locker station |
| **LCD I2C Display (16x2)** | I2C (SDA: GPIO 21, SCL: GPIO 22) | I2C Bus | Displays greeting, membership expiry, locker number |

---

## 2. Firmware Execution Logic & State Machine

```
               +-----------------------------------+
               |          ESP32 BOOTUP             |
               |  - Init Serial 115200             |
               |  - Init DHT22, RFID, Servo, Relay |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |      CONNECT WI-FI & MQTT         |
               |  - Broker: test.mosquitto.org     |
               |  - Sub: fan_control, door_resp... |
               +-----------------------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
        v                                                 v
+-------------------------------+             +-------------------------------+
|    ENVIRONMENT TELEMETRY      |             |     RFID SCAN EVENT LOOP      |
|  - Read DHT22 every 5-10s     |             |  - Detect Card UID            |
|  - Pub: environment/reading   |             |  - Pub: door/checkin_request  |
|  - Callback: fan_control      |             |         or locker/request     |
|    -> Toggle GPIO 12 (Relay)  |             |  - Wait Callback & Actuate    |
+-------------------------------+             +-------------------------------+
```

### 2.1 Environmental Monitoring Loop
1. Every 5 to 10 seconds, ESP32 samples temperature and relative humidity from the DHT22 sensor on GPIO 15.
2. The payload is formatted as JSON:
   ```json
   {
     "temperature": 31.4,
     "humidity": 68.2
   }
   ```
3. ESP32 publishes this payload to `gymtag/environment/reading`.
4. ESP32 listens to `gymtag/environment/fan_control`. When a command is received:
   - If `"fan": "on"`, set GPIO 12 `HIGH` (Relay closed / Fan ON).
   - If `"fan": "off"`, set GPIO 12 `LOW` (Relay open / Fan OFF).

### 2.2 Door Check-in / Check-out Loop
1. Member swipes RFID card at RC522 #1 (Door).
2. ESP32 reads UID (e.g., `CARD001`) and publishes:
   ```json
   { "card_id": "CARD001" }
   ```
   to `gymtag/door/checkin_request`.
3. ESP32 awaits response on `gymtag/door/checkin_response`.
4. If `"status": "granted"`:
   - Rotate Servo on GPIO 13 to 90° (Unlock).
   - Display greeting `"Welcome <Name>"` or `"Goodbye <Name> (XX min)"` on LCD.
   - Wait 5 seconds, then return Servo to 0° (Lock).
5. If `"status": "denied"`:
   - Keep Servo locked (0°), flash red LED / sound buzzer, display reason on LCD (e.g., `"Card Expired"` or `"Card Inactive"`).

### 2.3 Locker Station Loop
1. Member swipes RFID card at RC522 #2 (Locker Area).
2. ESP32 publishes `{ "card_id": "CARD001" }` to `gymtag/locker/request`.
3. ESP32 awaits response on `gymtag/locker/response`.
4. If `"action": "assign"`: display `"Assigned Locker #X"`.
5. If `"action": "release"`: display `"Locker #X Released"`.

---

## 3. Simulation with PlatformIO & Wokwi

The project includes preconfigured PlatformIO and Wokwi simulation files located in the [`esp32/`](file:///D:/Hieu/university/2nd%20year/HK3/IOT/Project2/esp32) directory:
- [`esp32/src/main.cpp`](file:///D:/Hieu/university/2nd%20year/HK3/IOT/Project2/esp32/src/main.cpp): Arduino C++ firmware source code.
- [`esp32/diagram.json`](file:///D:/Hieu/university/2nd%20year/HK3/IOT/Project2/esp32/diagram.json): Wokwi schematic with ESP32 DevKit, DHT22 sensor, and Fan Indicator LED.
- [`esp32/wokwi.toml`](file:///D:/Hieu/university/2nd%20year/HK3/IOT/Project2/esp32/wokwi.toml): Simulation configuration file.

To simulate:
1. Open the project in VS Code with the **Wokwi for VS Code** extension installed.
2. Press `F1` -> **Wokwi: Start Simulator** on `esp32/diagram.json`.
3. The simulator connects to Wi-Fi `Wokwi-GUEST`, links to `test.mosquitto.org:1883`, and streams DHT22 readings to the Python backend in real-time.
