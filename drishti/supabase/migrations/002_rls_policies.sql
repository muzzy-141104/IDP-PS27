-- DRISHTI RLS Policies
-- Run this in Supabase SQL Editor to allow the backend to read/write data

-- count_logs: allow all operations
ALTER TABLE count_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all inserts on count_logs"
  ON count_logs FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow all selects on count_logs"
  ON count_logs FOR SELECT
  USING (true);

CREATE POLICY "Allow all updates on count_logs"
  ON count_logs FOR UPDATE
  USING (true);

-- alerts: allow all operations
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all inserts on alerts"
  ON alerts FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow all selects on alerts"
  ON alerts FOR SELECT
  USING (true);

CREATE POLICY "Allow all updates on alerts"
  ON alerts FOR UPDATE
  USING (true);

-- analytics_daily: allow all operations
ALTER TABLE analytics_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all inserts on analytics_daily"
  ON analytics_daily FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow all selects on analytics_daily"
  ON analytics_daily FOR SELECT
  USING (true);

CREATE POLICY "Allow all updates on analytics_daily"
  ON analytics_daily FOR UPDATE
  USING (true);
