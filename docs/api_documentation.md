# GymTag REST API & WebSocket Documentation

Base URL: `http://localhost:8000`  
Interactive OpenAPI Documentation: `http://localhost:8000/docs`

---

## 1. Member Management Endpoints

### 1.1 List All Members
- **URL**: `/api/members`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  [
    {
      "card_id": "CARD001",
      "name": "Nguyen Van A",
      "email": "a@example.com",
      "phone": "0901234567",
      "membership_expiry": "2026-12-31",
      "is_active": true,
      "created_at": "2026-08-11T23:00:00"
    }
  ]
  ```

### 1.2 Create or Update Member
- **URL**: `/api/members`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "card_id": "CARD002",
    "name": "Tran Van B",
    "email": "b@example.com",
    "phone": "0987654321",
    "membership_expiry": "2026-10-15",
    "is_active": true
  }
  ```
- **Response**: `201 Created`

### 1.3 Get Member Details by Card ID
- **URL**: `/api/members/{card_id}`
- **Method**: `GET`
- **Response**: `200 OK` or `404 Not Found`

### 1.4 Delete Member
- **URL**: `/api/members/{card_id}`
- **Method**: `DELETE`
- **Response**: `204 No Content` or `404 Not Found`

---

## 2. Locker Status Endpoints

### 2.1 List All Lockers
- **URL**: `/api/lockers`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  [
    {
      "locker_number": 1,
      "is_occupied": true,
      "card_id": "CARD001",
      "assigned_at": "2026-08-11T23:10:00"
    },
    {
      "locker_number": 2,
      "is_occupied": false,
      "card_id": null,
      "assigned_at": null
    }
  ]
  ```

---

## 3. Environmental Telemetry Endpoints

### 3.1 Get Latest Environment Reading
- **URL**: `/api/environment/latest`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  {
    "temperature": 29.5,
    "humidity": 65.0,
    "fan_on": false,
    "timestamp": "2026-08-11T23:15:00"
  }
  ```

### 3.2 Get Environment History
- **URL**: `/api/environment/history?limit=50`
- **Method**: `GET`
- **Query Parameters**: `limit` (integer, default: 50, max: 500)
- **Response**: `200 OK`

---

## 4. Access Logs & Occupancy Endpoints

### 4.1 Get Access History Logs
- **URL**: `/api/logs`
- **Method**: `GET`
- **Query Parameters**:
  - `limit`: (integer, default: 50)
  - `card_id`: (optional string filter)
- **Response**: `200 OK`
  ```json
  [
    {
      "id": "log-uuid-1",
      "card_id": "CARD001",
      "member_name": "Nguyen Van A",
      "action": "checkout",
      "status": "granted",
      "reason": "Check-out successful",
      "duration_minutes": 45.2,
      "timestamp": "2026-08-11T23:55:00"
    }
  ]
  ```

### 4.2 Get Real-time Occupancy Count
- **URL**: `/api/occupancy`
- **Method**: `GET`
- **Response**: `200 OK`
  ```json
  {
    "current_occupancy": 3
  }
  ```

---

## 5. WebSocket Live Data Interface

- **URL**: `ws://localhost:8000/ws`
- **Protocol**: WebSocket

### Broadcast Event Types

#### 1. Door Access Event (`checkin_event`)
```json
{
  "type": "checkin_event",
  "data": {
    "card_id": "CARD001",
    "status": "granted",
    "action": "checkin",
    "member_name": "Nguyen Van A",
    "reason": "Check-in granted",
    "duration_minutes": null
  }
}
```

#### 2. Locker Allocation Event (`locker_event`)
```json
{
  "type": "locker_event",
  "data": {
    "event": {
      "card_id": "CARD001",
      "action": "assign",
      "locker_number": 1,
      "reason": "Locker #1 assigned successfully"
    },
    "lockers": [ ... updated locker list ... ]
  }
}
```

#### 3. Environmental Telemetry Update (`environment_update`)
```json
{
  "type": "environment_update",
  "data": {
    "temperature": 34.5,
    "humidity": 82.0,
    "fan_on": true,
    "timestamp": "2026-08-11T23:50:00"
  }
}
```
