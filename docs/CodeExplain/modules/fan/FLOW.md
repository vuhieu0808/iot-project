# Luồng module quạt

## Mục đích

Nhận quyết định bật/tắt từ backend và chuyển thành mức điện áp GPIO trên ESP32. Chính sách ngưỡng nằm ở backend, không nằm trong firmware.

## Luồng tự động

```text
DHT22 → EnvironmentService so sánh ngưỡng
→ MQTT gymtag/environment/fan_control
→ MqttManager callback
→ FanController::handleMqttPayload()
→ GPIO 12 HIGH/LOW
```

## Luồng thủ công

Admin UI gửi `POST /api/admin/environment/fan`; backend ghi nhận trạng thái, publish cùng MQTT topic và phát dữ liệu môi trường qua WebSocket.

## Payload và GPIO

Payload là `{"fan":"on|off","reason":"..."}`. `FAN_PIN=12`; `HIGH` là bật, `LOW` là tắt. `begin()` luôn đưa chân về `LOW`.

## Xử lý lỗi

JSON sai hoặc lệnh không phải `on`/`off` bị bỏ qua và không đổi GPIO.

Xem [kịch bản quạt](../../scenarios/FAN_CONTROL.md) và [giao thức MQTT](../../02_MQTT_PROTOCOL.md).
