# GymTag REST API & WebSocket Documentation (Tiered Access Control)

Base URL: `http://localhost:8000`  
Interactive OpenAPI Documentation: `http://localhost:8000/docs`

---

## 1. Public Endpoints (`/api/public/*`)

No authentication required.

### 1.1 Get Public System Status
- **URL**: `/api/public/status`
- **Method**: `GET`
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
- **Response**: `200 OK` (omits sensitive `card_id` and `assigned_at`)
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
    }
  ]
  ```

---

## 2. User Personal Endpoints (`/api/user/{card_id}/*`)

Self-service lookup using RFID card_id.

### 2.1 Get Member Profile
- **URL**: `/api/user/{card_id}/profile`
- **Method**: `GET`
- **Response**: `200 OK`

### 2.2 Get Member Access Logs History
- **URL**: `/api/user/{card_id}/history`
- **Method**: `GET`
- **Query Parameters**: `limit` (integer, default: 50)
- **Response**: `200 OK`

### 2.3 Get Member Assigned Locker
- **URL**: `/api/user/{card_id}/locker`
- **Method**: `GET`
- **Response**: `200 OK`

### 2.4 Get Member Workout Statistics
- **URL**: `/api/user/{card_id}/stats`
- **Method**: `GET`
- **Response**: `200 OK`

---

## 3. Admin Management Endpoints (`/api/admin/*`)

Requires JWT Bearer Header (`Authorization: Bearer <token>`).

### 3.1 Admin Login
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

### 3.2 List All Members
- **URL**: `/api/admin/members`
- **Method**: `GET`

### 3.3 Create or Update Member
- **URL**: `/api/admin/members`
- **Method**: `POST`

### 3.4 Delete Member
- **URL**: `/api/admin/members/{card_id}`
- **Method**: `DELETE`

### 3.5 List All Lockers (Full Info)
- **URL**: `/api/admin/lockers`
- **Method**: `GET`

### 3.6 Force Release Locker
- **URL**: `/api/admin/lockers/{locker_number}/force-release`
- **Method**: `POST`

### 3.7 Force Assign Locker
- **URL**: `/api/admin/lockers/{locker_number}/force-assign`
- **Method**: `POST`

### 3.8 Update Locker Status
- **URL**: `/api/admin/lockers/{locker_number}/status`
- **Method**: `PATCH`

### 3.9 Get Real-time Activity Logs (Full Logs)
- **URL**: `/api/admin/activity`
- **Method**: `GET`
- **Query Parameters**: `limit`, `card_id`

### 3.10 Get Environment Telemetry History
- **URL**: `/api/admin/environment/history`
- **Method**: `GET`

---

## 4. WebSocket Live Data Interfaces

### 4.1 Public WebSocket Stream
- **URL**: `ws://localhost:8000/ws/public` (or `ws://localhost:8000/ws`)
- **Authentication**: None
- **Received Events**:
  - `occupancy_update`: `{ "type": "occupancy_update", "data": { "current_occupancy": 5 } }`
  - `locker_status_update`: `{ "type": "locker_status_update", "data": { "lockers": [...] } }`
  - `environment_update`: `{ "type": "environment_update", "data": { "temperature": 30.5, "humidity": 68.0, "fan_on": false } }`

### 4.2 Admin Authenticated WebSocket Stream
- **URL**: `ws://localhost:8000/ws/admin?token=<JWT_TOKEN>`
- **Authentication**: Valid JWT Admin Token
- **Received Events**:
  - `checkin_event`: Full check-in details (member name, card_id, action, duration)
  - `locker_event`: Full locker allocation updates including assigned card_ids
  - `environment_update`: Environment sensor telemetry updates
