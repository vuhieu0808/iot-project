# `backend/app/api/websocket.py`

## Mục đích

Quản lý hai nhóm WebSocket public/admin và broadcast event JSON.

## `TieredConnectionManager`

Giữ hai danh sách connection trong bộ nhớ. `connect_*` accept và thêm socket; `disconnect_*` loại bỏ; `_send_to_list()` serialize một lần, gửi tuần tự và dọn connection lỗi. `broadcast()` gửi đến cả hai nhóm.

## Endpoint

Endpoint public chấp nhận kết nối ngay. Endpoint admin kiểm tra token trên query bằng `verify_admin_token`; client không hợp lệ bị đóng với mã vi phạm chính sách.

## Xử lý lỗi

`WebSocketDisconnect` và exception thông thường đều loại connection. Hiện chưa có broker/backplane bền vững cho WebSocket event.

## Cách giải thích khi bảo vệ

“WebSocket manager giúp backend chủ động đẩy thay đổi mà browser không cần poll liên tục. Admin và public được tách để card ID chỉ xuất hiện ở kênh admin.”
