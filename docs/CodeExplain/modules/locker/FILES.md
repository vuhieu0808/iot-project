# Các file của module locker

## `esp32/include/lockerRFID.h` và `src/lockerRFID.cpp`

`begin()` khởi tạo SPI/MFRC522. `readCard(String&)` đọc UID, chuẩn hóa uppercase không dấu `:`, halt card và áp dụng cooldown 5 giây.

## `esp32/include/hardware_config.h`

Tập trung mapping 4 servo, 4 door switch, release button, góc servo và timeout:

```text
servo: 25, 26, 27, 32
door:  13, 14, 16, 17
release: 33
locked/unlocked: 0°/90°
```

## `esp32/src/locker_controller.cpp`

- `begin()`: attach bốn servo, đặt 0°, cấu hình năm button `INPUT_PULLUP`.
- `handleCardScan()`: chỉ nhận ở `IDLE`, publish scan và vào `WAITING_BACKEND`.
- `handleMqttPayload()`: kiểm tra card/state/action/số locker; assign/access unlock servo; release response chỉ clear session.
- `update()`: debounce input, đánh dấu release pending, theo dõi door transition, timeout và cooldown.
- `unlockLocker()`/`lockLocker()`: ghi góc servo đã định nghĩa tập trung.
- `isDoorClosed()`: đọc stable door state của đúng locker.
- `finishPhysicalSession()`: khóa servo trước; chỉ publish release nếu `releasePending`.

`DebouncedInput` giữ raw/stable/changedAt cho từng button. Chỉ door switch của `currentLockerNumber` tác động session.

## `esp32/src/main.cpp`

Khởi tạo RFID/controller/MQTT và chuyển `gymtag/locker/response` đến `LockerController::handleMqttPayload()`.

## Dependency

```text
LockerRfid → LockerController
LockerController → ESP32Servo + GPIO + MqttManager
MqttManager → broker MQTT
backend MQTT handler → LockerService → Firebase
```

## Cách giải thích khi bảo vệ

“Backend quyết định ownership; ESP32 quyết định physical safety. Servo chỉ khóa sau khi cửa đã đi từ đóng sang mở rồi đóng lại. Release database chỉ xảy ra sau khi servo đã khóa.”
