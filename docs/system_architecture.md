# GymTag System Architecture Documentation

## 1. Overview

GymTag is an IoT-based Gym Access & Facility Management system designed to replace legacy gateway solutions (e.g. Node-RED) with a clean, extensible, asynchronous Python backend.

The system manages RFID card authentication at main entry doors and locker areas, monitors ambient temperature and relative humidity via DHT22 sensors, controls automated fan relays, sends real-time Telegram alerts, and feeds live telemetry to a Web Dashboard via WebSockets.

---

## 2. System Architecture Diagram

```
+-----------------------------------------------------------------------+
|                            ESP32 FIRMWARE                             |
|  - RFID RC522 (Door Entrance Check-in/Check-out)                      |
|  - RFID RC522 (Locker Area Assignment/Release)                        |
|  - DHT22 (Temperature & Humidity Sensor)                              |
|  - Servo Motors (Door Lock & Locker Release)                          |
|  - Relay Module (Ventilation Fan Control)                             |
+-----------------------------------------------------------------------+
                                   | |
                           MQTT Protocol (JSON)
                                   | |
                                   v v
+-----------------------------------------------------------------------+
|                            MQTT BROKER                                |
|  - Mosquitto Local / test.mosquitto.org (Port 1883)                   |
+-----------------------------------------------------------------------+
                                   | |
                           paho-mqtt (Async Bridge)
                                   | |
                                   v v
+-----------------------------------------------------------------------+
|                         PYTHON BACKEND SERVICE                        |
|  FastAPI Framework (Python 3.11+)                                     |
|                                                                       |
|  [MQTT Handler] ----> [Services Layer] ----> [Repository Layer]       |
|                             |                      |                  |
|                 +-----------+----------+           |                  |
|                 |                      |           v                  |
|                 v                      v    +----------------------+  |
|         [Telegram Notifier]    [WebSocket]  | Firebase Realtime DB |  |
|         (httpx HTTP API)       (Manager)    +----------------------+  |
+-----------------------------------------------------------------------+
                                         |
                                  WebSocket / REST
                                         |
                                         v
+-----------------------------------------------------------------------+
|                            WEB DASHBOARD                              |
|  - Real-time occupancy counter                                        |
|  - Dynamic Locker status grid                                         |
|  - Ambient Temperature / Humidity telemetry                           |
|  - Live RFID Access Log Feed                                          |
+-----------------------------------------------------------------------+
```

---

## 3. Core Component Responsibilities

### 3.1 Hardware (ESP32)
- Scans RFID tags at the main entrance door and sends access requests.
- Scans RFID tags at the locker area and sends locker requests.
- Reads ambient temperature and humidity from DHT22 every 5–10 seconds.
- Actuates door lock servos based on access authorization responses.
- Toggles the cooling fan relay based on backend fan control commands.

### 3.2 MQTT Broker
- Serves as the lightweight message bus between ESP32 and Python backend.
- Decouples hardware execution from server processing logic.

### 3.3 Python Backend Application
- **MQTT Layer (`app/mqtt/`)**: Subscribes to incoming request topics, parses JSON payloads, bridges thread-safe execution into FastAPI's asyncio event loop, and publishes decision responses.
- **Service Layer (`app/services/`)**:
  - `AccessService`: Verifies membership validity, registration status, expiration dates, determines check-in vs check-out, and calculates session workout duration.
  - `LockerService`: Dynamically assigns the lowest available empty locker slot or releases an existing locker.
  - `EnvironmentService`: Evaluates temperature/humidity against thresholds (32.0 C / 80.0%), triggers automatic fan relay commands, and sends Telegram alerts.
  - `OccupancyService`: Calculates the current occupant count inside the facility.
  - `NotificationService`: Sends HTML-formatted alert messages to a Telegram Chat ID via Bot API using `httpx`.
- **Repository Layer (`app/repositories/`)**: Implements an abstract repository pattern (`BaseRepository`) with Firebase Realtime Database persistence (`FirebaseRepository`).
- **API & Realtime Layer (`app/api/`)**: Provides REST endpoints for CRUD operations and WebSockets (`/ws`) for live UI updates.

### 3.4 Web Dashboard
- Single-page interface providing live metrics, locker allocation grid, environmental readings, and real-time event logging.
