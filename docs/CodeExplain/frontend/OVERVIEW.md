# Tổng quan frontend

Frontend là ứng dụng JavaScript thuần, chia thành ba giao diện: `public`, `user` và `admin`. Mỗi giao diện có HTML/CSS riêng nhưng dùng chung `shared/js/api.js`, `shared/js/websocket.js` và các tiện ích hiển thị.

| Khu vực | Điểm vào | Trách nhiệm |
|---|---|---|
| Public | `frontend/public/index.html`, `app.js` | Hiển thị môi trường và trạng thái locker công khai |
| User | `frontend/user/index.html`, `app.js` | Đăng nhập bằng card ID/mật khẩu, hồ sơ, locker và lịch sử cá nhân |
| Admin | `frontend/admin/index.html`, `app.js` | Tổng quan, thành viên, locker, log, môi trường và điều khiển quạt |
| Shared | `frontend/shared/js/` | REST client, WebSocket client và tiện ích dùng chung |

Frontend không kết nối MQTT trực tiếp. Mọi lệnh và dữ liệu đi qua REST/WebSocket của FastAPI; backend là MQTT client duy nhất ở phía server.

Xem [luồng dữ liệu](DATA_FLOW.md), [realtime](REALTIME_FLOW.md) và [tổng quan hệ thống](../00_SYSTEM_OVERVIEW.md).
