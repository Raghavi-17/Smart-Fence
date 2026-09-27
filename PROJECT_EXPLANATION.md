# Smart Fence — Technical Project Explanation

## 1. Project Overview

**Smart Fence** is an AI and IoT-based intelligent safety monitoring system designed to detect and assess potential intrusions near a physical fence before physical contact occurs.

The system combines computer vision, object tracking, spatial analysis, risk assessment, backend services, database storage, a web dashboard, and IoT-based warning hardware.

The core idea is:

```text
Detect → Track → Analyze Movement → Identify Zone → Assess Risk → Alert
```

---

## 2. Problem Statement

Traditional perimeter monitoring systems commonly depend on basic motion sensors, PIR sensors, or break-beam mechanisms.

These systems can detect movement, but they have limited ability to understand:

* What caused the movement?
* Is it a human or an animal?
* Is the object approaching the fence or moving away?
* How close is it to the fence?
* Is the situation actually risky?

Environmental movement such as animals, vegetation, rain, or other disturbances can also result in unnecessary alerts.

The project aims to provide an intelligent monitoring layer that can analyze these factors before generating a high-priority warning.

---

## 3. Proposed Solution

Smart Fence uses a camera-based AI pipeline to understand the activity near the monitored boundary.

The system:

1. Captures a video feed.
2. Detects humans and animals using YOLOv8.
3. Tracks detected objects using ByteTrack.
4. Calculates the object's ground-contact position.
5. Determines movement direction.
6. Checks which virtual zone contains the object.
7. Calculates a risk level.
8. Generates and stores an alert when required.
9. Updates the monitoring dashboard.
10. Sends a warning command to the ESP32.

This creates an end-to-end monitoring pipeline instead of relying only on a single motion trigger.

---

# 4. System Architecture

```text
                         Camera Feed
                              │
                              ▼
                    ┌──────────────────┐
                    │      YOLOv8      │
                    │ Object Detection │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    ByteTrack     │
                    │ Object Tracking  │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ Ground Point & Movement│
                 │      Analysis          │
                 └────────────┬───────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │   Virtual Zone Engine  │
                 │ Safe / Warning / Danger│
                 └────────────┬───────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │     Risk Assessment    │
                 │ LOW / MEDIUM / HIGH /  │
                 │        CRITICAL         │
                 └────────────┬───────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
        ┌──────────┐   ┌─────────────┐   ┌──────────┐
        │  SQLite  │   │   React     │   │  ESP32   │
        │ Database │   │  Dashboard  │   │ Buzzer + │
        │          │   │             │   │   LED    │
        └──────────┘   └─────────────┘   └──────────┘
```

---

# 5. Complete Working Flow

### Step 1 — Camera Capture

The camera provides the video frames to the AI pipeline.

The system can process a physical camera feed when available.

If the physical camera is unavailable, the project can use a synthetic feed for demonstration and testing.

---

### Step 2 — Object Detection

Each frame is processed using **YOLOv8**.

The detector identifies objects and provides:

* Bounding box
* Class
* Confidence score

Relevant detected classes are categorized as humans or animals.

A confidence threshold is applied to reduce low-confidence detections.

```text
Camera Frame
     ↓
YOLOv8
     ↓
Bounding Box + Class + Confidence
```

---

### Step 3 — Object Tracking

YOLOv8 detects objects independently in each frame.

To maintain the identity of an object across multiple frames, the system uses **ByteTrack**.

Example:

```text
Frame 1 → Person → ID 1
Frame 2 → Person → ID 1
Frame 3 → Person → ID 1
Frame 4 → Person → ID 1
```

Maintaining the same tracking ID allows the system to analyze movement over time.

---

# 6. Why YOLOv8?

YOLOv8 is used because the project requires object detection from a continuous video stream.

Compared with traditional approaches, YOLO-based detection provides:

* Object localization
* Object classification
* Confidence scores
* Support for multiple objects
* Practical real-time inference

The project uses the lightweight **YOLOv8n** model to keep inference computationally practical.

---

# 7. Confidence Threshold

Every YOLO detection has a confidence score.

The project uses a configurable confidence threshold:

```text
CONFIDENCE_THRESHOLD = 0.50
```

Detections below the configured threshold are ignored.

The threshold provides a trade-off:

```text
Higher Threshold
    ↓
Fewer low-confidence detections
    +
Possibility of missing difficult objects

Lower Threshold
    ↓
More detections
    +
Possibility of more false positives
```

The value can be adjusted according to the camera environment and required detection sensitivity.

---

# 8. Why ByteTrack?

Detection alone cannot provide temporal information.

For example, YOLO can detect a person in multiple frames, but the system needs to know whether those detections represent the same person.

ByteTrack maintains track identities and provides persistent tracking IDs.

This enables:

* Movement analysis
* Direction detection
* Dwell-time calculation
* Track history
* Multi-object monitoring

Therefore:

```text
YOLOv8  → What is detected?
ByteTrack → Which object is it over time?
```

---

# 9. Ground-Contact Point

For zone evaluation, Smart Fence uses the **bottom-center of the bounding box**.

If the bounding box is:

```text
(x_min, y_min)
       ┌────────────┐
       │            │
       │   Object   │
       │            │
       └─────●──────┘
       (x_mid, y_max)
```

The ground point is:

```text
x_mid = (x_min + x_max) / 2
y_ground = y_max
```

So:

```text
Ground Point = (x_mid, y_max)
```

### Why?

The center of a person's bounding box usually represents the torso.

The bottom-center is closer to the person's feet and therefore provides a better representation of where the object is positioned on the ground.

---

# 10. Virtual Perimeter Zones

The monitored camera view is divided into three virtual zones.

### Safe Zone

The area relatively far from the physical fence.

### Warning Zone

The intermediate area where the system increases monitoring attention.

### Danger Zone

The area immediately near the monitored fence boundary.

The zones are represented using polygons.

The system checks whether the object's ground-contact point lies inside a particular polygon.

OpenCV's:

```text
cv2.pointPolygonTest()
```

is used for this spatial evaluation.

---

# 11. Movement Direction Analysis

The system stores recent ground positions for every tracking ID.

For example:

```text
ID 1:

(x1, y1, t1)
(x2, y2, t2)
(x3, y3, t3)
(x4, y4, t4)
```

The recent trajectory is analyzed to determine movement.

Because the fence is positioned towards the lower part of the camera view:

```text
Increasing Y
     ↓
Closer to Fence

Decreasing Y
     ↓
Away from Fence
```

The system classifies movement as:

```text
TOWARDS_FENCE
AWAY_FROM_FENCE
STATIONARY
```

A sliding window and linear trend analysis are used to reduce the effect of frame-to-frame bounding-box jitter.

---

# 12. Risk Assessment

The project does not treat every detection as the same type of threat.

The Risk Engine considers multiple factors:

```text
Object Class
     +
Zone
     +
Direction
     +
Dwell Time
     ↓
Risk Level
```

Possible risk levels are:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

For example, an animal in a warning zone and a human moving towards the fence in a danger zone can be treated differently by the risk engine.

The purpose is to make alerts more context-aware rather than simply triggering whenever motion is detected.

---

# 13. Alert Debouncing

A video pipeline can process many frames per second.

If an object remains in a danger zone for several seconds, the same event may appear in many consecutive frames.

Without debouncing:

```text
One Incident
     ↓
Many Frames
     ↓
Many Duplicate Alerts
```

Smart Fence uses an alert cooldown:

```text
ALERT_COOLDOWN_SECONDS = 5
```

After an alert is generated, repetitive alerts for the same continuing condition are suppressed during the cooldown period.

However, if the threat level increases, a new alert can be generated.

Example:

```text
MEDIUM
   ↓
HIGH
   ↓
CRITICAL
```

This prevents alert flooding while still allowing important risk escalation to be reported.

---

# 14. Backend Architecture

The backend is developed using **FastAPI**.

It acts as the communication layer between:

* AI pipeline
* Database
* Frontend
* ESP32

Main backend responsibilities include:

* Processing application requests
* Providing REST APIs
* Managing database operations
* Providing system status
* Handling alerts
* Providing live video streaming
* Broadcasting real-time events

---

# 15. REST API

REST APIs are used for communication between the backend and other system components.

For example, the backend can send an alert command to the ESP32.

Example:

```http
POST /api/alert
```

Payload:

```json
{
  "risk": "HIGH",
  "buzzer": true,
  "led": true,
  "reason": "Human approaching danger zone"
}
```

This allows the backend to control the warning hardware without directly handling the hardware logic itself.

---

# 16. WebSocket Communication

REST APIs are suitable for normal request-response operations.

For events that need to reach the dashboard immediately, the project uses WebSockets.

Flow:

```text
AI Pipeline
     ↓
Risk Escalation
     ↓
FastAPI Backend
     ↓
WebSocket
     ↓
React Dashboard
```

This allows the dashboard to receive important live events without waiting for a normal polling cycle.

---

# 17. MJPEG Live Streaming

The annotated camera feed is delivered to the frontend using **MJPEG streaming**.

The backend continuously sends JPEG frames through an HTTP multipart response.

Conceptually:

```text
JPEG Frame 1
     ↓
JPEG Frame 2
     ↓
JPEG Frame 3
     ↓
JPEG Frame 4
     ↓
     ...
```

The browser can display the stream directly through an image element.

This provides a relatively simple approach for displaying the annotated video feed in the web dashboard.

---

# 18. Database Design

The project uses:

**SQLite + SQLAlchemy ORM**

SQLite provides lightweight local relational storage, while SQLAlchemy provides structured interaction with the database.

Important entities include:

### Detection Records

Stores information related to detected and tracked objects.

### Alert Records

Stores generated security incidents and their status.

### Zone Records

Stores configurable virtual-zone information.

### System Logs

Stores system and subsystem events.

Conceptually:

```text
Detection
    │
    ├── Tracking ID
    ├── Object Class
    ├── Zone
    ├── Risk Level
    └── Timestamp

Alert
    │
    ├── Risk Level
    ├── Status
    ├── Acknowledgment
    └── Timestamp
```

---

# 19. IoT Layer — ESP32

The ESP32 provides the physical warning layer of the project.

Communication flow:

```text
FastAPI
   │
   │ Wi-Fi / HTTP
   ▼
ESP32
   │
   ├── Buzzer
   │
   └── LED
```

When the backend identifies a relevant risk condition, it can send an alert command to the ESP32.

The ESP32 then activates the configured warning output.

---

# 20. Buzzer and LED Control

The ESP32 controls:

* Piezo buzzer
* High-intensity LEDs

Different alert levels can be represented using different buzzer frequencies or patterns and different LED behaviors.

For example:

```text
Warning  → Lower-intensity indication
High     → Stronger buzzer / LED indication
Critical → High-priority warning pattern
```

The exact output behavior is controlled by the ESP32 firmware.

---

# 21. Why Non-Blocking Timing Is Used

The ESP32 should remain responsive to network requests while controlling LEDs and the buzzer.

Using long blocking `delay()` calls can prevent the controller from handling other tasks promptly.

Therefore, timing logic based on:

```text
millis()
```

can be used to perform non-blocking LED and alarm patterns.

This allows the ESP32 to continue handling communication while the warning indicators are active.

---

# 22. ESP32 Fail-Safe Behavior

The hardware layer considers communication failures.

If the expected communication from the backend is lost, the ESP32 can use a timeout mechanism rather than keeping an old alarm state active indefinitely.

The prototype therefore includes a safety-oriented fallback behavior for communication failures.

---

# 23. React Dashboard

The frontend is developed using:

* React
* Vite

The dashboard acts as the operator interface.

It provides visualization of:

* Live annotated camera feed
* Detection information
* Risk statistics
* Alert history
* System status
* System health
* Alert acknowledgment

The dashboard communicates with the FastAPI backend through REST APIs and WebSockets.

---

# 24. Dashboard Alert Acknowledgment

When an alert is generated, the operator can review and acknowledge it.

Conceptually:

```text
ACTIVE ALERT
     ↓
Operator Reviews
     ↓
ACKNOWLEDGED
```

This creates a basic incident-handling workflow instead of treating an alert as a simple notification.

---

# 25. Camera Fallback

The project supports a synthetic camera feed when a physical camera is unavailable.

The flow is:

```text
Physical Camera
      │
      ├── Available
      │      ↓
      │   Live Feed
      │
      └── Unavailable
             ↓
       Synthetic Feed
```

The synthetic feed can simulate a monitored scene and moving targets.

This is useful for:

* Development
* Testing
* Demonstration
* Debugging

It also reduces dependency on physical camera hardware during project presentation.

---

# 26. Testing

The project uses **Pytest** for automated testing.

The tests cover important decision-making components such as:

* Safe-zone classification
* Warning-zone classification
* Danger-zone classification
* Movement direction
* Stationary movement rejection
* Risk escalation
* Multiple tracking IDs
* Alert debouncing
* Camera failure behavior
* ESP32 communication failure behavior

Testing these components separately helps verify the core logic before relying on the complete live-video pipeline.

---

# 27. Project Design Pattern

The AI processing pipeline follows a **Pipes and Filters** style architecture.

```text
Camera Capture
      ↓
Detection
      ↓
Tracking
      ↓
Zone Evaluation
      ↓
Movement Analysis
      ↓
Risk Assessment
      ↓
Annotation
      ↓
Alert / Dispatch
```

Each stage performs a specific task.

This separation makes individual components easier to understand, modify, and test.

---

# 28. Technology Stack

| Layer                  | Technology | Purpose                        |
| ---------------------- | ---------- | ------------------------------ |
| Object Detection       | YOLOv8     | Detect humans and animals      |
| Object Tracking        | ByteTrack  | Maintain object identities     |
| Computer Vision        | OpenCV     | Image processing and geometry  |
| Backend                | FastAPI    | APIs and application logic     |
| Validation             | Pydantic   | Validate API data              |
| Database               | SQLite     | Store application data         |
| ORM                    | SQLAlchemy | Database interaction           |
| Frontend               | React      | Monitoring dashboard           |
| Build Tool             | Vite       | Frontend development           |
| Real-Time Events       | WebSocket  | Live dashboard updates         |
| Video Streaming        | MJPEG      | Live annotated feed            |
| IoT Controller         | ESP32      | Hardware alert control         |
| Hardware Communication | HTTP/REST  | Backend-to-ESP32 communication |
| Testing                | Pytest     | Automated testing              |

---

# 29. Security and Safety Considerations

The project is designed as a **prototype early-warning system**.

The ESP32 hardware should remain electrically isolated from any high-voltage electric fence system.

The prototype uses:

```text
AI Detection
     ↓
Risk Decision
     ↓
Non-Lethal Warning
     ↓
Buzzer + LED
```

It does not directly control or energize a high-voltage fence.

This separation is important for protecting both people and the prototype electronics.

---

# 30. Current Limitations

### Monocular Camera

A single camera provides image coordinates rather than direct physical distance.

The current system therefore does not provide reliable real-world distance measurements in meters.

### Nighttime Conditions

A normal visible-light camera may perform poorly in very low-light environments.

### Weather Conditions

Heavy rain, fog, dust, or lens obstruction can reduce object-detection quality.

### Model Dependency

Detection performance depends on the trained model, camera quality, scene conditions, and target appearance.

---

# 31. Future Enhancements

### Metric Distance Estimation

Camera calibration and homography can map image coordinates to real-world ground coordinates.

### Stereo Vision / LiDAR

Depth sensors can provide more direct physical distance information.

### Thermal Imaging

Thermal cameras can improve detection in low-light and nighttime environments.

### Edge AI

The AI pipeline can be deployed on dedicated edge-computing hardware.

### PTZ Camera

A PTZ camera could automatically focus on high-risk targets.

### Multi-Camera Monitoring

Multiple cameras could provide wider perimeter coverage.

### Cloud Monitoring

Security events could be synchronized to a cloud platform for remote monitoring and historical analytics.

---

# 32. End-to-End Example

Consider a person entering the monitored area.

```text
Person enters camera view
          ↓
YOLOv8 detects person
          ↓
ByteTrack assigns Tracking ID
          ↓
Bottom-center ground point calculated
          ↓
Object enters Warning Zone
          ↓
Movement history analyzed
          ↓
Object is moving TOWARDS_FENCE
          ↓
Risk Engine evaluates the situation
          ↓
Risk level increases
          ↓
Alert generated
          ↓
Alert stored in SQLite
          ↓
Dashboard receives live event
          ↓
ESP32 receives HTTP command
          ↓
Buzzer + LED activated
```

This example represents the complete project workflow from **camera input to AI analysis to software and hardware response**.

---

# 33. Project Summary

Smart Fence integrates multiple technologies into one intelligent monitoring workflow:

```text
Computer Vision
       +
Object Tracking
       +
Spatial Analysis
       +
Risk Assessment
       +
Backend
       +
Database
       +
Web Dashboard
       +
IoT Hardware
```

The main technical idea is to move beyond simple motion detection and use multiple contextual factors—**object type, location, movement, and time**—to make the monitoring system more informative and responsive.

The prototype focuses on providing an **early, non-lethal warning** before an individual or animal reaches the physical fence.
