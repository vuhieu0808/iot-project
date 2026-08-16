# `frontend/user/app.js`

`initUserPortal()` cấu hình xác thực, WebSocket và modal đổi mật khẩu. `setupAuth()` gọi API đăng nhập, lưu `gymtag_user_token`, logout và đổi trạng thái login/dashboard. `loadUserDashboard()` tải dữ liệu cá nhân.

Các renderer chính là `renderProfile()`, `renderLocker()`, `renderStats()` và `renderHistory()`. `setupChangePasswordModal()` kiểm tra dữ liệu form trước khi gọi API. File nhận credentials hoặc event UI, xuất request REST và cập nhật DOM.
