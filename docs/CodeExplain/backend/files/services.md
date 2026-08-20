# Các file service của backend

## `access_service.py`

Kiểm tra member, trạng thái active và hạn membership; tạo check-in/check-out log granted/denied. Checkout thành công có thể tính `duration_minutes` từ check-in đang hoạt động.

## `environment_service.py`
 
Chuyển telemetry thành `EnvironmentReading` kèm timestamp, kiểm tra sanity check loại bỏ ngoại lai, so sánh ngưỡng với cơ chế Hysteresis Deadband (tránh chập chờn relay), quản lý chế độ Admin Manual Override (ưu tiên tuyệt đối) và Auto mode, lưu reading và gọi `NotificationService`. Đồng thời cung cấp lịch sử, reading mới nhất, và cập nhật ngưỡng động.
 
## `occupancy_service.py`
 
Ủy quyền phép tính số người hiện tại cho repository.
 
## `notification_service.py`
 
Gửi cảnh báo Telegram bằng HTTP (ép buộc IPv4 Transport để tránh nghẽn IPv6 tại Việt Nam, hỗ trợ proxy) khi có token/chat ID; định dạng HTML tiếng Việt có timestamp; nếu thiếu cấu hình thì log và bỏ qua an toàn.


## Quan hệ gọi

MQTT handler gọi access/environment/occupancy. REST route gọi environment/occupancy. Mọi thao tác lưu trữ đều đi qua repository.

## Cách giải thích khi bảo vệ

“Service biểu diễn use case chứ không biểu diễn transport. `AccessService` được MQTT gọi mà không biết Paho; `EnvironmentService` được MQTT hoặc REST gọi mà không biết browser hay thiết bị.”
