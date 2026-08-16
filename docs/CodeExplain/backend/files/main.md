# `backend/app/main.py`

## Vai trò

Điểm composition root của backend: tạo repository, service, MQTT client/handler, router, CORS và static frontend.

## `lifespan(app)`

Input là FastAPI app. Khi startup, hàm kiểm tra cấu hình Firebase, khởi tạo `FirebaseRepository`, nạp ngưỡng đã lưu, tạo các service, gắn chúng vào `app.state`, nối MQTT và đăng ký asyncio loop. Khi shutdown, nó ngắt MQTT.

## Quan hệ gọi

Uvicorn/FastAPI gọi `lifespan`; các route lấy dependency từ `app.state`. MQTT callback được chuyển an toàn từ thread Paho sang event loop FastAPI.

## HTTP/static

Các router được đăng ký dưới prefix riêng. Thư mục frontend được mount ở `/public`, `/user`, `/admin`, `/shared`; `/` redirect đến `/public/`.

## Cách giải thích khi bảo vệ

“`main.py` chỉ lắp ghép hệ thống và quản lý vòng đời. Luật nghiệp vụ nằm ở service, lưu trữ nằm ở repository và transport nằm ở route/MQTT.”
