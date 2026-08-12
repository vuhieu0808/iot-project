# GymTag Backend System

Python backend service for **GymTag** - RFID Gym Access & Environment Control System. Replaces Node-RED to handle MQTT messaging with ESP32, business logic processing, database persistence (Firebase Realtime Database / SQLite fallback), Telegram alert notifications, and real-time Web Dashboard data streaming via WebSockets.

---

## 📁 Project Architecture

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, lifecycle setup & MQTT connection
│   ├── config.py                # Environment configuration settings
│   ├── mqtt/
│   │   ├── client.py            # Paho-MQTT connection client wrapper
│   │   ├── topics.py           # MQTT topic string constants
│   │   └── handlers.py         # MQTT message payload router & dispatcher
│   ├── models/
│   │   ├── member.py           # Member model & schemas
│   │   ├── locker.py           # Locker status model
│   │   ├── environment.py      # Temperature/humidity reading model
│   │   └── check_log.py        # Door check-in/check-out event log model
│   ├── services/
│   │   ├── access_service.py       # Check-in/check-out & membership expiry logic
│   │   ├── locker_service.py        # Locker assignment & release logic
│   │   ├── environment_service.py   # Threshold checking & fan control logic
│   │   ├── occupancy_service.py     # Real-time gym occupancy counter
│   │   └── notification_service.py  # Telegram Bot API notification client
│   ├── repositories/
│   │   ├── base.py                  # Abstract base repository interface
│   │   ├── firebase_repo.py         # Firebase Realtime Database repository
│   │   └── sqlite_repo.py           # SQLite asynchronous repository (fallback)
│   ├── api/
│   │   ├── routes_members.py        # REST API endpoints for members
│   │   ├── routes_lockers.py        # REST API endpoints for locker state
│   │   ├── routes_environment.py    # REST API endpoints for telemetry
│   │   ├── routes_logs.py           # REST API endpoints for access history & occupancy
│   │   └── websocket.py             # Real-time WebSocket endpoint
│   └── static/
│       └── dashboard.html           # Simple real-time web dashboard
├── tests/
│   ├── test_access_service.py       # Access verification unit tests
│   ├── test_locker_service.py       # Locker management unit tests
│   └── test_environment_service.py  # Environment monitoring unit tests
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🛠️ Requirements & Prerequisites

- **Python**: 3.11+
- **MQTT Broker**: `test.mosquitto.org` (public testing broker) or local Mosquitto broker
- **Dependencies**: `fastapi`, `uvicorn`, `paho-mqtt`, `httpx`, `pydantic-settings`, `firebase-admin`, `aiosqlite`

---

## 🚀 Quick Start Guide

### 1. Installation

Clone or navigate to the `backend` directory and set up a virtual environment:

```bash
cd backend
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configuration (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` values as needed:

```ini
# MQTT Broker Settings
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883

# Thresholds
TEMP_THRESHOLD=32.0
HUMIDITY_THRESHOLD=80.0

# Telegram Bot (Optional, for alerts)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Database Selection
# Options: 'firebase' or 'sqlite'
DB_TYPE=sqlite
SQLITE_DB_PATH=gymtag.db

# Firebase configuration (Required if DB_TYPE=firebase)
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/

# Locker System
LOCKER_COUNT=5
```

> **Note on Database**: If `DB_TYPE=firebase` is set but the `serviceAccountKey.json` credentials file is missing, the backend will automatically fallback to local `sqlite` (`gymtag.db`).

### 3. Run the Backend Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application:
- **Dashboard UI**: [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Unit Tests

Run pytest to execute automated unit tests for all core services:

```bash
pytest tests/ -v
```

---

## 📡 MQTT Interface Specification (ESP32 Integration)

### 1. Door Access (Check-in / Check-out)

- **Request Topic (ESP32 -> Backend)**: `gymtag/door/checkin_request`
  ```json
  {
    "card_id": "A1B2C3D4"
  }
  ```

- **Response Topic (Backend -> ESP32)**: `gymtag/door/checkin_response`
  ```json
  {
    "card_id": "A1B2C3D4",
    "status": "granted",       // "granted" or "denied"
    "action": "checkin",       // "checkin" or "checkout"
    "member_name": "Nguyen Van A",
    "reason": "Check-in granted",
    "duration_minutes": null   // Total workout minutes if action == "checkout"
  }
  ```

### 2. Locker Assignment & Release

- **Request Topic (ESP32 -> Backend)**: `gymtag/locker/request`
  ```json
  {
    "card_id": "A1B2C3D4"
  }
  ```

- **Response Topic (Backend -> ESP32)**: `gymtag/locker/response`
  ```json
  {
    "card_id": "A1B2C3D4",
    "action": "assign",         // "assign", "release", or "denied"
    "locker_number": 1,        // Locker slot number assigned or released
    "reason": "Locker #1 assigned successfully"
  }
  ```

### 3. Environmental Telemetry & Fan Control

- **Reading Topic (ESP32 -> Backend)**: `gymtag/environment/reading`
  ```json
  {
    "temperature": 34.5,
    "humidity": 82.0
  }
  ```

- **Fan Control Topic (Backend -> ESP32)**: `gymtag/environment/fan_control`
  *(Published only when fan state needs to change)*
  ```json
  {
    "fan": "on",               // "on" or "off"
    "reason": "Threshold exceeded! Temp: 34.5C (limit 32.0C), Humidity: 82.0% (limit 80.0%)"
  }
  ```

---

## 💡 Testing with MQTT Command Line (`mosquitto_pub` / `mosquitto_sub`)

You can test MQTT interaction without hardware using Mosquitto CLI tools:

### Subscribe to Backend Responses:
```bash
mosquitto_sub -h test.mosquitto.org -t "gymtag/#" -v
```

### Simulate Door Card Scan:
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/door/checkin_request" -m '{"card_id":"TEST001"}'
```

### Simulate Locker Card Scan:
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/locker/request" -m '{"card_id":"TEST001"}'
```

### Simulate Sensor Reading (Trigger Fan & Alert):
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/environment/reading" -m '{"temperature":35.0,"humidity":85.0}'
```
