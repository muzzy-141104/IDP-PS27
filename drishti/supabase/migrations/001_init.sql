-- DRISHTI Database Schema
-- Run this in your Supabase SQL Editor

-- count_logs: every inference result
CREATE TABLE IF NOT EXISTS count_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    count_value     INTEGER NOT NULL,
    model_used      TEXT NOT NULL,         -- 'yolo' or 'csrnet'
    source_type     TEXT NOT NULL,         -- 'image', 'video', 'webcam'
    threshold       INTEGER NOT NULL DEFAULT 500,
    file_path       TEXT
);

-- alerts: threshold breach events
CREATE TABLE IF NOT EXISTS alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    count_log_id        UUID REFERENCES count_logs(id),
    alert_type          TEXT NOT NULL,     -- 'warning', 'critical', 'escalated'
    threshold_value     INTEGER NOT NULL,
    count_value         INTEGER NOT NULL,
    notification_sent   BOOLEAN DEFAULT FALSE,
    sms_dispatch_id     TEXT,
    police_notified     BOOLEAN DEFAULT FALSE,
    ambulance_notified  BOOLEAN DEFAULT FALSE,
    fire_notified       BOOLEAN DEFAULT FALSE,
    acknowledged        BOOLEAN DEFAULT FALSE,
    acknowledged_by     TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- analytics_daily: aggregated stats
CREATE TABLE IF NOT EXISTS analytics_daily (
    date            DATE PRIMARY KEY,
    total_counts    INTEGER DEFAULT 0,
    avg_count       FLOAT DEFAULT 0,
    max_count       INTEGER DEFAULT 0,
    alert_count     INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_count_logs_timestamp ON count_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);

-- Enable Realtime on alerts table (for Supabase Realtime subscriptions)
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE count_logs;
