# Các file của module quạt

## `esp32/include/fan_controller.h`

Khai báo `begin()` và `handleMqttPayload()` trong namespace `FanController`.

## `esp32/src/fan_controller.cpp`

- `begin()` cấu hình `HardwareConfig::FAN_PIN` là output và tắt quạt.
- Handler parse JSON, yêu cầu field `fan` bằng `on` hoặc `off`, rồi ghi GPIO.
- Input là con trỏ/độ dài buffer do PubSubClient sở hữu; handler đọc đồng bộ ngay trong callback.

## `esp32/include/hardware_config.h`

Định nghĩa `FAN_PIN=12`; logic active-high nằm trực tiếp trong controller.

## Cách giải thích khi bảo vệ

“Module quạt không quyết định lúc nào cần làm mát; `EnvironmentService` ở backend quyết định. Firmware chỉ kiểm tra lệnh và ánh xạ on/off sang GPIO 12, qua đó tách chính sách khỏi thao tác phần cứng.”
