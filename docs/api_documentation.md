# GymTag REST API & WebSocket Documentation (3-Tier Access Architecture)

Base URL: `http://localhost:8000`  
Interactive OpenAPI / Swagger Documentation: `http://localhost:8000/docs`  
ReDoc Documentation: `http://localhost:8000/redoc`

---

## 1. Public Endpoints (`/api/public/*`)

Public endpoints require **no authentication** and are used for public monitor screens, lobby displays, and guest dashboards.

### 1.1 Get Public Gym Facility Status
- **URL**: `/api/public/status`
- **Method**: `GET`
- **Description**: Returns live head-count (current occupancy) and latest ambient environment metrics (DHT22).
- **Response**: `200 OK`
  ```json
  {
    "current_occupancy": 3,
    "temperature": 29.5,
    "humidity": 65.0,
    "fan_on": false
  }
  ```

### 1.2 Get Public Locker Status Grid
- **URL**: `/api/public/lockers`
- **Method**: `GET`
- **Description**: Returns the public availability status of all lockers. Sensitized data such as member `card_id` and `assigned_at` timestamps are strictly omitted for privacy.
- **Response**: `200 OK`
  ```json
  [
    {
      "locker_number": 1,
      "status": "occupied",
      "is_occupied": true
    },
    {
      "locker_number": 2,
      "status": "vacant",
      "is_occupied": false
    },
    {
      "locker_number": 3,
      "status": "broken",
      "is_occupied": false
    }
  ]
  ```

---

## 2. Member User Portal Endpoints (`/api/user/*`)

Dedicated endpoints for gym members to log in, view personal profiles, review check-in/out attendance history, view active locker assignments, calculate workout stats, and manage account passwords.

### 2.1 Member Login
- **URL**: `/api/user/login`
- **Method**: `POST`
- **Description**: Authenticate member using RFID `card_id` and personal password (default initial password: `123456`).
- **Request Body**:
  ```json
  {
    "card_id": "CARD001",
    "password": "your_password"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "token": "<jwt-token-string>",
    "card_id": "CARD001",
    "name": "Nguyễn Văn A"
  }
  ```

### 2.2 Change Password
- **URL**: `/api/user/change-password`
- **Method**: `POST`
- **Authentication**: Requires User JWT Bearer (`Authorization: Bearer <user_token>`)
- **Request Body**:
  ```json
  {
    "old_password": "123456",
    "new_password": "new_secure_password"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "message": "Đổi mật khẩu thành công!"
  }
  ```

### 2.3 Get Current Member Profile
- **URL**: `/api/user/me/profile`
- **Method**: `GET`
- **Authentication**: Requires User JWT Bearer (`Authorization: Bearer <user_token>`)
- **Response**: `200 OK`
  ```json
  {
    "card_id": "CARD001",
    "name": "Nguyễn Văn A",
    "membership_expiry": "2026-12-31",
    "is_active": true,
    "is_expired": false
  }
  ```

### 2.4 Get Personal Check-in / Check-out History
- **URL**: `/api/user/me/history`
- **Method**: `GET`
- **Authentication**: Requires User JWT Bearer (`Authorization: Bearer <user_token>`)
- **Query Parameters**: `limit` (int, default: 50, max: 200)
- **Response**: `200 OK`
  ```json
  [
    {
      "log_id": "log_1710000000_1234",
      "card_id": "CARD001",
      "member_name": "Nguyễn Văn A",
      "timestamp": "2026-08-14T09:30:00",
      "action": "checkout",
      "status": "granted",
      "duration_minutes": 75.5,
      "reason": "Check-out granted"
    }
  ]
  ```

### 2.5 Get Assigned Locker
- **URL**: `/api/user/me/locker`
- **Method**: `GET`
- **Authentication**: Requires User JWT Bearer (`Authorization: Bearer <user_token>`)
- **Response**: `200 OK` (returns `null` if no locker currently held)
  ```json
  {
    "locker_number": 4,
    "status": "occupied",
    "assigned_card_id": "CARD001",
    "assigned_at": "2026-08-14T08:15:00"
  }
  ```

### 2.6 Get Personal Workout Statistics
- **URL**: `/api/user/me/stats`
- **Method**: `GET`
- **Authentication**: Requires User JWT Bearer (`Authorization: Bearer <user_token>`)
- **Response**: `200 OK`
  ```json
  {
    "total_sessions": 24,
    "total_workout_minutes": 1820.5
  }
  ```

*(Note: Legacy lookup routes `/api/user/{card_id}/profile`, `/history`, `/locker`, and `/stats` are also supported for backward-compatible lookups).*

---

## 3. Admin Management Endpoints (`/api/admin/*`)

All administrative endpoints require Admin JWT authentication (`Authorization: Bearer <admin_token>`).

### 3.1 Admin Authentication
- **URL**: `/api/admin/login`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "token": "<jwt-token-string>",
    "username": "admin"
  }
  ```

### 3.2 Member Management
- **`GET /api/admin/members`**: List all registered gym members.
- **`POST /api/admin/members`**: Create or update a member record.
  ```json
  {
    "card_id": "CARD005",
    "name": "Trần Thị B",
    "membership_expiry": "2026-12-31",
    "is_active": true,
    "password": "initial_password_optional"
  }
  ```
- **`GET /api/admin/members/{card_id}`**: Get full details of a specific member.
- **`DELETE /api/admin/members/{card_id}`**: Delete a member from the database (`204 No Content`).
- **`POST /api/admin/members/{card_id}/toggle-active`**: Toggle or set active status (`?is_active=true|false`).
- **`POST /api/admin/members/{card_id}/reset-password`**: Reset member's password to default `123456`.

### 3.3 Locker Management
- **`GET /api/admin/lockers`**: List all lockers with complete details (status, assigned card ID, timestamp).
- **`POST /api/admin/lockers/{locker_number}/force-release`**: Forcibly unlock and clear locker assignment.
- **`POST /api/admin/lockers/{locker_number}/force-assign`**: Forcibly assign a specific card ID to a locker:
  ```json
  {
    "card_id": "CARD001"
  }
  ```
- **`PATCH /api/admin/lockers/{locker_number}/status`**: Update locker state (`vacant`, `occupied`, or `broken`):
  ```json
  {
    "status": "broken"
  }
  ```

### 3.4 Activity & Audit Logs
- **`GET /api/admin/activity`**: Retrieve full system RFID check-in/out logs.
  - **Query Params**: `limit` (default: 100, max: 500), `card_id` (optional filter).

### 3.5 Environment & Ventilation Management
- **`GET /api/admin/environment/history`**: Get DHT22 sensor history logs (`limit` query param).
- **`POST /api/admin/environment/fan`**: Turn the ventilation fan relay ON, OFF, or return to AUTO mode (Admin command has highest priority over sensor logic).
  - **Request Body**: `{"command": "on"}`, `{"command": "off"}`, or `{"command": "auto"}`
  - **Response**: `200 OK`
    ```json
    {
      "message": "Đã gửi lệnh ON quạt thông gió (Thủ công - Ưu tiên cao nhất) thành công!",
      "fan_on": true,
      "manual_mode": true,
      "reading": {
        "temperature": 32.5,
        "humidity": 65.0,
        "fan_on": true,
        "timestamp": "2026-08-16T23:00:00.123456"
      }
    }
    ```
- **`GET /api/admin/environment/thresholds`**: Get current automatic fan activation thresholds.
  - **Response**: `200 OK`
    ```json
    {
      "temp_threshold": 32.0,
      "humidity_threshold": 80.0
    }
    ```
- **`PUT /api/admin/environment/thresholds`**: Update automatic fan activation thresholds (persisted to Firebase).
  - **Request Body**:
    ```json
    {
      "temp_threshold": 30.5,
      "humidity_threshold": 75.0
    }
    ```
  - **Response**: `200 OK`

### 3.6 Telegram Bot Alert Testing
- **`POST /api/admin/telegram/test`**: Dispatches a test alert notification to the configured Telegram Chat ID to verify connectivity.
  - **Response**: `200 OK`
    ```json
    {
      "message": "Đã gửi thông báo thử nghiệm tới Telegram thành công!"
    }
    ```

---

## 4. Real-time WebSocket Channels

The backend provides two distinct WebSocket channels partitioned by privilege.

### 4.1 Public WebSocket Stream
- **URL**: `ws://localhost:8000/ws/public` (or `ws://localhost:8000/ws`)
- **Authentication**: None
- **Broadcast Events**:
  - `occupancy_update`:
    ```json
    { "type": "occupancy_update", "data": { "current_occupancy": 4 } }
    ```
  - `locker_status_update`:
    ```json
    { "type": "locker_status_update", "data": { "lockers": [ ... ] } }
    ```
  - `environment_update`:
    ```json
    {
      "type": "environment_update",
      "data": {
        "temperature": 30.2,
        "humidity": 68.5,
        "fan_on": false,
        "timestamp": "2026-08-16T23:00:00.123456",
        "manual_mode": false
      }
    }
    ```

### 4.2 Admin WebSocket Stream
- **URL**: `ws://localhost:8000/ws/admin?token=<ADMIN_JWT_TOKEN>`
- **Authentication**: Valid Admin JWT passed as query parameter
- **Broadcast Events**:
  - `checkin_event` / `checkout_event`: Real-time scan alerts with complete member info, duration, and status.
  - `locker_event`: Full locker allocation updates including assigned member cards.
  - `environment_update`: Live DHT22 telemetry, timestamp, and fan state (`manual_mode` flag included).
  - `threshold_update`: Live notification when environment thresholds are reconfigured by an admin.

