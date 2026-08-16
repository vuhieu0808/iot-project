# Các file MQTT trên ESP32

## `esp32/include/mqtt_manager.h`

Định nghĩa `MessageHandler`, một kiểu callback bằng con trỏ hàm. Callback giúp module MQTT chuyển message mà không cần import phần triển khai quạt/locker, nhờ đó giảm coupling.

API công khai:

- `begin(handler)`: cấu hình mạng và callback.
- `update()`: tiến triển trạng thái Wi-Fi/MQTT.
- `publish(topic, payload)`: gửi message không retained.
- `connected()`: cho biết trạng thái broker.

## `esp32/src/mqtt_manager.cpp`

Giữ credentials, broker `test.mosquitto.org:1883`, các timer thử lại và hai network client ở phạm vi file. `connectMqtt()` dùng client ID `gymtag_locker_<efuse>` và khôi phục subscription sau mỗi lần reconnect.

`update()` chủ ý return sớm: chỉ lớp hợp lệ mới chạy tiếp — Wi-Fi trước, MQTT sau, cuối cùng mới đến network loop. Các lần thử lại đều dùng phép trừ `millis()` unsigned nên vẫn xử lý đúng khi timer tràn.

## `esp32/src/main.cpp`

`routeMqttMessage()` so sánh chính xác topic và chuyển payload đến controller tương ứng. `loop()` gọi `MqttManager::update()` trước các module nghiệp vụ.

## Cách giải thích khi bảo vệ

“MQTT manager sở hữu một client và che giấu chi tiết reconnect. Nó nhận con trỏ hàm từ main nên có thể chuyển topic/payload thô mà không biết module nghiệp vụ. Reconnect không blocking nên DHT, RFID và nút vẫn tiếp tục chạy.”
