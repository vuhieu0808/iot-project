# Các file của module locker

## `esp32/include/lockerRFID.h`

Khai báo API RFID: `begin()` và `readCard(String&)`. `String&` là tham chiếu C++; hàm ghi UID chuẩn hóa vào object của caller.

## `esp32/src/lockerRFID.cpp`

Namespace ẩn giữ trạng thái riêng của file: `reader`, `lastAcceptedAt`, `hasAcceptedCard`.

- `normalizeUid(const MFRC522::Uid&)`: nhận UID RC522 và trả Arduino `String` uppercase, hai ký tự hex mỗi byte.
- `begin()`: được `main.setup()` gọi để khởi động SPI/RC522.
- `readCard(String&)`: mỗi loop kiểm tra cooldown, phát hiện/đọc card, chuẩn hóa UID, gọi `PICC_HaltA()` và `PCD_StopCrypto1()`. Chỉ trả `true` khi chấp nhận một lần đọc.

## `esp32/include/locker_controller.h`

Khai báo `begin`, `update`, `handleCardScan`, `handleMqttPayload`. Payload MQTT dùng con trỏ buffer chỉ đọc và độ dài tường minh.

## `esp32/src/locker_controller.cpp`

`enum class State` tạo các trạng thái có scope rõ ràng. Card ID, member, số locker, timer và trạng thái relay/nút được giữ riêng trong `.cpp`.

- `begin()`: đưa relay đã map về inactive và cấu hình nút pull-up tùy chọn.
- `handleCardScan()`: chỉ nhận card ở `IDLE`, lưu card và publish operation `scan`.
- `handleMqttPayload()`: parse JSON, đối chiếu card/state/action/số locker rồi quyết định mở relay hoặc chuyển state.
- `update()`: scheduler không blocking cho pulse relay, timeout backend, debounce/release, timeout phiên và cooldown.
- `openLocker()` và `stopRelay()`: ánh xạ số locker bắt đầu từ 1 sang mảng GPIO bắt đầu từ 0, có kiểm tra biên.
- `releaseButtonPressed()`: debounce nút active-low bằng `millis()`.

## `esp32/include/hardware_config.h`

Nguồn tập trung cho GPIO, polarity và timing. Mapping relay/nút bị tắt có chủ ý để tránh kích nhầm chân chưa xác nhận.

## `esp32/src/main.cpp`

Composition root của firmware: khởi tạo module, chuyển MQTT topic đến controller và gọi các hàm `update()` trong loop.

## Quan hệ gọi

```text
main.loop → LockerRfid::readCard → LockerController::handleCardScan
MqttManager callback → main.routeMqttMessage → LockerController::handleMqttPayload
LockerController → MqttManager::publish
LockerController → digitalWrite/read GPIO
```

## Cách giải thích khi bảo vệ

“Locker được tách thành RFID reader và controller. RFID chỉ đọc/chuẩn hóa UID; controller giữ state machine, dựng MQTT request và kiểm tra response. State có thể ghi được giấu trong một file để tránh global state rải rác.”
