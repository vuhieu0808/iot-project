# Luồng module locker

## Phần cứng ESP32

- MFRC522: SPI SCK18, MISO19, MOSI23, SS21, RST4.
- LCD RFID station: I2C SDA22, SCL25, address `0x27`.
- Servo locker #1–#3: GPIO26, GPIO27, GPIO32.
- Door button #1–#3: GPIO13, GPIO14, GPIO16, `INPUT_PULLUP`.
- RELEASE chung: GPIO33, `INPUT_PULLUP`.

Door pressed/LOW là closed; released/HIGH là open. Servo 0° là locked, 90° là unlocked.

## Assign/access

```text
RFID scan → MQTT operation=scan → backend assign/access
→ LockerController hiển thị LCD assign/authorized
→ servo đúng locker unlock
→ chỉ door của locker active CLOSED → OPEN → CLOSED
→ servo lock → cooldown → IDLE
```

## Release

RELEASE chỉ đặt `releasePending` trong session. Sau door open/close, servo lock trước, rồi ESP32 publish `operation=release`. Response release hiển thị `Locker Released` và chỉ clear session; backend ownership flow không thay đổi.

## Timeout

Backend: 8 giây. Door action: 30 giây. RFID/state cooldown: 5 giây. Tất cả dùng `millis()`, không blocking MQTT/DHT/display.
