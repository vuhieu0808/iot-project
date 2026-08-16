# Luồng WebSocket

## Endpoint

- `/ws/public` và alias `/ws`: kết nối public.
- `/ws/admin?token=<JWT>`: kiểm tra admin token trước khi accept.

`TieredConnectionManager` giữ hai danh sách connection trong bộ nhớ. Disconnect/lỗi gửi sẽ loại socket. Client gửi `ping` nhận `{"type":"pong"}`.

## Event

| Event | Nguồn | Đối tượng | Phản ứng frontend |
|---|---|---|---|
| `checkin_event`, `checkout_event` | MQTT cửa | Admin | Reload overview/log |
| `occupancy_update` | Access handler | Public | Cập nhật số người |
| `locker_event` | MQTT/admin locker | Admin | Render/reload chi tiết |
| `locker_status_update` | MQTT/admin locker | Public | Render trạng thái ẩn danh |
| `environment_update` | MQTT/route môi trường | Tùy caller | Render môi trường/lịch sử |
| `threshold_update` | Route admin | Client được broadcast | Cập nhật control ngưỡng |

Payload admin có thể chứa card/timestamp; payload public loại các field riêng tư.

## Kết nối frontend

`GymTagWebSocket.connect()` dựng URL `ws://` hoặc `wss://`, parse `{type,data}` và dispatch callback. Khi đóng, client reconnect với delay tăng dần, tối đa 10 giây.

REST lấy snapshot/thực hiện mutation; WebSocket đẩy event đến browser; MQTT trao đổi với thiết bị. State WebSocket chỉ ở bộ nhớ một process backend.

Xem [realtime frontend](../frontend/REALTIME_FLOW.md) và [file WebSocket](files/websocket.md).
