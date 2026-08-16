# `frontend/shared/js/api.js`

## Vai trò

REST client dùng chung. `request()` dựng URL, thêm `Content-Type`, đọc token admin/user từ `sessionStorage`, gọi `fetch`, parse JSON và chuẩn hóa lỗi HTTP.

`GymTagAPI` nhóm các lời gọi public, xác thực user/admin, dữ liệu user, CRUD member/locker/log, lịch sử môi trường, ngưỡng và điều khiển quạt. Input là tham số JavaScript/body object; output là Promise trả JSON backend hoặc ném `Error`.

Được gọi bởi ba file `app.js`; gọi các endpoint mô tả tại [API flow](../../backend/API_FLOW.md).
