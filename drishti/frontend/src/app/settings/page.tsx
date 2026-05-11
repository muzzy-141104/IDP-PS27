'use client'

import { useState, useEffect } from 'react'
import ThresholdSettings from '@/components/ThresholdSettings'
import { API_URL } from '@/lib/supabase'

export default function SettingsPage() {
  const [threshold, setThreshold] = useState(500)

  useEffect(() => {
    fetch(`${API_URL}/api/settings/threshold`)
      .then(res => res.json())
      .then(data => {
        if (data.threshold) setThreshold(data.threshold)
      })
      .catch(() => {})
  }, [])

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          <span className="gradient-text">Settings</span>
        </h1>
        <p className="text-xs text-[var(--drishti-text-dim)] mt-1">
          Configure thresholds, notifications, and system preferences
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Threshold */}
        <ThresholdSettings threshold={threshold} onThresholdChange={setThreshold} />

        {/* System Info */}
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-6">
            <svg className="w-5 h-5 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            <h3 className="text-sm font-semibold text-[var(--drishti-text)]">System Information</h3>
          </div>

          <div className="space-y-3">
            <InfoRow label="API Endpoint" value={API_URL} />
            <InfoRow label="Active Models" value="YOLO-CROWD, CSRNet" />
            <InfoRow label="Alert Method" value="Browser Push Notification" />
            <InfoRow label="Database" value="Supabase (PostgreSQL)" />
            <InfoRow label="Stream Protocol" value="MJPEG" />
            <InfoRow label="Version" value="1.0.0" />
          </div>
        </div>

        {/* Notification Settings */}
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-6">
            <svg className="w-5 h-5 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <h3 className="text-sm font-semibold text-[var(--drishti-text)]">Notification Settings</h3>
          </div>

          <div className="space-y-4">
            <ToggleRow label="Browser Push Notifications" description="Show desktop alerts when threshold is exceeded" defaultOn={true} />
            <ToggleRow label="In-App Alerts" description="Display alerts in the dashboard console" defaultOn={true} />
            <ToggleRow label="Sound Alerts" description="Play alert sound when threshold is breached" defaultOn={false} />

            <div className="pt-3 border-t border-[var(--drishti-border)]">
              <p className="text-xs text-[var(--drishti-text-dim)] mb-3">SMS notifications require Twilio configuration</p>
              <ToggleRow label="SMS to Police" description="Send SMS to police when critical threshold is exceeded" defaultOn={false} disabled />
              <ToggleRow label="SMS to Ambulance" description="Send SMS to ambulance services" defaultOn={false} disabled />
              <ToggleRow label="SMS to Fire Department" description="Send SMS to fire services" defaultOn={false} disabled />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass p-6">
          <div className="flex items-center gap-2 mb-6">
            <svg className="w-5 h-5 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            <h3 className="text-sm font-semibold text-[var(--drishti-text)]">Quick Actions</h3>
          </div>

          <div className="space-y-3">
            <ActionButton
              label="Send Test Alert"
              description="Trigger a test notification"
              icon="🔔"
              onClick={async () => {
                try {
                  await fetch(`${API_URL}/api/alerts/send`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: 'Test alert', count_value: threshold + 100 }),
                  })
                } catch {}
              }}
            />
            <ActionButton
              label="Request Notification Permission"
              description="Enable browser notifications"
              icon="🔓"
              onClick={() => {
                if ('Notification' in window) {
                  Notification.requestPermission()
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[var(--drishti-border)] last:border-0">
      <span className="text-xs text-[var(--drishti-text-muted)]">{label}</span>
      <span className="text-xs font-mono text-[var(--drishti-text)]">{value}</span>
    </div>
  )
}

function ToggleRow({ label, description, defaultOn = false, disabled = false }: {
  label: string; description: string; defaultOn?: boolean; disabled?: boolean
}) {
  const [isOn, setIsOn] = useState(defaultOn)
  return (
    <div className={`flex items-center justify-between py-2 ${disabled ? 'opacity-40' : ''}`}>
      <div>
        <p className="text-xs font-medium text-[var(--drishti-text)]">{label}</p>
        <p className="text-[10px] text-[var(--drishti-text-dim)]">{description}</p>
      </div>
      <button
        onClick={() => !disabled && setIsOn(!isOn)}
        className={`w-9 h-5 rounded-full transition-colors relative cursor-pointer ${isOn ? 'bg-indigo-500' : 'bg-white/10'} ${disabled ? 'cursor-not-allowed' : ''}`}
      >
        <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${isOn ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </button>
    </div>
  )
}

function ActionButton({ label, description, icon, onClick }: {
  label: string; description: string; icon: string; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 rounded-xl border border-[var(--drishti-border)] hover:border-[var(--drishti-border-hover)] hover:bg-white/[0.02] transition-all text-left cursor-pointer"
    >
      <span className="text-xl">{icon}</span>
      <div>
        <p className="text-xs font-medium text-[var(--drishti-text)]">{label}</p>
        <p className="text-[10px] text-[var(--drishti-text-dim)]">{description}</p>
      </div>
    </button>
  )
}
