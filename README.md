# DRISHTI Surveillance Platform

> **D**ensity **R**ecognition and **I**ntelligent **S**urveillance for **H**azard **T**hreshold **I**dentification

DRISHTI is a real-time crowd density monitoring and hazard detection system. It leverages state-of-the-art computer vision models (YOLO-CROWD & CSRNet) to automatically count crowds, logs all detection data to a cloud database (Supabase), and triggers instant visual and simulated SMS notifications when crowd counts exceed configurable safety thresholds.

---

## 🚀 Key Features

* **Dual AI Architectures**:
  * **YOLO-CROWD** (`yolo-crowd.pt`): Fast object-detection-based counting, drawing individual bounding boxes. Best for sparse to medium crowds.
  * **CSRNet** (`modelCRNet.pt`): Dilated CNN density map estimator. Best for highly congested dense crowds (1000+ people).
* **Cloud-Native Storage**: Automatically pushes inference media and heatmaps directly to Supabase Storage buckets, saving local disk space and allowing high-speed CDN delivery.
* **Live Hardware Streaming**: Integrates a live MJPEG stream (e.g. from a Raspberry Pi) and passes frames asynchronously to the AI engine for real-time crowd monitoring.
* **Surveillance Operator Dashboard**: Modern Next.js frontend styled like a premium security command center console.
* **Dynamic Safety Thresholds**: Configurable crowd thresholds with animated indicators and real-time status updates.
* **Advanced Alert Console**: Instant browser pushes and a hybrid **Twilio Notification Service** (SMS for Warnings, automated Voice Calls for Critical alerts).
* **Server-Sent Events (SSE)**: Real-time backend streaming of counts and alerts without page polling.
* **Interactive Heatmaps**: Precision zoom and pan controls for color-coded crowd density heatmaps rendered directly from the cloud.

---

## 🛠️ Getting Started

### 1. Clone the Repository
This project uses **Git LFS** (Large File Storage) to manage model weights. Make sure you have Git LFS installed:
```bash
git lfs install
git clone https://github.com/muzzy-141104/IDP-PS27.git
cd IDP-PS27
```

### 2. Configure Database & Env (Supabase)
Create a Supabase project and run the SQL scripts located in:
* [001_init.sql](file:///d:/Crowd-Counting-Platform/drishti/supabase/migrations/001_init.sql)
* [002_rls_policies.sql](file:///d:/Crowd-Counting-Platform/drishti/supabase/migrations/002_rls_policies.sql)

Configure the environment files:
* **Backend Env**: Create `drishti/backend/.env` with your Supabase credentials:
  ```env
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_KEY=your-anon-or-service-role-key
  ALERT_THRESHOLD=500
  TWILIO_ACCOUNT_SID=your_twilio_sid
  TWILIO_AUTH_TOKEN=your_twilio_token
  TWILIO_PHONE_NUMBER=+1234567890
  TARGET_PHONE_NUMBER=+0987654321
  ```
* **Frontend Env**: Create `drishti/frontend/.env.local` with:
  ```env
  NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

---

## 🏃 Running the Application

### 1. Start the FastAPI Backend
```bash
pip install -r requirements.txt
uvicorn drishti.backend.main:app --reload --port 8000
```
API docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start the Next.js Frontend
```bash
cd drishti/frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 📖 Project Structure

```
drishti/
├── backend/               # FastAPI Backend Router, Managers, and SSE Pipelines
│   ├── main.py            # API entry point
│   ├── count_ws.py        # SSE streams & media upload inference
│   ├── alert_manager.py   # Safety threshold evaluation & alert router
│   ├── notifications.py   # Twilio Hybrid SMS/Voice integration
│   └── supabase_client.py # Supabase database & storage integration
├── frontend/              # Next.js 16 (App Router) + React 19 Frontend Dashboard
│   ├── src/components/    # MediaUpload, AlertConsole, LiveCounter, Sidebar
│   └── src/app/           # Dashboard Page, Alerts Table, Heatmap Zoom View
└── supabase/              # PostgreSQL Database Init Migrations
```

---

## ⚖️ License
This project is licensed under the MIT License.
