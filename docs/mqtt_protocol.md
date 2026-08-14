# GymTag MQTT Messaging Protocol Specification

- **Default MQTT Broker**: `test.mosquitto.org` (Port 1883)  
- **QoS Level**: `0` (Telemetry) / `1` (Control & State Commands)  
- **Payload Encoding**: UTF-8 JSON  
- **Base Topic Namespace**: `gymtag/*`

---

## 1. Door Access Control Channel

### 1.1 Door Scan Request
- **Topic**: `gymtag/door/checkin_request`
- **Direction**: ESP32 -> Python Backend
- **Trigger**: Fired whenever an RFID card is swiped at the door reader (RC522 #1).
- **Payload Schema**:
  ```json
  {
    "card_id": "CARD001"
  }
  ```

### 1.2 Door Scan Response
- **Topic**: `gymtag/door/checkin_response`
- **Direction**: Python Backend -> ESP32
- **Trigger**: Immediate backend validation response.

#### Case A: Access Granted (Check-in)
```json
{
  "card_id": "CARD001",
  "status": "granted",
  "action": "checkin",
  "member_name": "Nguyễn Văn A",
  "reason": "Check-in granted",
  "duration_minutes": null
}
```

#### Case B: Access Granted (Check-out with Duration Calculation)
```json
{
  "card_id": "CARD001",
  "status": "granted",
  "action": "checkout",
  "member_name": "Nguyễn Văn A",
  "reason": "Check-out granted",
  "duration_minutes": 65.2
}
```

#### Case C: Access Denied (Expired Membership / Inactive / Unknown Card)
```json
{
  "card_id": "CARD999",
  "status": "denied",
  "action": "checkin",
  "member_name": "Unknown",
  "reason": "Card not found",
  "duration_minutes": null
}
```
*(Other possible denial reasons: `"Membership expired on 2025-12-31"`, `"Member account is disabled"`)*.

---

## 2. Smart Locker Station Channel

### 2.1 Locker Request
- **Topic**: `gymtag/locker/request`
- **Direction**: ESP32 -> Python Backend
- **Trigger**: Fired when an RFID card is swiped at the locker kiosk reader (RC522 #2).
- **Payload Schema**:
  ```json
  {
    "card_id": "CARD001"
  }
  ```

### 2.2 Locker Response
- **Topic**: `gymtag/locker/response`
- **Direction**: Python Backend -> ESP32

#### Case A: Successfully Assigned Empty Locker
```json
{
  "card_id": "CARD001",
  "action": "assign",
  "locker_number": 3,
  "reason": "Locker #3 assigned successfully"
}
```

#### Case B: Successfully Released Existing Locker
```json
{
  "card_id": "CARD001",
  "action": "release",
  "locker_number": 3,
  "reason": "Locker #3 released successfully"
}
```

#### Case C: Locker Allocation Denied (All Lockers Occupied or Broken)
```json
{
  "card_id": "CARD001",
  "action": "denied",
  "locker_number": null,
  "reason": "No vacant lockers available"
}
```

---

## 3. Environment Monitoring & Cooling Fan Channel

### 3.1 Environment Sensor Telemetry
- **Topic**: `gymtag/environment/reading`
- **Direction**: ESP32 -> Python Backend
- **Interval**: Periodically published every 5 to 10 seconds.
- **Payload Schema**:
  ```json
  {
    "temperature": 33.5,
    "humidity": 82.0
  }
  ```

### 3.2 Fan Relay Control Command
- **Topic**: `gymtag/environment/fan_control`
- **Direction**: Python Backend -> ESP32
- **Trigger**: Sent only when a change in fan operating state is required (state transition).

#### Case A: Turn Fan ON (Exceeded Dynamic Thresholds)
```json
{
  "fan": "on",
  "reason": "Threshold exceeded! Temp: 33.5°C (limit 32.0°C), Humidity: 82.0% (limit 80.0%)"
}
```

#### Case B: Turn Fan OFF (Environment Normalized)
```json
{
  "fan": "off",
  "reason": "Environment returned to normal: Temp: 29.0°C, Humidity: 65.0%"
}
```

#### Case C: Manual Control by Admin Dashboard
```json
{
  "fan": "on",
  "reason": "Manual control (ON) by Admin"
}
```
