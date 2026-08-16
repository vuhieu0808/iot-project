# `frontend/shared/js/websocket.js`

## Vai trò

`GymTagWebSocket` quản lý một kết nối WebSocket dùng chung.

- `getWsUrl(path)`: tạo URL `ws:`/`wss:` từ API base URL.
- `connect(path, onMessage, onStatusChange)`: mở socket, parse JSON và báo trạng thái.
- `scheduleReconnect()`: backoff tăng dần, giới hạn bởi `maxReconnectDelay` 10 giây.
- `disconnect()`: chủ động đóng và không reconnect.

Input là path/callback; output là event đưa vào callback và thay đổi trạng thái kết nối. `wsClient` được import bởi public, user và admin app.
