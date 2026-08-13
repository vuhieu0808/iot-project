# 🏋️‍♂️ GymTag - Hệ Thống Quản Lý Phòng Gym Thông Minh (RFID & IoT)

Dự án môn học **Vật lý cho Công nghệ Thông tin** — Trường Đại học Khoa học Tự nhiên, ĐHQG TP.HCM.

---

## 📌 Hướng Dẫn Sử Dụng Web App GymTag

Ứng dụng Web App của GymTag được chia thành **3 phân hệ giao diện chính**, đáp ứng từng đối tượng người dùng từ khách truy cập, thành viên phòng tập cho đến Quản trị viên hệ thống.

---

### 🌐 1. Trang Giám Sát Công Khai (Public Dashboard)
* **Đường dẫn truy cập:** `http://localhost:8000/` hoặc `http://localhost:8000/public/`
* **Quyền truy cập:** Công khai (Không cần đăng nhập).
* **Mục đích:** Hiển thị màn hình theo dõi tổng quan tại sảnh/phòng chờ cho hội viên và khách hàng.

#### Chức năng chính:
- **⏱️ Số người đang tập (Gym Occupancy Counter):** Tự động đếm và cập nhật thời gian thực số lượng thành viên đang ở trong phòng tập (Dựa trên chênh lệch lượt check-in và check-out ở cửa ra vào).
- **🌡️ Giám sát Cảm biến Môi trường (DHT22):**
  - Hiển thị **Nhiệt độ (°C)** và **Độ ẩm (%)** môi trường phòng tập theo thời gian thực.
  - Hiển thị trạng thái quạt làm mát tự động (**Bật/Tắt**). Quạt tự động bật khi nhiệt độ > 32°C hoặc độ ẩm > 80%.
- **🔐 Sơ đồ Trạng thái Tủ Locker:** Hiển thị trực quan danh sách các tủ Locker (Trống / Đang sử dụng) giúp hội viên dễ dàng nhận biết các tủ còn trống.
- **📋 Nhật ký Ra/Vào Công khai:** Nhật ký ghi nhận lượt quẹt thẻ tại cửa ra vào (Chỉ hiển thị thời gian, hành động Check-in/Check-out, kết quả Scan — **ẩn toàn bộ thông tin cá nhân nhạy cảm**).
- **🔄 Kết nối WebSocket Realtime:** Mọi thay đổi về nhiệt độ, trạng thái tủ locker hay lượt ra vào sẽ tự động cập nhật ngay lập tức trên màn hình mà **không cần ấn F5/tải lại trang**.

---

### 👤 2. Portal Thành Viên (Member User Dashboard)
* **Đường dẫn truy cập:** `http://localhost:8000/user/`
* **Quyền truy cập:** Đăng nhập bằng tài khoản Hội viên.

#### 🔑 Thông tin Đăng nhập mặc định:
- **Mã Thẻ RFID (Card ID):** Nhập mã thẻ của bạn (Ví dụ: `CARD001`, `CARD002`,...)
- **Mật khẩu ban đầu:** `123456` *(Khuyên dùng đổi mật khẩu ngay sau lần đăng nhập đầu tiên)*.

#### Chức năng chính:
- **👤 Thẻ Thông Tin Cá Nhân:** Hiển thị Họ và Tên, Mã thẻ RFID, Ngày hết hạn gói tập và Trạng thái thẻ (Còn hạn / Hết hạn).
- **🔐 Thông Tin Locker Đang Giữ:** Hiển thị vị trí tủ Locker hiện tại đang gán cho thẻ của bạn và thời gian bắt đầu mượn tủ.
- **⏱️ Thống Kê Thời Gian Tập Luyện:** Tổng số phút tập luyện tích lũy và tổng số buổi tập đã thực hiện.
- **📋 Nhật Ký Ra Vào Cá Nhân:** Danh sách chi tiết lịch sử quẹt thẻ check-in/check-out của riêng bạn, đi kèm thời lượng tập luyện của từng buổi.
- **🔑 Đổi Mật Khẩu Cá Nhân:** Cho phép thành viên tự cập nhật mật khẩu mới để bảo vệ tài khoản.

---

### 🔒 3. Trang Quản Trị Viện (Admin Panel)
* **Đường dẫn truy cập:** `http://localhost:8000/admin/`
* **Quyền truy cập:** Đăng nhập bằng Mã Khóa Quản Trị (Admin Passkey).

#### 🔑 Thông tin Đăng nhập Admin mặc định:
- **Tên đăng nhập / Passkey Admin:** `admin123` (hoặc Tài khoản: `admin` / Mật khẩu: `admin123`).

#### Chức năng chính:
- **👥 Quản Lý Thành Viên (CRUD Member):**
  - **Xem danh sách & Tìm kiếm:** Tìm kiếm thành viên theo Họ tên, Mã thẻ RFID, Email hoặc Số điện thoại.
  - **Thêm Thành Viên Mới:** Cấp mã thẻ RFID (Card ID), điền Họ tên, Email, SĐT, Ngày hết hạn gói tập và Mật khẩu khởi tạo.
  - **Chỉnh sửa thông tin:** Cập nhật thông tin cá nhân, gia hạn ngày hết hạn gói tập.
  - **Reset Mật khẩu:** Khôi phục mật khẩu mặc định (`123456`) cho thành viên nếu họ quên mật khẩu.
  - **Xóa Thành viên:** Thu hồi thẻ và xóa dữ liệu khỏi hệ thống.
- **🔐 Quản Lý & Giám Sát Locker:**
  - Xem danh sách toàn bộ các tủ Locker, mã thẻ RFID đang giữ tủ, tên thành viên giữ tủ và thời điểm gán.
  - **Mở/Giải phóng Locker thủ công:** Quản trị viên có thể chủ động giải phóng tủ locker bị kẹt hoặc khi khách quên trả tủ.
- **📊 Báo Cáo Lịch Sử Ra Vào (Door Access Logs):** Xem và tra cứu lịch sử check-in / check-out toàn phòng gym, lọc theo Card ID, tên thành viên hoặc kết quả truy cập.
- **🌡️ Nhật Ký Cảm Biến Môi Trường:** Xem lịch sử ghi nhận biến động nhiệt độ, độ ẩm và nhật ký kích hoạt Relay quạt tự động.

---

## 🔑 Tổng Hợp Tài Khoản & Đường Dẫn Mặc Định

| Phân Hệ | Đường Dẫn (URL) | Tài Khoản / Passkey Mặc Định | Mô Tả |
| :--- | :--- | :--- | :--- |
| **Public Dashboard** | `http://localhost:8000/public/` | *(Không yêu cầu)* | Màn hình sảnh công khai, giám sát realtime |
| **Member Portal** | `http://localhost:8000/user/` | Mã thẻ: `CARD001` / Mật khẩu: `123456` | Portal dành cho hội viên xem thông tin & đổi mật khẩu |
| **Admin Panel** | `http://localhost:8000/admin/` | Mã Quản Trị: `admin123` *(hoặc admin/admin123)* | Trang quản trị hệ thống phòng gym |
| **REST API Docs** | `http://localhost:8000/docs` | *(Không yêu cầu)* | Tài liệu Swagger UI REST API đầy đủ |

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy Hệ Thống

### 1. Yêu Cầu Tiền Đề
- **Python:** phiên bản 3.11 trở lên.
- **Trình duyệt Web:** Google Chrome, Microsoft Edge, Mozilla Firefox hoặc Safari.

### 2. Khởi Chạy Backend (FastAPI Server)

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Tạo và kích hoạt môi trường ảo Python (Virtual Environment)
python -m venv .venv

# Trên Windows (PowerShell):
.\.venv\Scripts\activate

# Trên Linux / macOS:
source .venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 4. Chạy server FastAPI
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> 💡 **Lưu ý về Cơ Sở Dữ Liệu:** Hệ thống sử dụng **Firebase Realtime Database** để lưu trữ và đồng bộ dữ liệu thời gian thực. Bạn cần cấu hình file `firebase-admin-sdk.json` và khai báo `FIREBASE_DATABASE_URL` trong file `.env`.

### 3. Khởi Chạy Frontend (Giao Diện Web)

Backend FastAPI đã tích hợp sẵn Static Files Serving, do đó khi Backend khởi chạy thành công:
- Truy cập thẳng `http://localhost:8000/` trên trình duyệt để sử dụng Web App.

Ngoài ra, bạn cũng có thể mở trực tiếp bằng **VS Code Live Server**:
- Chuột phải vào `frontend/public/index.html` chọn **Open with Live Server**.
- Chuột phải vào `frontend/user/index.html` chọn **Open with Live Server**.
- Chuột phải vào `frontend/admin/index.html` chọn **Open with Live Server**.

---

## 🧪 Mô Phỏng & Test Nhanh Kịch Bản IoT (Không Cần Phần Cứng)

Bạn có thể giả lập thiết bị ESP32 quẹt thẻ RFID hoặc gửi dữ liệu cảm biến DHT22 lên hệ thống thông qua công cụ MQTT Command Line (`mosquitto_pub`):

### 1. Giả lập Quẹt Thẻ Ra / Vào Cửa (Check-in / Check-out):
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/door/checkin_request" -m "{\"card_id\":\"CARD001\"}"
```

### 2. Giả lập Quẹt Thẻ Mượn / Trả Locker:
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/locker/request" -m "{\"card_id\":\"CARD001\"}"
```

### 3. Giả lập Gửi Dữ Liệu Nhiệt Độ & Độ Ẩm (Kích hoạt quạt & cảnh báo):
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/environment/reading" -m "{\"temperature\":34.5, \"humidity\":82.0}"
```

---

## 📁 Cấu Trúc Thư Mục Dự Án

```
GymTag/
├── README.md                  # Hướng dẫn sử dụng tổng quan (File này)
├── docs/                      # Tài liệu chi tiết kiến trúc, MQTT & API
│   ├── project_context.md
│   ├── system_architecture.md
│   ├── api_documentation.md
│   └── mqtt_protocol.md
├── backend/                   # Mã nguồn Backend Python FastAPI
│   ├── app/
│   │   ├── main.py            # Entrypoint FastAPI server
│   │   ├── api/               # Các REST & WebSocket Routers
│   │   ├── services/          # Business logic (Access, Locker, Env, Occupancy)
│   │   ├── repositories/      # Lưu trữ dữ liệu (Firebase Realtime Database)
│   │   └── mqtt/              # Paho MQTT Client & Router
│   └── requirements.txt       # Danh sách thư viện Python
└── frontend/                  # Mã nguồn Frontend Web App
    ├── shared/                # System Design UI, API client & WebSockets
    ├── public/                # Public Dashboard UI
    ├── user/                  # Member User Portal UI
    └── admin/                 # Admin Panel UI
```

---

## 👨‍💻 Thông Tin Nhóm Thường Thực Hiện

* **Nhóm 6:**
  - Vũ Trần Minh Hiếu - 24127003
  - Hoàng Đức Thịnh - 24127240
  - Trần Viết Bảo - 24127270
* **Đồ án:** Vật lý cho Công nghệ Thông tin — Khoa CNTT, Trường Đại học Khoa học Tự nhiên, ĐHQG TP.HCM.
