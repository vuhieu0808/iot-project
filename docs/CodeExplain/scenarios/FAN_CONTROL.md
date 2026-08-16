# Kịch bản: điều khiển quạt

Admin nhấn bật/tắt quạt → `setupFanControl()` gọi REST fan-control → backend publish `{"fan":"on"|"off","reason":"..."}` lên `gymtag/environment/fan_control`. `MqttManager` trên ESP32 đã subscribe topic này; callback chuyển payload cho `FanController`, ghi GPIO 12 active-high.

Trạng thái quạt được phản ánh trong reading môi trường kế tiếp và quay về backend/frontend. Vì topic được publish không retained, ESP32 phải đang kết nối để nhận lệnh; sau reconnect, trạng thái mới được đồng bộ khi có lệnh/logic tiếp theo.
