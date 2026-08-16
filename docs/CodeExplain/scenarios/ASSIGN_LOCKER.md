# Kịch bản: tự động cấp locker

```mermaid
sequenceDiagram
  participant RFID as RC522 / ESP32
  participant MQTT as MQTT broker
  participant Handler as backend mqtt/handlers.py
  participant Service as LockerService
  participant DB as Firebase
  RFID->>MQTT: gymtag/locker/request {operation:"scan",card_id}
  MQTT->>Handler: _handle_locker_request()
  Handler->>Service: process_locker_scan(card_id)
  Service->>DB: get_member + get_locker_by_card + find_vacant_locker
  Service->>DB: update locker occupied
  Service-->>Handler: granted, action=assign, locker_number
  Handler->>MQTT: gymtag/locker/response
  MQTT-->>RFID: JSON response
  RFID->>RFID: pulse relay, enter MEMBER_SESSION
```

Điều kiện: card thuộc member hợp lệ, chưa giữ locker và còn locker `vacant`. Locker được chọn theo số nhỏ nhất. ESP32 chỉ kích relay khi response được cấp quyền và có số locker điều khiển được.
