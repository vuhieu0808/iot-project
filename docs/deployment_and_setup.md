# GymTag Deployment and Setup Guide

## 1. Prerequisites

- **Python**: 3.11 or higher
- **Package Manager**: `pip` & Python virtual environment (`venv`)
- **MQTT Broker**: Public test broker (`test.mosquitto.org:1883`) or local Mosquitto
- **Firebase Realtime Database**: Project created on Google Firebase with Realtime DB enabled and Service Account private key JSON file.
- **ESP32 Toolchain / Simulator**: Wokwi Simulator or PlatformIO / Arduino IDE for physical ESP32 DevKit V1.

---

## 2. Environment Variables Configuration (`.env`)

Create a `.env` file inside the `backend/` directory:

```ini
# Server Binding
HOST=0.0.0.0
PORT=8000

# MQTT Settings
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=gymtag_backend_service

# Automatic Fan Trigger Defaults (can be reconfigured dynamically via Admin Dashboard)
TEMP_THRESHOLD=32.0
HUMIDITY_THRESHOLD=80.0

# Telegram Bot Alert Configuration (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Firebase Realtime Database
FIREBASE_CREDENTIALS_PATH=firebase-admin-sdk.json
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/

# Locker System
LOCKER_COUNT=10

# Security & Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET=gymtag-secret-key-2026
```

> **Note**: Place your downloaded Firebase Admin SDK credentials file as `backend/firebase-admin-sdk.json`.

---

## 3. Backend Setup & Launch

### 3.1 Install Dependencies
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3.2 Start FastAPI Application Server
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Root: `http://localhost:8000`
- Swagger UI Documentation: `http://localhost:8000/docs`

---

## 4. Frontend Web Portals

The frontend consists of 3 dedicated web portals:

1. **Public Monitor Display** (`frontend/public/index.html`):
   - Accessible by gym patrons & TV screens. Displays real-time gym occupancy, locker status grid, and temperature/humidity gauges.
2. **User Member Portal** (`frontend/user/index.html`):
   - Personal member login (`Card ID` + `Password`). View membership expiry, workout stats, check-in history, assigned locker, and change password.
3. **Admin Management Dashboard** (`frontend/admin/index.html`):
   - Admin authentication (`admin` / `admin123`). Manage members, lockers, view real-time scan logs, manual fan relay toggle, and configure dynamic temperature/humidity thresholds.

### Accessing Frontend:
- Open `frontend/public/index.html`, `frontend/user/index.html`, or `frontend/admin/index.html` directly in a modern web browser or serve via VS Code **Live Server** on port 5500.
- The shared API client (`frontend/shared/js/api.js`) automatically points to `http://localhost:8000`.

---

## 5. Default Credentials

- **Admin Portal**:
  - Username: `admin`
  - Password: `admin123`
- **User Member Accounts**:
  - Card ID: `CARD001`, `CARD002`, `CARD003`, etc.
  - Default Initial Password: `123456`

---

## 6. End-to-End Simulation with Mosquitto CLI

### 6.1 Monitor All MQTT Traffic
```powershell
mosquitto_sub -h test.mosquitto.org -t "gymtag/#" -v
```

### 6.2 Simulate Door Entrance Scan (Check-in / Check-out)
```powershell
mosquitto_pub -h test.mosquitto.org -t "gymtag/door/checkin_request" -m "{\"card_id\":\"CARD001\"}"
```

### 6.3 Simulate Locker Request (Assign / Release)
```powershell
mosquitto_pub -h test.mosquitto.org -t "gymtag/locker/request" -m "{\"card_id\":\"CARD001\"}"
```

### 6.4 Simulate DHT22 Environmental Telemetry
```powershell
mosquitto_pub -h test.mosquitto.org -t "gymtag/environment/reading" -m "{\"temperature\":34.5,\"humidity\":82.0}"
```

---

## 7. Running Automated Test Suite

Run unit and integration tests using pytest:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
All tests should pass, including tests for AccessService, LockerService, EnvironmentService (with dynamic thresholds), OccupancyService, and Admin Threshold REST APIs.
