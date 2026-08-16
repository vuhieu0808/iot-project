# Các file route của backend

Các file `backend/app/api/routes_*.py` khai báo REST theo miền public, user, admin, locker, member, access và environment. Route parse path/query/body bằng model Pydantic, áp dụng dependency xác thực khi cần, gọi service/repository và trả JSON/HTTP error.

`websocket.py` khai báo các endpoint WebSocket theo nhóm người nhận. Danh mục endpoint và quan hệ gọi được tổng hợp tại [luồng API](../API_FLOW.md) và [luồng WebSocket](../WEBSOCKET_FLOW.md).
