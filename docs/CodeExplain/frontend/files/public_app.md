# `frontend/public/app.js`

`initPublicDashboard()` là điểm khởi tạo. `loadInitialData()` gọi `fetchStatus()` và `fetchLockers()`; `renderEnvironment()` hiển thị nhiệt độ, độ ẩm, quạt; `renderLockers()` tính tổng/trống/hỏng và dựng lưới locker.

`setupWebSocket()` kết nối kênh public, cập nhật chỉ báo kết nối và phản ứng với event backend. File nhận JSON qua `GymTagAPI`/`wsClient`, xuất thay đổi DOM trong public dashboard.
