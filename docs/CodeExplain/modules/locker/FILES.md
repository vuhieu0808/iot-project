# Các file module locker ESP32

## `esp32/include/hardware_config.h`

Chứa GPIO trực tiếp cho ba servo, ba door switch, Release và LCD I2C; cũng chứa góc servo, debounce và timeout.

## `esp32/src/locker_controller.cpp`

- `begin()`: attach ba servo, đặt 0° và cấu hình bốn input `INPUT_PULLUP`.
- `handleCardScan()`: publish scan khi state là `IDLE`.
- `handleMqttPayload()`: validate response, hiển thị LCD, unlock servo đúng locker hoặc show denied.
- `update()`: debounce mọi door/release và update từng `LockerSession` độc lập cho CLOSED → OPEN → CLOSED, timeout và release response.
- `lockLocker()` / `unlockLocker()`: API vật lý tập trung.
- `isDoorClosed()` / `isDoorOpen()`: đọc state door đúng locker active.

## `esp32/src/display_controller.cpp`

Chỉ render LCD1602 I2C: idle, assign, access, denied và release. Message tự trở về idle sau 4 giây bằng `millis()`; không MQTT parsing.

## Dependency

```text
LockerRfid → one pending scan → LockerController `lockers[3]` → DisplayController + Servo/GPIO + MqttManager
MqttManager → broker MQTT → backend LockerService → Firebase
```
