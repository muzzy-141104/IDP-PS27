# DRISHTI — Design Specification

**Project**: DRISHTI — Density Recognition and Intelligent Surveillance for Hazard Threshold Identification

**Date**: 2026-05-07

**Status**: Approved

---

## 1. Overview

DRISHTI is a real-time crowd counting and alert system that uses YOLO-CROWD and CSRNet models to monitor crowd density and send emergency notifications when thresholds are exceeded. The system consists of a Next.js frontend dashboard, FastAPI backend, and Supabase database.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      NEXT.JS FRONTEND                          │
│   Dashboard  │  Live Feed (MJPEG)  │  Alert Console           │
└──────┬───────────────┬─────────────────┬────────────────────────┘
       │               │                 │
       │ SSE/WebSocket │  MJPEG Stream   │  REST API
       ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ /ws/count    │  │ /stream/{m}  │  │ /api/...             │  │
│  │ (real-time)  │  │ (existing     │  │ (alerts, records)    │  │
│  │              │  │  VideoCamera)│  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                     ┌─────────────┐
                     │  Supabase   │
                     └─────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS | Dashboard, real-time UI |
| Backend | FastAPI (Python) | API endpoints, streaming |
| ML Inference | Existing camera_*.py files | YOLO/CSRNet video processing |
| Real-time | Server-Sent Events (SSE) | Live count updates to dashboard |
| Database | Supabase (PostgreSQL) | Count logs, alerts, analytics |
| Notifications | Browser Push + In-app + SMS (Twilio) | Emergency alerts |

---

## 4. Components

### 4.1 Frontend (Next.js)

**Pages:**
- `/` — Main dashboard with live counter, camera feed, alert console
- `/alerts` — Alert history and management
- `/settings` — Threshold configuration

**Key Components:**
- `LiveCounter.tsx` — Real-time crowd count display with trend indicator
- `CameraFeed.tsx` — MJPEG video stream player (connects to `/stream/{model}`)
- `AlertConsole.tsx` — Live alert feed with acknowledgement
- `ModelSelector.tsx` — Toggle between YOLO-CROWD and CSRNet
- `ThresholdSettings.tsx` — Configure alert threshold (default: 500)

### 4.2 Backend (FastAPI)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stream/{model}` | MJPEG stream (yolo/csrnet) |
| WS | `/ws/count` | SSE for real-time count updates |
| POST | `/api/count` | Upload image, returns count + density map |
| GET | `/api/alerts` | Alert history |
| POST | `/api/alerts/send` | Trigger manual emergency alert |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |

### 4.3 ML Inference Layer (Existing — No Changes)

- `camera_yolo.py` — VideoCamera.get_frame() returns MJPEG bytes
- `camera_csrnet.py` — VideoCamera.get_frame() returns MJPEG bytes
- `inferenceYOLO.py` — Single image inference
- `inferenceCRNet.py` — Single image inference

### 4.4 Database (Supabase)

**Tables:**

```sql
-- count_logs: every inference result
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
timestamp       TIMESTAMPTZ DEFAULT NOW()
count_value     INTEGER
model_used      TEXT (yolo/csrnet)
source_type     TEXT (image/video/webcam)
threshold       INTEGER
file_path       TEXT

-- alerts: threshold breach events
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
count_log_id    UUID REFERENCES count_logs(id)
alert_type      TEXT (warning/critical/escalated)
threshold_value INTEGER
count_value     INTEGER
notification_sent BOOLEAN DEFAULT FALSE
sms_dispatch_id TEXT
police_notified  BOOLEAN DEFAULT FALSE
ambulance_notified BOOLEAN DEFAULT FALSE
fire_notified    BOOLEAN DEFAULT FALSE
acknowledged     BOOLEAN DEFAULT FALSE
acknowledged_by  TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()

-- analytics_daily: aggregated stats
date            DATE PRIMARY KEY
total_counts    INTEGER
avg_count       FLOAT
max_count       INTEGER
alert_count     INTEGER
```

---

## 5. Alert Escalation Logic

```
Count > 500?
├── YES → Browser Push Notification
├── YES → Create Alert Record in DB
├── YES → If count > 750 (1.5x threshold):
│         ├── SMS to Police
│         ├── SMS to Ambulance
│         └── SMS to Fire Department
└── NO  → Continue monitoring
```

**Alert Types:**
- `warning` — count between threshold and 1.5x threshold
- `critical` — count exceeds 1.5x threshold
- `escalated` — SMS sent to emergency services

---

## 6. File Structure

```
drishti/
├── frontend/                   # Next.js 14
│   ├── app/
│   │   ├── page.tsx
│   │   ├── alerts/page.tsx
│   │   └── settings/page.tsx
│   ├── components/
│   │   ├── LiveCounter.tsx
│   │   ├── CameraFeed.tsx
│   │   ├── AlertConsole.tsx
│   │   ├── ModelSelector.tsx
│   │   └── ThresholdSettings.tsx
│   ├── lib/
│   │   └── supabase.ts
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                    # FastAPI
│   ├── main.py
│   ├── stream_router.py       # Wraps existing camera_*.py
│   ├── count_ws.py            # SSE for real-time counts
│   ├── alert_manager.py       # Threshold logic + notifications
│   ├── schemas.py             # Pydantic models
│   └── requirements.txt
│
├── inference/                  # EXISTING — no changes
│   ├── camera_yolo.py
│   ├── camera_csrnet.py
│   ├── inferenceYOLO.py
│   └── inferenceCRNet.py
│
└── supabase/
    └── migrations
        └── 001_init.sql
```

---

## 7. Constraints

- **No model modifications** — inferenceYOLO.py, inferenceCRNet.py, camera_yolo.py, camera_csrnet.py remain unchanged
- **Local deployment** — no cloud services required for MVP
- **MJPEG compatibility** — live stream must use existing VideoCamera pattern
- **Supabase** — database choice made by user

---

## 8. Implementation Priority

1. Set up FastAPI backend with streaming endpoints
2. Connect existing camera_*.py to FastAPI stream router
3. Set up Supabase tables
4. Build Next.js dashboard
5. Implement alert escalation logic
6. Add SMS notifications via Twilio