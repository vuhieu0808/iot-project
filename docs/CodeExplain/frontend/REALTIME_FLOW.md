# Luồng realtime của frontend

1. Public và user `app.js` gọi `wsClient.connect('/ws/public')`; admin dùng `/ws/admin?token=<JWT>` sau khi đăng nhập.
2. `GymTagWebSocket` đổi protocol HTTP(S) thành WS(S), parse JSON và chuyển message cho callback.
3. Backend phát event sau khi xử lý MQTT hoặc thay đổi dữ liệu qua API.
4. Callback của từng giao diện cập nhật trực tiếp phần đơn giản hoặc gọi lại REST để lấy snapshot nhất quán.
5. Khi mất kết nối, client reconnect với backoff lũy tiến, tối đa 10 giây.

WebSocket chỉ là kênh server → browser trong code hiện tại; thao tác browser → server vẫn dùng REST. Xem [WebSocket backend](../backend/WEBSOCKET_FLOW.md) và [luồng MQTT](../backend/MQTT_FLOW.md).
