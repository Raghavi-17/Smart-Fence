# Smart Fence

### AI & IoT-Based Intelligent Safety Monitoring System

Smart Fence is an AI and IoT-based safety monitoring system designed to detect humans and animals approaching a restricted fence area. The system analyzes object movement, determines the associated risk level, and generates real-time alerts through an IoT device and web dashboard.

## Overview

Traditional fence monitoring mainly depends on manual observation or simple intrusion detection. Smart Fence adds an intelligent monitoring layer by combining **AI-based object detection, movement analysis, risk assessment, and IoT alerts**.

### How It Works

```text
Camera
   ↓
AI Object Detection
   ↓
Object Tracking
   ↓
Movement Analysis
   ↓
Zone Detection
   ↓
Risk Assessment
   ↓
Real-Time Alert
   ├── ESP32 + Buzzer + LED
   └── Web Dashboard
```

## Key Features

* Detects humans and animals using AI
* Tracks detected objects and analyzes their movement
* Uses virtual warning and danger zones
* Assigns risk levels based on object movement and zone
* Generates real-time alerts
* ESP32-based buzzer and LED alert system
* Web dashboard for live monitoring
* Stores detection and alert history
* Displays system statistics and analytics

## Tech Stack

| Component            | Technologies                   |
| -------------------- | ------------------------------ |
| AI & Computer Vision | Python, OpenCV, YOLO, NumPy    |
| Object Tracking      | ByteTrack / Tracking Algorithm |
| Backend              | FastAPI, SQLAlchemy            |
| Database             | SQLite                         |
| Frontend             | React, Vite, JavaScript, CSS   |
| IoT                  | ESP32, Wi-Fi                   |
| Communication        | REST API                       |

## Project Structure

```text
Smart-Fence/
├── ai/                  # Detection, tracking and risk analysis
├── backend/             # APIs, database and IoT communication
├── frontend/            # Web dashboard
├── esp32/               # ESP32 alert system
├── tests/               # Project tests
├── requirements.txt
├── .env.example
├── PROJECT_EXPLANATION.md
└── README.md
```

## Risk Assessment

The system evaluates the detected object's location and movement to determine the risk level.

* **LOW** – Object is in a safe area or moving away
* **MEDIUM** – Object enters the warning zone
* **HIGH** – Object enters the danger zone and approaches the fence
* **CRITICAL** – High-risk presence persists in the danger zone

## Dashboard

The web dashboard provides:

* Live monitoring
* Current risk status
* Recent alerts
* Detection statistics
* Analytics
* System diagnostics
* Zone configuration

## Getting Started

### Backend

```bash
pip install -r requirements.txt
```

Configure the required environment variables using `.env.example`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Start the backend and frontend according to the project configuration.

## Safety Note

The IoT component is designed as a **safe prototype using an ESP32, buzzer, and LED** for alert demonstration. It is not intended to directly control a high-voltage electric fence.

## Project Documentation

For detailed architecture, implementation details, modules, and project explanation, see:

`PROJECT_EXPLANATION.md`
