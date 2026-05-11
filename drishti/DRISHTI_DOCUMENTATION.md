# DRISHTI — System Documentation

> **D**ensity **R**ecognition and **I**ntelligent **S**urveillance for **H**azard **T**hreshold **I**dentification

---

## Table of Contents

1. [Overview](#overview)
2. [Models Used](#models-used)
3. [Dataset](#dataset)
4. [Model Accuracy & Evaluation](#model-accuracy--evaluation)
5. [Tech Stack](#tech-stack)
6. [System Architecture](#system-architecture)
7. [Frontend–Backend Connection](#frontendbackend-connection)
8. [Database Schema](#database-schema)
9. [API Endpoints](#api-endpoints)
10. [Alert Escalation Logic](#alert-escalation-logic)
11. [How to Run](#how-to-run)

---

## Overview

DRISHTI is a real-time crowd density monitoring and hazard detection platform. It uses deep learning models to count people in uploaded images and videos, logs data to a cloud database (Supabase), and triggers alerts when crowd counts exceed configurable thresholds.

The system is designed for surveillance operators monitoring public spaces such as religious gatherings, stadiums, transit hubs, and festivals.

---

## Models Used

### 1. YOLO-CROWD (Detection-Based Counting)

| Property | Value |
|----------|-------|
| **Architecture** | YOLOv5 (Modified for crowd detection) |
| **Approach** | Object detection — draws bounding boxes around each person and counts them |
| **Weights File** | `yolo-crowd.pt` (37.2 MB) |
| **Engine File** | `yolo-crowd.engine` (85.4 MB, TensorRT optimized) |
| **Input Size** | 640 × 640 pixels |
| **Backend** | PyTorch + CUDA |
| **Inference Type** | Single-class detection (class 0 = person) |
| **NMS** | Non-Maximum Suppression with confidence threshold 0.3, IoU threshold 0.45 |

**How it works:**
1. Input image is resized to 640×640 using letterbox padding
2. YOLOv5 backbone extracts features via CSPDarknet53
3. Detection head outputs bounding boxes with confidence scores
4. Non-Maximum Suppression filters overlapping detections
5. Final count = number of remaining bounding boxes

**Strengths:** Fast inference, individual person localization, works well in sparse to medium crowds.  
**Weakness:** Caps at ~300 detections per image, struggles with highly dense crowds where individuals overlap significantly.

---

### 2. CSRNet (Density Estimation-Based Counting)

| Property | Value |
|----------|-------|
| **Architecture** | CSRNet — Congested Scene Recognition Network |
| **Backbone** | VGG-16 (first 10 layers as feature extractor) |
| **Backend Layers** | 6 dilated convolutional layers (dilation rates: 2, 2, 2, 2, 2, 2) |
| **Approach** | Density map estimation — predicts a heat map where pixel values represent person density |
| **Weights File** | `modelCRNet.pt` (65 MB) |
| **Input** | Variable-size RGB image (normalized with ImageNet mean/std) |
| **Output** | Density map — crowd count = sum of all pixel values |

**How it works:**
1. Input image is normalized using ImageNet statistics (mean: [0.485, 0.456, 0.406], std: [0.229, 0.224, 0.225])
2. VGG-16 frontend extracts multi-scale features
3. Dilated convolution backend generates a density map (same spatial resolution)
4. Each pixel value represents estimated number of people at that location
5. Total count = sum of all density map pixel values

**Strengths:** Handles extremely dense crowds (1000+ people), no upper count limit, produces visual density heat maps.  
**Weakness:** Slower inference, no individual localization, may over/under-estimate in sparse scenes.

---

## Dataset

### ShanghaiTech Part A

| Property | Value |
|----------|-------|
| **Name** | ShanghaiTech Crowd Counting Dataset — Part A |
| **Source** | Zhang et al., "Single-Image Crowd Counting via Multi-Column Convolutional Neural Network" (CVPR 2016) |
| **Scene Type** | Highly congested scenes (festivals, rallies, public gatherings) |
| **Training Images** | 300 |
| **Test Images** | 182 |
| **Annotation Type** | Dot annotations (center of each person's head) |
| **Count Range** | Min: 66 — Max: 2,256 — Mean: 433.3 people per image |
| **Resolution** | Variable (high-resolution photos) |

The dataset contains crowd images scraped from the internet, representing some of the most challenging crowd counting scenarios with extreme occlusion, perspective variation, and scale differences.

---

## Model Accuracy & Evaluation

Both models were evaluated on the **ShanghaiTech Part A test set** (182 images).

### Comparative Results

| Metric | YOLO-CROWD | CSRNet | Winner |
|--------|-----------|--------|--------|
| **MAE** (Mean Absolute Error) | 208.99 | **71.45** | ✅ CSRNet |
| **RMSE** (Root Mean Squared Error) | 377.87 | **110.25** | ✅ CSRNet |
| **Mean Error** | -203.60 (under-counts) | **1.01** (nearly unbiased) | ✅ CSRNet |
| **Predicted Range** | 46 – 300 | 52 – 1,838 | ✅ CSRNet |
| **Inference Speed** | **~0.0ms** (GPU) | ~50-100ms | ✅ YOLO |

### Key Observations

**YOLO-CROWD:**
- Caps detections at ~300 people, causing severe under-counting in dense scenes (GT: 1175 → Pred: 300)
- Performs well in low-density scenes (GT: 172 → Pred: 171, error: -1)
- Mean error of -203.60 indicates systematic under-counting
- Best suited for scenes with < 300 people

**CSRNet:**
- Near-zero bias (mean error: 1.01) — predictions are evenly distributed around ground truth
- Handles dense crowds effectively (GT: 1175 → Pred: 1269, GT: 1232 → Pred: 1358)
- MAE of 71.45 is competitive with state-of-the-art on this benchmark
- Better overall accuracy but slower than YOLO

### When to Use Which Model

| Scenario | Recommended Model |
|----------|------------------|
| Sparse crowds (< 200 people) | YOLO-CROWD |
| Dense crowds (> 300 people) | CSRNet |
| Need individual locations/bounding boxes | YOLO-CROWD |
| Need density heat map visualization | CSRNet |
| Real-time webcam processing | YOLO-CROWD |
| Static image analysis | CSRNet |

---

## Tech Stack

### Backend

| Technology | Role | Version |
|-----------|------|---------|
| **Python** | Core language | 3.10 |
| **FastAPI** | REST API framework | Latest |
| **Uvicorn** | ASGI server | Latest |
| **PyTorch** | Deep learning runtime | 2.5.1+cu121 |
| **CUDA** | GPU acceleration | 12.1 |
| **OpenCV** | Image/video processing | Latest |
| **Supabase Python** | Database client | Latest |
| **python-dotenv** | Environment configuration | Latest |
| **python-multipart** | File upload handling | Latest |
| **Pydantic** | Data validation & schemas | v2 (via FastAPI) |

### Frontend

| Technology | Role | Version |
|-----------|------|---------|
| **Next.js** | React framework (App Router) | 16.2.5 |
| **React** | UI library | 19 |
| **TypeScript** | Type-safe JavaScript | 5+ |
| **Tailwind CSS** | Utility-first styling | 4 |
| **@supabase/supabase-js** | Database client | Latest |
| **Inter** | Typography (Google Font) | — |

### Infrastructure

| Technology | Role |
|-----------|------|
| **Supabase** | Cloud PostgreSQL database + Row-Level Security |
| **NVIDIA RTX 2050** | GPU for model inference (4 GB VRAM) |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DRISHTI ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────────┐            │
│  │   Next.js 16     │  HTTP   │    FastAPI Backend    │            │
│  │   Frontend       │◄──────►│    (Port 8000)        │            │
│  │   (Port 3000)    │  REST   │                      │            │
│  │                  │  + SSE  │  ┌────────────────┐  │            │
│  │  ┌────────────┐  │         │  │  YOLO-CROWD    │  │            │
│  │  │ MediaUpload │──────────►│  │  yolo-crowd.pt │  │            │
│  │  │ LiveCounter │◄─── SSE ──│  └────────────────┘  │            │
│  │  │ AlertConsole│◄─── SSE ──│  ┌────────────────┐  │            │
│  │  │ ModelSelect │  │         │  │  CSRNet        │  │            │
│  │  └────────────┘  │         │  │  modelCRNet.pt │  │            │
│  └─────────────────┘         │  └────────────────┘  │            │
│           │                   │         │            │            │
│           │                   └─────────┼────────────┘            │
│           │                             │                         │
│           ▼                             ▼                         │
│  ┌─────────────────────────────────────────────┐                 │
│  │              Supabase (PostgreSQL)            │                 │
│  │  ┌─────────────┬──────────┬────────────────┐ │                 │
│  │  │ count_logs  │  alerts  │ analytics_daily│ │                 │
│  │  └─────────────┴──────────┴────────────────┘ │                 │
│  └───────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend–Backend Connection

### How the UI Connects to the Backend

The frontend communicates with the FastAPI backend through **three channels**:

#### 1. REST API (Request/Response)

Used for one-off actions like image upload, alert acknowledgment, and settings changes.

```
Frontend (fetch/XHR)  ──►  FastAPI (POST /api/count)  ──►  Response JSON
```

**Flow for image/video upload:**
1. User drops a file on `MediaUpload` component
2. `XMLHttpRequest` sends file as `multipart/form-data` to `POST /api/count`
3. Backend saves file, extracts frame (if video), runs inference
4. Backend logs count to Supabase, evaluates alert threshold
5. Returns JSON: `{ count, model_used, source_type, density_path, alert }`
6. Frontend updates `LiveCounter`, `StatCard`, and `AlertConsole`

#### 2. Server-Sent Events — SSE (Real-Time Push)

Used for real-time streaming updates without polling.

```
Frontend (EventSource)  ◄──  FastAPI (GET /ws/count)  ──  Continuous stream
Frontend (EventSource)  ◄──  FastAPI (GET /ws/alerts)  ──  Continuous stream
```

**How SSE works:**
1. Frontend creates `EventSource` connection to `/ws/count` and `/ws/alerts`
2. Backend keeps connection open, sends `data: {...}\n\n` events
3. Every time a count is processed, backend pushes update to all subscribers
4. Frontend `LiveCounter` animates the count change
5. `AlertConsole` shows new alerts and triggers browser notification
6. If connection drops, frontend auto-reconnects after 5 seconds

#### 3. Browser Notifications (Push)

When an alert is triggered:
1. Backend sends alert via SSE to `AlertConsole`
2. Frontend calls `new Notification()` with alert details
3. Desktop notification appears with 🚨 or ⚠️ icon

### Environment Configuration

```
# Frontend (.env.local)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend (.env)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
ALERT_THRESHOLD=500
```

---

## Database Schema

### `count_logs` — Every inference result

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Auto-generated |
| timestamp | TIMESTAMPTZ | When the count was made |
| count_value | INTEGER | Number of people detected |
| model_used | VARCHAR(20) | `yolo` or `csrnet` |
| source_type | VARCHAR(20) | `image`, `video`, or `webcam` |
| threshold | INTEGER | Active threshold at time of count |
| file_path | TEXT | Path to uploaded file |

### `alerts` — Threshold breach events

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Auto-generated |
| count_log_id | UUID (FK) | Links to the count that triggered it |
| alert_type | VARCHAR(20) | `warning`, `critical`, or `escalated` |
| threshold_value | INTEGER | Threshold that was exceeded |
| count_value | INTEGER | The actual count |
| acknowledged | BOOLEAN | Has an operator acknowledged it |
| acknowledged_by | VARCHAR(100) | Who acknowledged |
| notification_sent | BOOLEAN | Was browser notification sent |

### `analytics_daily` — Aggregated daily stats

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Auto-generated |
| date | DATE (unique) | The date |
| total_counts | INTEGER | Number of scans that day |
| avg_count | REAL | Average crowd count |
| max_count | INTEGER | Peak crowd count |
| alert_count | INTEGER | Number of alerts triggered |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/count` | Upload image/video for inference |
| `GET` | `/api/alerts` | Fetch alert history |
| `POST` | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| `POST` | `/api/alerts/send` | Send a test alert |
| `GET` | `/api/settings/threshold` | Get current threshold |
| `POST` | `/api/settings/threshold` | Update threshold |
| `GET` | `/ws/count` | SSE stream for real-time counts |
| `GET` | `/ws/alerts` | SSE stream for real-time alerts |
| `GET` | `/stream/{model}` | MJPEG video stream (live/webcam) |

---

## Alert Escalation Logic

```
Count ≤ threshold           →  No alert (SAFE ✅)
Count > threshold           →  WARNING ⚠️  (browser notification)
Count > threshold × 1.5     →  CRITICAL 🚨 (browser notification)
Count > threshold × 1.5     →  ESCALATED 🆘 (SMS — planned, not yet active)
```

Default threshold: **500 people** (configurable via Settings page)

---

## How to Run

### Prerequisites
- Python 3.10+, Node.js 18+, NVIDIA GPU with CUDA 12.1

### 1. Backend
```bash
cd d:\Crowd-Counting-Platform
uvicorn drishti.backend.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd d:\Crowd-Counting-Platform\drishti\frontend
npm run dev
```

### 3. Open Dashboard
Navigate to **http://localhost:3000**

---

## Project Structure

```
drishti/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── count_ws.py           # SSE + upload/inference endpoint
│   ├── alert_manager.py      # Threshold logic + alert CRUD
│   ├── stream_router.py      # MJPEG video streaming
│   ├── schemas.py            # Pydantic data models
│   ├── supabase_client.py    # Database CRUD helpers
│   └── .env                  # Supabase credentials
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx      # Dashboard (main page)
│   │   │   ├── alerts/       # Alert history page
│   │   │   ├── settings/     # Configuration page
│   │   │   ├── layout.tsx    # Root layout + sidebar
│   │   │   └── globals.css   # Design system
│   │   ├── components/
│   │   │   ├── MediaUpload   # Image/video upload + analysis
│   │   │   ├── LiveCounter   # Animated count display
│   │   │   ├── AlertConsole  # Real-time alert feed
│   │   │   ├── ModelSelector # YOLO/CSRNet toggle
│   │   │   ├── Sidebar       # Navigation
│   │   │   ├── StatCard      # Metric cards
│   │   │   └── ThresholdSettings
│   │   └── lib/
│   │       └── supabase.ts   # Client + type definitions
│   └── .env.local            # Frontend env vars
│
└── supabase/
    └── migrations/
        ├── 001_init.sql       # Table creation
        └── 002_rls_policies.sql # Row-level security
```

---

*Document generated for DRISHTI v1.0.0*
