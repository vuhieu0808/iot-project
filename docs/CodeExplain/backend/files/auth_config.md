# Xác thực và cấu hình backend

`backend/app/config.py` đọc cấu hình môi trường: Firebase, MQTT, CORS và thông tin/token liên quan. `backend/app/auth.py` cung cấp tạo/kiểm tra token và dependencies bảo vệ route admin/user. `.env.example` mô tả tên biến cấu hình; `.env` và credential Firebase là dữ liệu triển khai, không nên đưa vào tài liệu hay commit bí mật.

`main.py` sử dụng settings để khởi tạo repository, services, MQTT và CORS. Frontend gửi bearer token do endpoint login cấp; public endpoint không cần token.
