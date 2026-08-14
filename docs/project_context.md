# GymTag - Hệ thống Quản lý Phòng Gym Thông minh Ứng dụng IoT & RFID

## 1. Thông tin chung

- **Đồ án môn học**: Vật lý cho Công nghệ thông tin
- **Trường**: Trường Đại học Khoa học Tự nhiên, ĐHQG TP. Hồ Chí Minh
- **Khoa**: Công nghệ thông tin
- **Nhóm sinh viên thực hiện (Nhóm 6)**:
  - **Vũ Trần Minh Hiếu** - MSSV: `24127003`
  - **Hoàng Đức Thịnh** - MSSV: `24127240`
  - **Trần Viết Bảo** - MSSV: `24127270`
- **Proposal đồ án**: [Proposal Document](../24127003_24127240_24127270.pdf)

---

## 2. Mục đích và Ý nghĩa Đề tài

Trong các phòng gym truyền thống, việc quản lý thành viên ra vào, cấp phát chìa khóa tủ đồ (locker) và giám sát môi trường không khí thường thực hiện thủ công, dễ gây ùn tắc tại quầy lễ tân, nhầm lẫn tủ đồ và thiếu khả năng điều hòa môi trường tự động khi phòng tập quá tải.

**GymTag** giải quyết triệt để các vấn đề trên thông qua giải pháp IoT toàn diện:
1. **Kiểm soát ra vào tự động bằng thẻ RFID**: Tự động nhận diện thành viên, kiểm tra trạng thái kích hoạt và thời hạn gói tập, điều khiển khóa cửa servo, tính toán chính xác thời lượng tập luyện cho từng buổi tập.
2. **Cấp phát & thu hồi tủ đồ thông minh (Smart Locker)**: Quẹt thẻ tại trạm locker để nhận tủ trống đầu tiên hoặc mở khóa trả tủ tự động, ngăn ngừa việc chiếm dụng tủ trái phép.
3. **Giám sát & Điều hòa vi khí hậu tự động**: Đọc dữ liệu nhiệt độ và độ ẩm từ cảm biến DHT22 theo thời gian thực. Tự động bật quạt thông gió qua relay khi môi trường vượt ngưỡng cho phép, đồng thời gửi cảnh báo tức thì về Telegram của người quản lý.
4. **Hệ thống Web Dashboard phân quyền 3 tầng**:
   - **Màn hình giám sát công cộng (Public Display)**: Hiển thị sĩ số phòng tập, sơ đồ locker và chỉ số môi trường.
   - **Cổng thông tin hội viên (User Portal)**: Cho phép hội viên tra cứu hạn thẻ, thời lượng tập, lịch sử vào ra và đổi mật khẩu cá nhân.
   - **Bảng điều khiển quản trị (Admin Portal)**: Quản lý thành viên, điều khiển tủ đồ, xem log sự kiện realtime, bật/tắt quạt thủ công và cấu hình ngưỡng nhiệt độ & độ ẩm linh hoạt (Dynamic Thresholds).

---

## 3. Kiến trúc Tổng thể & Công nghệ Sử dụng

```
+--------------------------------------------------------------------------------+
|                             LỚP THIẾT BỊ PHẦN CỨNG                             |
|  - ESP32 DevKit V1 (Vi điều khiển trung tâm)                                    |
|  - Cảm biến DHT22 (Nhiệt độ & Độ ẩm - GPIO 15)                                  |
|  - Module Relay / Quạt thông gió (GPIO 12)                                     |
|  - Đầu đọc RFID RC522 Cửa (SPI GPIO 5) & Servo Khóa cửa (GPIO 13)              |
|  - Đầu đọc RFID RC522 Locker (SPI GPIO 21) & Màn hình LCD I2C                   |
+--------------------------------------------------------------------------------+
                                       | |
                               MQTT Protocol (JSON)
                               Broker: test.mosquitto.org (Port 1883)
                                       | |
                                       v v
+--------------------------------------------------------------------------------+
|                             LỚP BACKEND DỊCH VỤ                                |
|  - Ngôn ngữ: Python 3.11+ / Framework: FastAPI (Async IO)                      |
|  - Cầu nối MQTT: paho-mqtt kết nối bất đồng bộ với Event Loop                  |
|  - Cơ sở dữ liệu: Google Firebase Realtime Database (Admin SDK)                |
|  - Xác thực & Bảo mật: JWT Token 2 tầng (Admin Role & Member Role)             |
|  - Gửi cảnh báo: Telegram Bot API (httpx Async Client)                         |
|  - Đẩy dữ liệu Real-time: WebSockets Manager phân kênh (Public & Admin)        |
+--------------------------------------------------------------------------------+
                                       | |
                                REST API & WebSockets
                                       | |
                                       v v
+--------------------------------------------------------------------------------+
|                             LỚP GIAO DIỆN NGƯỜI DÙNG                           |
|  1. Public Dashboard: Màn hình theo dõi công cộng, hiển thị sĩ số & locker     |
|  2. User Member Portal: Đăng nhập hội viên, tra cứu thông tin cá nhân          |
|  3. Admin Dashboard: Quản lý hội viên, tủ đồ, log ra vào, chỉnh ngưỡng quạt   |
+--------------------------------------------------------------------------------+
```

---

## 4. Cấu trúc Thư mục Dự án

```
Project2/
├── backend/                        # Backend Python FastAPI
│   ├── app/
│   │   ├── api/                    # REST API routes & Auth
│   │   │   ├── auth.py             # JWT Token & Password Hash
│   │   │   ├── routes_admin.py     # Admin management APIs
│   │   │   ├── routes_public.py    # Public info APIs
│   │   │   ├── routes_user.py      # Member personal APIs
│   │   │   └── websocket.py        # Real-time WebSocket manager
│   │   ├── models/                 # Pydantic data schemas
│   │   ├── mqtt/                   # MQTT Client, Handlers & Topics
│   │   ├── repositories/           # Abstract Base & Firebase RTDB Repo
│   │   ├── services/               # Core business logic services
│   │   │   ├── access_service.py   # Check-in/out & Member validation
│   │   │   ├── environment_service.py # DHT22, Dynamic Thresholds & Fan logic
│   │   │   ├── locker_service.py   # Smart locker allocation
│   │   │   ├── notification_service.py # Telegram bot alerts
│   │   │   └── occupancy_service.py # Gym head-count counter
│   │   ├── config.py               # App configuration (.env)
│   │   └── main.py                 # FastAPI application factory & Lifespan
│   ├── tests/                      # Pytest automated test suite
│   │   ├── test_access_service.py
│   │   ├── test_environment_service.py
│   │   ├── test_locker_service.py
│   │   ├── test_occupancy_service.py
│   │   └── test_threshold_api.py
│   └── requirements.txt            # Python dependencies
├── esp32/                          # Firmware ESP32 & Wokwi Simulation
│   ├── src/
│   │   └── main.cpp                # Arduino C++ source code
│   ├── diagram.json                # Wokwi simulation schematic
│   ├── platformio.ini              # PlatformIO config
│   └── wokwi.toml                  # Wokwi run settings
├── frontend/                       # Web Client Application
│   ├── admin/                      # Admin Management Portal (index.html, app.js, style.css)
│   ├── public/                     # Public Monitor Screen (index.html, app.js, style.css)
│   ├── user/                       # Member User Portal (index.html, app.js, style.css)
│   └── shared/                     # Shared CSS tokens & API Client library
└── docs/                           # Tài liệu thiết kế & kỹ thuật chi tiết
    ├── api_documentation.md        # Đặc tả REST API & WebSockets
    ├── deployment_and_setup.md     # Hướng dẫn cài đặt & vận hành hệ thống
    ├── hardware_firmware_guide.md  # Sơ đồ chân & mã nguồn phần cứng ESP32
    ├── mqtt_protocol.md            # Chuẩn giao tiếp MQTT
    ├── project_context.md          # Tổng quan dự án (Tài liệu này)
    └── system_architecture.md      # Kiến trúc kỹ thuật chi tiết
```

---

## 5. Trạng thái Hiện tại & Tiến độ Hoàn thành

- [x] **Proposal & Báo cáo đề cương**: Hoàn thành tài liệu phân tích yêu cầu và kế hoạch.
- [x] **Phần cứng & Firmware ESP32**: Viết code Arduino C++, cấu hình PlatformIO, sơ đồ mạch Wokwi simulation kết nối Wi-Fi và MQTT broker.
- [x] **Giao thức MQTT**: Thiết lập đầy đủ các topic kiểm soát cửa, tủ đồ, dữ liệu cảm biến và lệnh điều khiển quạt.
- [x] **Backend FastAPI**: Hoàn thành toàn bộ kiến trúc đa tầng (Models, Repositories, Services, MQTT Async Bridge, REST APIs, WebSockets).
- [x] **Cơ sở dữ liệu Firebase Realtime Database**: Lưu trữ dữ liệu thành viên, tủ đồ, nhật ký vào ra, chỉ số môi trường và cấu hình ngưỡng.
- [x] **Cảnh báo Telegram**: Tự động bắn thông báo khi nhiệt độ/độ ẩm vượt ngưỡng cho phép.
- [x] **Cấu hình Ngưỡng Môi trường Động (Dynamic Thresholds)**: Cho phép Admin điều chỉnh ngưỡng kích hoạt quạt trực tiếp trên Web UI và lưu bền vững vào DB.
- [x] **Bộ 3 Web Portal**:
  - Giao diện Public Screen hiện đại.
  - Giao diện Member User Portal cho phép tra cứu & đổi mật khẩu.
  - Giao diện Admin Dashboard đầy đủ công cụ quản lý và điều khiển quạt thủ công.
- [x] **Unit Testing**: Bộ test tự động kiểm thử toàn bộ logic nghiệp vụ đạt 100% pass.