# Luồng REST API của backend

Frontend gọi các endpoint bằng `GymTagAPI` trừ các route cũ/được gọi trực tiếp.

## Giao diện công khai và route chung

| Method | Endpoint | Kết quả |
|---|---|---|
| GET | `/api/public/status` | Occupancy và môi trường mới nhất |
| GET | `/api/public/lockers` | Danh sách locker đã ẩn dữ liệu riêng |
| GET | `/api/lockers/logs` | Nhật ký hoạt động locker (lọc theo số tủ, mã thẻ) |
| GET | `/api/logs`, `/api/occupancy` | Log và số người hiện tại |
| GET | `/api/environment/latest`, `/history` | Reading mới nhất/lịch sử |
| POST | `/api/environment/fan` | Đổi trạng thái và gửi MQTT |
| CRUD | `/api/members`, `/api/lockers` | Route quản lý cũ, hiện không có admin dependency |

## Thành viên

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/api/user/login` | Đăng nhập member |
| POST | `/api/user/change-password` | Đổi mật khẩu |
| GET | `/api/user/me/profile` | Hồ sơ hiện tại |
| GET | `/api/user/me/history` | Lịch sử cá nhân |
| GET | `/api/user/me/locker` | Locker đang giữ |
| GET | `/api/user/me/stats` | Thống kê tập luyện |

Các route `/me/*` dùng `require_user`; các route fallback có `{card_id}` hiện đang public trong code.

## Quản trị viên

| Nhóm endpoint | Chức năng |
|---|---|
| `/api/admin/login` | Tạo JWT |
| `/api/admin/activity` | Lấy log ra vào cửa |
| `/api/admin/lockers` | Danh sách trạng thái locker chi tiết |
| `/api/admin/lockers/logs` | Lấy toàn bộ nhật ký hoạt động locker (lọc theo số tủ, mã thẻ) |
| `/api/admin/lockers...` | Force-release/assign, đổi status |
| `/api/admin/members...` | CRUD, reset password, toggle active |
| `/api/admin/environment/history` | Lịch sử môi trường |
| `/api/admin/environment/fan` | Điều khiển quạt (on/off/auto) qua service + MQTT + WS |
| `/api/admin/environment/thresholds` | Đọc/ghi ngưỡng |
| `/api/admin/telegram/test` | Gửi cảnh báo thử nghiệm tới Telegram Bot |


Ngoại trừ login, route admin phụ thuộc `require_admin`.

## Luồng chuẩn

```text
frontend request()
→ fetch kèm Bearer token nếu cần
→ FastAPI route và Pydantic validation
→ service hoặc repository
→ Firebase
→ JSON response
→ renderer DOM
```

Một số mutation còn broadcast WebSocket; route quạt publish MQTT. Force-release locker của admin chỉ thay đổi database, không mở vật lý.
