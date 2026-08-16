# Các file của module môi trường

## `esp32/include/environment_sensor.h`

Khai báo API tối thiểu `begin()` và `update()`.

## `esp32/src/environment_sensor.cpp`

- Giữ `DHTesp sensor` và `lastReadingAt` ở phạm vi riêng của file.
- `begin()` cấu hình DHT22 bằng `HardwareConfig::DHT_PIN`.
- `update()` giới hạn tần suất 5000 ms, đọc cảm biến, dựng JSON và gọi `MqttManager::publish()`.
- Tác dụng phụ: ghi Serial và publish MQTT.

## Các file backend liên quan

- `mqtt/handlers.py`: parse payload và phát event.
- `services/environment_service.py`: áp dụng ngưỡng, trạng thái quạt và cảnh báo.
- `repositories/firebase_repo.py`: đọc/ghi Firebase.

## Các file frontend liên quan

`frontend/public/app.js` và `frontend/admin/app.js` hiển thị reading mới nhất/lịch sử và phản ứng với `environment_update`.
