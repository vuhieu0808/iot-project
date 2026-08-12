# GymTag Deployment and Setup Guide

## 1. Environment Requirements

- Python 3.11 or higher
- Pip package manager
- Virtual environment (`venv`)

---

## 2. Environment Variables Configuration (`.env`)

File location: `backend/.env`

```ini
# Server Settings
HOST=0.0.0.0
PORT=8000

# MQTT Settings
MQTT_BROKER=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=gymtag_backend_service

# Thresholds
TEMP_THRESHOLD=32.0
HUMIDITY_THRESHOLD=80.0

# Telegram Alert Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Database Selection: 'firebase' or 'sqlite'
DB_TYPE=sqlite
SQLITE_DB_PATH=gymtag.db

# Firebase Realtime DB Settings (required if DB_TYPE=firebase)
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/

# Locker System
LOCKER_COUNT=10
```

---

## 3. Running the Server

Activate virtual environment and launch Uvicorn server:

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. Testing End-to-End Flow with Mosquitto CLI

### 4.1 Monitor All Topics
```bash
mosquitto_sub -h test.mosquitto.org -t "gymtag/#" -v
```

### 4.2 Simulate Door Scan Request
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/door/checkin_request" -m "{\"card_id\":\"CARD001\"}"
```

### 4.3 Simulate High Temperature Reading (Trigger Fan & Telegram Alert)
```bash
mosquitto_pub -h test.mosquitto.org -t "gymtag/environment/reading" -m "{\"temperature\":35.5,\"humidity\":85.0}"
```

---

## 5. Running Automated Unit Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```
