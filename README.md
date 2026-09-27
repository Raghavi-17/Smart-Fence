# 🛡️ Smart Fence

### AI & IoT-Based Intelligent Perimeter Safety Monitoring System

Smart Fence is an **AI and IoT-based safety monitoring system** that uses computer vision to detect, track, and analyze humans and animals approaching a monitored fence.

Instead of generating alerts for every movement, the system evaluates **object type, location, movement direction, and dwell time** to determine the level of risk. When a high-risk situation is detected, it provides real-time alerts through a web dashboard and activates an **ESP32-based buzzer and LED warning system**.

> **Note:** This project is a prototype early-warning system. The IoT hardware is designed to remain electrically isolated from any high-voltage fence.

---

## 🎯 Problem Statement

Traditional perimeter monitoring systems often rely on basic motion detection mechanisms.

These systems may generate unnecessary alerts due to:

* Stray animals
* Moving vegetation
* Environmental disturbances
* Rain and other background motion

They also cannot reliably determine whether a detected object is actually **approaching the fence or moving away from it**.

Smart Fence addresses this by combining **AI-based object detection, object tracking, spatial zones, movement analysis, and risk assessment**.

---

## 💡 How Smart Fence Works

```text
Camera Feed
     ↓
YOLOv8 Object Detection
     ↓
ByteTrack Object Tracking
     ↓
Ground-Contact Point Detection
     ↓
Movement Direction Analysis
     ↓
Virtual Zone Evaluation
     ↓
Risk Assessment
     ↓
Alert Debouncing
     ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
SQLite       React Dashboard    ESP32
Database     Real-Time Alerts   Buzzer + LED
```

---

## ✨ Key Features

### 🤖 AI-Based Detection

* YOLOv8-based object detection
* Identifies humans and relevant animal classes
* Configurable confidence threshold

### 🎯 Object Tracking

* ByteTrack maintains persistent tracking IDs
* Tracks multiple objects simultaneously
* Maintains movement history for each object

### 📍 Virtual Perimeter Zones

The camera view is divided into:

* 🟢 Safe Zone
* 🟡 Warning Zone
* 🔴 Danger Zone

The object's ground-contact point is used for zone evaluation.

### 🧭 Movement Analysis

The system classifies object movement as:

```text
TOWARDS_FENCE
AWAY_FROM_FENCE
STATIONARY
```

This helps distinguish an object approaching the boundary from one simply passing through the monitored area.

### ⚠️ Dynamic Risk Assessment

Risk is evaluated using:

```text
Object Class
+
Zone
+
Direction
+
Dwell Time
```

Possible risk levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

### 🔔 Intelligent Alerting

* Alert cooldown/debouncing
* Prevents repeated alerts for the same incident
* Allows alerts when the threat level escalates

### 📡 IoT Warning System

ESP32 communicates with the backend over Wi-Fi and controls:

* Piezo buzzer
* High-intensity LEDs

### 📊 Monitoring Dashboard

The React dashboard provides:

* Live annotated camera feed
* Active alerts
* Detection information
* Risk statistics
* System health
* Alert acknowledgment

### 🧪 Camera Fallback

A synthetic camera feed is available when a physical camera is not connected, making the system easier to test and demonstrate.

---

## 🏗️ System Architecture

```text
                         ┌─────────────────┐
                         │  Camera / Feed  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     YOLOv8      │
                         │ Object Detection│
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    ByteTrack    │
                         │ Object Tracking │
                         └────────┬────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │ Movement & Zone Engine │
                     └────────────┬───────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │    Risk Assessment     │
                     └────────────┬───────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
          ┌────────────┐   ┌─────────────┐   ┌──────────┐
          │   SQLite   │   │   React     │   │  ESP32   │
          │  Database  │   │  Dashboard  │   │ Buzzer + │
          │            │   │             │   │   LED    │
          └────────────┘   └─────────────┘   └──────────┘
```

---

## 🧰 Technology Stack

| Category                | Technology  |
| ----------------------- | ----------- |
| AI / Object Detection   | YOLOv8      |
| Object Tracking         | ByteTrack   |
| Computer Vision         | OpenCV      |
| Backend                 | FastAPI     |
| API Validation          | Pydantic    |
| Database                | SQLite      |
| ORM                     | SQLAlchemy  |
| Frontend                | React       |
| Frontend Tooling        | Vite        |
| Real-Time Communication | WebSocket   |
| Video Streaming         | MJPEG       |
| IoT Controller          | ESP32       |
| Hardware Communication  | HTTP / REST |
| Testing                 | Pytest      |

---

## 📂 Project Structure

```text
Smart-Fence/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── ...
│
├── ai/
│   ├── detection/
│   ├── tracking/
│   ├── movement/
│   └── risk/
│
├── esp32/
│   └── ...
│
├── tests/
│   └── test_smart_fence.py
│
├── README.md
└── project_explanation.md
```

> The exact folder names may vary depending on the current implementation.

---

## 🔄 Example Detection Flow

Suppose a person approaches the monitored fence.

```text
Person enters camera view
        ↓
YOLOv8 detects the person
        ↓
ByteTrack assigns Tracking ID
        ↓
Ground-contact point is calculated
        ↓
Object enters Warning Zone
        ↓
Movement history is analyzed
        ↓
Direction = TOWARDS_FENCE
        ↓
Risk Engine evaluates the situation
        ↓
Risk level increases
        ↓
Alert is generated
        ↓
Alert stored in SQLite
        ↓
React dashboard receives the alert
        ↓
ESP32 activates buzzer + LED
```

---

## 🌐 Application Access

### Local Development

The project can be run locally with separate frontend and backend services.

Typical development endpoints:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

FastAPI also provides interactive API documentation through its development server.

> These are local development addresses and are not public links.

---

## ▶️ Running the Project

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Smart-Fence
```

### 2. Start the Backend

```bash
cd backend
```

Create and activate a Python virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server using the project's configured entry point.

---

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the frontend development URL shown by Vite.

---

### 4. ESP32 Setup

The ESP32 should be connected to the same network as the backend.

Configure:

* Wi-Fi credentials
* Backend API address
* Buzzer connection
* LED connection

The ESP32 receives alert commands from the backend through HTTP.

---

## 📡 ESP32 Alert API

Example request:

```http
POST /api/alert
```

Example payload:

```json
{
  "risk": "HIGH",
  "buzzer": true,
  "led": true,
  "reason": "Human approaching danger zone"
}
```

The ESP32 interprets the command and activates the appropriate warning pattern.

---

## 🗄️ Database

Smart Fence uses **SQLite with SQLAlchemy ORM**.

The system stores information such as:

* Detection records
* Tracking IDs
* Zone information
* Risk levels
* Alerts
* Alert acknowledgment
* System logs

This allows the dashboard to display current and historical monitoring information.

---

## 🔌 Communication

### Frontend ↔ Backend

```text
React
  │
  ├── REST API → FastAPI
  │
  └── WebSocket → Real-Time Events
```

### Backend ↔ ESP32

```text
FastAPI
   │
   │ HTTP / REST
   ▼
 ESP32
   │
   ├── Buzzer
   └── LED
```

### Backend ↔ Camera

```text
Camera
   ↓
AI Processing
   ↓
Annotated Frames
   ↓
MJPEG Stream
   ↓
React Dashboard
```

---

## 🧪 Testing

The project includes automated tests using **Pytest**.

Testing covers important components including:

* Zone detection
* Movement direction
* Human/animal risk handling
* Stationary-object filtering
* Tracking isolation
* Alert cooldown
* Camera failure handling
* ESP32 communication failure

---

## ⚠️ Limitations

The current prototype has some practical limitations:

* A monocular camera provides 2D image coordinates rather than direct physical distance.
* Very low-light conditions can affect visible-camera detection.
* Fog, heavy rain, dust, or lens obstruction can reduce detection accuracy.
* AI performance depends on the model, camera quality, environment, and target appearance.

---

## 🚀 Future Enhancements

Possible future improvements include:

* Camera calibration and real-world distance estimation
* Stereo vision or LiDAR
* Thermal imaging for nighttime monitoring
* Edge AI deployment
* PTZ camera integration
* Multi-camera perimeter monitoring
* Cloud-based remote monitoring
* Advanced analytics and historical incident analysis

---

## 📖 Documentation

For a detailed explanation of the internal working and technical decisions:

**[Project Technical Explanation](project_explanation.md)**

The technical explanation covers:

* System architecture
* YOLOv8 detection
* ByteTrack tracking
* Movement analysis
* Virtual zones
* Risk assessment
* Alert debouncing
* FastAPI backend
* SQLite database
* ESP32 communication
* React dashboard
* Testing
* Limitations and future enhancements

---

## 🛡️ Safety Note

Smart Fence is an **early-warning prototype**.

The prototype should remain electrically isolated from high-voltage fence systems. The ESP32 controls only the non-lethal warning components such as the buzzer and LED.

**Do not connect the prototype electronics directly to a live high-voltage electric fence.**

---

## 👥 Project

**Smart Fence — AI & IoT-Based Intelligent Perimeter Safety Monitoring System**

Built as an academic engineering project combining:

**Artificial Intelligence + Computer Vision + Backend Development + Web Technologies + IoT**
