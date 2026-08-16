# Các file service của backend

## `access_service.py`

Kiểm tra member, trạng thái active và hạn membership; tạo check-in/check-out log granted/denied. Checkout thành công có thể tính `duration_minutes` từ check-in đang hoạt động.

## `environment_service.py`

Chuyển telemetry thành `EnvironmentReading`, so sánh ngưỡng, giữ trạng thái quạt trong bộ nhớ, lưu reading và gọi `NotificationService`. Đồng thời cung cấp lịch sử, reading mới nhất, điều khiển thủ công và cập nhật ngưỡng.

## `occupancy_service.py`

Ủy quyền phép tính số người hiện tại cho repository.

## `notification_service.py`

Gửi cảnh báo Telegram bằng HTTP khi có token/chat ID; nếu thiếu cấu hình thì log và bỏ qua an toàn.

## Quan hệ gọi

MQTT handler gọi access/environment/occupancy. REST route gọi environment/occupancy. Mọi thao tác lưu trữ đều đi qua repository.

## Cách giải thích khi bảo vệ

“Service biểu diễn use case chứ không biểu diễn transport. `AccessService` được MQTT gọi mà không biết Paho; `EnvironmentService` được MQTT hoặc REST gọi mà không biết browser hay thiết bị.”
