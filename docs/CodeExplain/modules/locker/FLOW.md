# Luồng module locker

## Phần cứng

- MFRC522: SCK18, MISO19, MOSI23, SS21, RST4.
- Servo #1–#4: GPIO 25, 26, 27, 32.
- Door button #1–#4: GPIO 13, 14, 16, 17, `INPUT_PULLUP`.
- RELEASE chung: GPIO33, `INPUT_PULLUP`.

Servo dùng ESP32Servo: 0° là locked, 90° là unlocked. Door button pressed/LOW nghĩa là closed; released/HIGH nghĩa là open.

## Luồng assign/access

```text
RFID scan
→ publish operation=scan
→ WAITING_BACKEND
→ backend assign/access
→ servo UNLOCKED và giữ 90°
→ WAIT_DOOR_OPEN, bắt buộc thấy CLOSED → OPEN
→ WAIT_DOOR_CLOSE
→ thấy OPEN → CLOSED
→ servo LOCKED 0°
→ nếu không releasePending: COOLDOWN → IDLE
```

Backend assign làm locker occupied trước khi response. Access không đổi ownership. Scan không bao giờ tự release.

## Luồng release

Trong `WAIT_DOOR_OPEN` hoặc `WAIT_DOOR_CLOSE`, nhấn RELEASE chỉ đặt `releasePending=true`. Firmware chưa gửi MQTT và backend chưa chuyển vacant.

Sau khi door đã open rồi close:

```text
servo LOCKED
→ publish operation=release cùng locker_number
→ WAITING_RELEASE_RESPONSE
→ backend validate và ghi vacant
→ response release
→ clear session; không mở servo lần nữa
```

## Timeout

- Backend: 8000 ms.
- Door action: 30000 ms.
- Cooldown RFID/state: 5000 ms.

Nếu door vẫn closed và chưa từng mở sau 30 giây, servo khóa và session kết thúc. Nếu door đang open, firmware chỉ log rồi tiếp tục chờ, không ép khóa cửa đang mở.

## Tính không blocking

RFID cooldown, debounce, backend timeout và door timeout đều dùng `millis()`. `MqttManager::update()`, DHT và door detection tiếp tục chạy; không có `delay()` trong controller.

Xem [state machine](STATE_MACHINE.md), [chi tiết file](FILES.md) và [kịch bản release](../../scenarios/RELEASE_LOCKER.md).
