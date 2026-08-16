# Kịch bản: cập nhật môi trường

Mỗi khoảng 5 giây, `EnvironmentSensor::update()` đọc DHT22 và publish `{temperature, humidity, fan_on}` lên `gymtag/environment/reading`. Backend `handle_environment_reading()` parse/validate model, lưu một reading mới tại `environment_readings/{uuid}`, rồi phát event WebSocket.

Public/admin frontend nhận event realtime hoặc lấy snapshot qua REST và render nhiệt độ, độ ẩm, trạng thái quạt. Nếu DHT trả giá trị không hợp lệ, ESP32 bỏ lần publish đó.
