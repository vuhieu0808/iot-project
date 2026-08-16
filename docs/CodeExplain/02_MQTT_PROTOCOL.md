# Giao thức MQTT

## Danh sách topic

| Topic | Bên publish | Bên subscribe | Mục đích | Payload chính |
|---|---|---|---|---|
| `gymtag/door/checkin_request` | Thiết bị | Backend | Yêu cầu check-in | `card_id` |
| `gymtag/door/checkout_request` | Thiết bị | Backend | Yêu cầu check-out | `card_id` |
| `gymtag/locker/request` | ESP32 | Backend | Scan/access hoặc release | `card_id`, `operation`, tùy chọn `locker_number` |
| `gymtag/environment/reading` | ESP32 | Backend | Telemetry DHT22 | `temperature`, `humidity`, `fan_on` |
| `gymtag/door/checkin_response` | Backend | Thiết bị | Kết quả check-in | kết quả access |
| `gymtag/door/checkout_response` | Backend | Thiết bị | Kết quả check-out | kết quả access |
| `gymtag/locker/response` | Backend | ESP32 | Assign/access/release/denied | kết quả locker |
| `gymtag/environment/fan_control` | Backend | ESP32 | Bật/tắt quạt | `fan`, `reason` |

Hằng topic nằm trong `backend/app/mqtt/topics.py`. ESP32 hiện chỉ subscribe fan control và locker response; source chưa có firmware RFID cửa.

## Yêu cầu và phản hồi locker

Bên gửi là `LockerController::publishOperation()`; bên nhận là `_handle_locker_request()`.

```json
{"card_id":"04A13F92","operation":"scan"}
```

Thiếu `operation` vẫn được hiểu là `scan` để tương thích ngược.

```json
{"card_id":"04A13F92","operation":"release","locker_number":3}
```

Các action phản hồi có thể là `assign`, `access`, `release`, `denied` và đi kèm `card_id`, `locker_number`, `member_name`, `reason`.

```json
{"card_id":"04A13F92","action":"assign","locker_number":3,"member_name":"Nguyen Van A","reason":"Locker #3 assigned successfully"}
```

```json
{"card_id":"UNKNOWN","action":"denied","locker_number":null,"member_name":null,"reason":"RFID card is not registered"}
```

## Cửa check-in/check-out

Request có dạng `{"card_id":"04A13F92"}`. Response do `AccessService` tạo chứa `card_id`, `member_name`, `action`, `status`, `reason`, `timestamp` và có thể có `duration_minutes`.

## Reading môi trường

```json
{"temperature":29.4,"humidity":71.2,"fan_on":false}
```

Backend chấp nhận số JSON hoặc chuỗi chuyển được bằng `float()`.

## Điều khiển quạt

```json
{"fan":"on","reason":"Temperature or humidity above threshold"}
```

Chỉ `on` và `off` hợp lệ. `FanController::handleMqttPayload()` là bên nhận trên ESP32.

## Hành vi kết nối

- Broker firmware: `test.mosquitto.org:1883`; backend lấy broker/port từ settings.
- Client ID backend mặc định: `gymtag_backend_service`; ESP32: `gymtag_locker_<efuse>`.
- QoS 0, publish không retained.
- Backend dùng Paho `loop_start()`; ESP32 gọi `MqttManager::update()` và `PubSubClient::loop()`.
- ESP32 thử Wi-Fi lại mỗi 10 giây, MQTT mỗi 5 giây và khôi phục subscription sau reconnect.
- Chưa có TLS/authentication; broker công cộng chỉ phù hợp demo.

## Xử lý lỗi

- JSON sai hoặc thiếu card: backend log và không phản hồi.
- Operation locker không hỗ trợ: trả `denied`.
- Firmware nhận JSON sai, card cũ, sai state hoặc số không hợp lệ: bỏ qua, không kích GPIO.
- Broker/backend mất kết nối: publish thất bại hoặc timeout sau 8000 ms.

Xem [luồng MQTT backend](backend/MQTT_FLOW.md) và [state machine locker](modules/locker/STATE_MACHINE.md).
