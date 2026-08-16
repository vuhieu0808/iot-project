# Luồng module MQTT trên ESP32

## Mục đích

Sở hữu duy nhất một `WiFiClient` và một `PubSubClient`, quản lý kết nối/reconnect, subscription và publish. Các module khác không tự tạo MQTT client.

## Khởi tạo và vòng lặp

```text
MqttManager::begin(routeMqttMessage)
→ lưu callback
→ cấu hình broker/callback của PubSubClient
→ bắt đầu kết nối Wi-Fi

loop()
→ MqttManager::update()
→ thử lại Wi-Fi mỗi 10 giây, hoặc MQTT mỗi 5 giây, hoặc mqttClient.loop()
```

Khi kết nối MQTT thành công, module subscribe QoS 0 vào topic điều khiển quạt và phản hồi locker. Client ID chứa chip ID từ eFuse để hạn chế trùng lặp.

## Luồng callback

Callback nội bộ nhận topic/payload rồi chuyển nguyên dữ liệu đến `routeMqttMessage()` trong `main.cpp`. `main` định tuyến sang `FanController` hoặc `LockerController`.

## Dữ liệu vào/ra

- Input: trạng thái Wi-Fi, message từ broker, topic và `String` cần publish.
- Output: subscription, message MQTT không retained và lời gọi callback.

## Lỗi

Module log lỗi kết nối và thử lại không blocking. `publish()` trả `false` nếu MQTT chưa kết nối.

Xem [chi tiết file](FILES.md) và [giao thức](../../02_MQTT_PROTOCOL.md).
