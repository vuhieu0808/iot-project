# GymTag Frontend

Hệ thống giao diện Web Dashboard cho Đồ án GymTag (RFID Gym Management System).

Frontend được tách biệt hoàn toàn khỏi backend Python FastAPI, bao gồm **2 giao diện riêng biệt**:

1. **User Dashboard** (`frontend/user/index.html`)
2. **Admin Panel** (`frontend/admin/index.html`)

---

## 📁 Cấu Trúc Thư Mục

```
frontend/
├── shared/
│   ├── css/
│   │   ├── variables.css      # Custom CSS design tokens (Colors, Typography, Shadows)
│   │   ├── base.css           # CSS Reset & Base styles
│   │   └── components.css     # Common UI components (Cards, Badges, Tables, Locker Grid)
│   └── js/
│       ├── api.js             # Client wrapper cho REST API (`http://localhost:8000`)
│       ├── websocket.js       # WebSocket Realtime Client với tự động kết nối lại
│       └── utils.js           # Hàm tiện ích (Format thời gian, escape HTML, Toast)
│
├── user/
│   ├── index.html             # User Dashboard (Trang giám sát realtime)
│   ├── style.css              # Style dành riêng cho User Dashboard
│   └── app.js                 # App Controller cho User Dashboard
│
├── admin/
│   ├── index.html             # Admin Panel (Trang quản trị hệ thống)
│   ├── style.css              # Style dành riêng cho Admin Panel
│   └── app.js                 # App Controller cho Admin Panel (CRUD, Tab routing)
│
└── README.md                  # Hướng dẫn sử dụng
```

---

## 🚀 Hướng Dẫn Chạy Frontend

### 1. Khởi chạy Backend FastAPI
Trước tiên, hãy chắc chắn Backend Python đang chạy tại `http://localhost:8000`:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Mở Frontend
Bạn có thể mở giao diện bằng 2 cách:

#### Cách 1: Sử dụng VS Code Live Server (Khuyên dùng)
- Mở VS Code tại thư mục project.
- Click chuột phải vào `frontend/user/index.html` chọn **Open with Live Server**.
- Click chuột phải vào `frontend/admin/index.html` chọn **Open with Live Server**.

#### Cách 2: Mở trực tiếp bằng Trình duyệt Web
- Truy cập thư mục `frontend/user/index.html` hoặc `frontend/admin/index.html` và double-click để mở file trong trình duyệt Chrome / Edge.
- Hệ thống hỗ trợ CORS tự động nhận diện kết nối về `http://localhost:8000`.

---

## 🌟 Chức Năng Chính

### 1. User Dashboard (`/user/` hoặc `http://localhost:8000/`)
- **Trang mặc định public**: Bất kỳ ai mở `http://localhost:8000` đều vào trang này đầu tiên.
- **Bảo mật & Ẩn thông tin nhạy cảm**:
  - Không chứa nút bấm chuyển trang Admin.
  - Không hiển thị Card ID, không hiển thị Họ tên hay Email/SĐT của thành viên.
  - Chỉ hiển thị chỉ số tổng quan: Số người đang tập, Nhiệt độ (°C), Độ ẩm (%), Trạng thái quạt, Số locker trống/đầy và Lịch sử quẹt thẻ công khai (Thời gian + Hành động + Kết quả).

### 2. Admin Panel (`/admin/` hoặc `http://localhost:8000/admin/`)
- **Yêu cầu Đăng nhập (Authentication)**:
  - Bắt buộc nhập **Mã Khóa Quản Trị (Passkey Admin)** mới được truy cập dữ liệu hệ thống.
  - **Passkey mặc định**: `admin123`
  - Lưu phiên đăng nhập tự động trong `sessionStorage`, hỗ trợ nút **🔒 Đăng Xuất Admin**.
- **Quản lý thông tin chi tiết**:
  - **Quản lý Thành viên (CRUD)**: Xem danh sách, Thêm, Chỉnh sửa, Gia hạn & Xoá thành viên (hiển thị đầy đủ Card ID, Họ tên, Email, SĐT).
  - **Chi tiết Locker**: Xem RFID Card ID đang giữ locker & thời gian gán.
  - **Lịch sử Ra vào**: Bộ lọc theo Card ID, tên thành viên & thời gian tập chi tiết.
  - **Lịch sử Môi trường**: Nhật ký chi tiết của cảm biến DHT22 & Relay quạt.
