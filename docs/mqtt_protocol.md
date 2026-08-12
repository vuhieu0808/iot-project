# GymTag MQTT Messaging Protocol Specification

Default MQTT Broker: `test.mosquitto.org` (Port 1883)  
QoS Level: `0` or `1`  
Payload Encoding: UTF-8 JSON

---

## 1. Door Access Control Channel

### 1.1 Door Check-in Request
- **Topic**: `gymtag/door/checkin_request`
- **Direction**: ESP32 -> Python Backend
- **Payload Schema**:
  ```json
  {
    "card_id": "RFID_CARD_STRING"
  }
  ```

### 1.2 Door Check-in Response
- **Topic**: `gymtag/door/checkin_response`
- **Direction**: Python Backend -> ESP32
- **Payload Schema (Access Granted)**:
  ```json
  {
    "card_id": "RFID_CARD_STRING",
    "status": "granted",
    "action": "checkin",
    "member_name": "Full Name",
    "reason": "Check-in granted",
    "duration_minutes": null
  }
  ```
- **Payload Schema (Access Denied - Expired or Not Found)**:
  ```json
  {
    "card_id": "RFID_CARD_STRING",
    "status": "denied",
    "action": "checkin",
    "member_name": "Unknown",
    "reason": "Card not found",
    "duration_minutes": null
  }
  ```

---

## 2. Locker Assignment Channel

### 2.1 Locker Request
- **Topic**: `gymtag/locker/request`
- **Direction**: ESP32 -> Python Backend
- **Payload Schema**:
  ```json
  {
    "card_id": "RFID_CARD_STRING"
  }
  ```

### 2.2 Locker Response
- **Topic**: `gymtag/locker/response`
- **Direction**: Python Backend -> ESP32
- **Payload Schema (Assigned)**:
  ```json
  {
    "card_id": "RFID_CARD_STRING",
    "action": "assign",
    "locker_number": 1,
    "reason": "Locker #1 assigned successfully"
  }
  ```
- **Payload Schema (Released)**:
  ```json
  {
    "card_id": "RFID_CARD_STRING",
    "action": "release",
    "locker_number": 1,
    "reason": "Locker #1 released successfully"
  }
  ```
- **Payload Schema (Denied - No Lockers Free)**:
  ```json
  {
    "card_id": "RFID_CARD_STRING",
    "action": "denied",
    "locker_number": null,
    "reason": "No lockers available"
  }
  ```

---

## 3. Environment & Relay Control Channel

### 3.1 Environment Sensor Telemetry
- **Topic**: `gymtag/environment/reading`
- **Direction**: ESP32 -> Python Backend
- **Interval**: Every 5 - 10 seconds
- **Payload Schema**:
  ```json
  {
    "temperature": 34.5,
    "humidity": 82.0
  }
  ```

### 3.2 Fan Relay Control Command
- **Topic**: `gymtag/environment/fan_control`
- **Direction**: Python Backend -> ESP32
- **Trigger**: Sent only when fan state needs to change (turn ON or turn OFF)
- **Payload Schema**:
  ```json
  {
    "fan": "on",
    "reason": "Threshold exceeded! Temp: 34.5C (limit 32.0C), Humidity: 82.0% (limit 80.0%)"
  }
  ```
