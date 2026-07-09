'use client'

import { useState, useEffect, useRef } from 'react'
import { API_URL, type Alert } from '@/lib/supabase'

interface AlertConsoleProps {
  maxItems?: number
}

export default function AlertConsole({ maxItems = 20 }: AlertConsoleProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Fetch initial alerts
  useEffect(() => {
    fetch(`${API_URL}/api/alerts`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setAlerts(data.slice(0, maxItems))
      })
      .catch(() => {})
  }, [maxItems])

  // SSE for real-time alerts
  useEffect(() => {
    let eventSource: EventSource | null = null

    const connect = () => {
      eventSource = new EventSource(`${API_URL}/ws/alerts`)

      eventSource.onopen = () => setIsConnected(true)

      eventSource.onmessage = (event) => {
        try {
          const alert = JSON.parse(event.data) as Alert
          setAlerts(prev => [alert, ...prev].slice(0, maxItems))

          // Browser notification
          if (Notification.permission === 'granted') {
            const icon = alert.alert_type === 'critical' ? '🚨' : '⚠️'
            new Notification(`${icon} DRISHTI Alert`, {
              body: `Count: ${alert.count_value} (Threshold: ${alert.threshold_value}) — ${alert.alert_type.toUpperCase()}`,
              tag: `drishti-alert-${alert.id}`,
            })
          }
        } catch {}
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        eventSource?.close()
        // Reconnect after 5s
        setTimeout(connect, 5000)
      }
    }

    connect()

    // Request notification permission
    if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    return () => eventSource?.close()
  }, [maxItems])

  const handleAcknowledge = async (alertId: string) => {
    try {
      await fetch(`${API_URL}/api/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged_by: 'operator' }),
      })
      setAlerts(prev =>
        prev.map(a => a.id === alertId ? { ...a, acknowledged: true, acknowledged_by: 'operator' } : a)
      )
    } catch {}
  }

  const alertTypeStyles: Record<string, string> = {
    warning: 'alert-warning',
    critical: 'alert-critical',
    escalated: 'alert-escalated',
  }

  const alertTypeIcons: Record<string, string> = {
    warning: '⚠️',
    critical: '🚨',
    escalated: '🆘',
  }

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch {
      return ts
    }
  }

  return (
    <div className="glass p-4 flex flex-col h-full" id="alert-console">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
            Alert Console
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className={`status-dot ${isConnected ? 'live' : 'idle'}`} />
          <span className="text-xs text-[var(--drishti-text-dim)]">
            {alerts.length}
          </span>
        </div>
      </div>

      {/* Alerts list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-2 min-h-0">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mb-3">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-[var(--drishti-text-muted)]">All clear</p>
            <p className="text-xs text-[var(--drishti-text-dim)] mt-1">No alerts detected</p>
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div
              key={alert.id || i}
              className={`p-3 rounded-xl border text-sm animate-slide-in ${alertTypeStyles[alert.alert_type] || 'alert-warning'} ${alert.acknowledged ? 'opacity-50' : ''}`}
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-base flex-shrink-0">{alertTypeIcons[alert.alert_type] || '⚠️'}</span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-xs uppercase">{alert.alert_type}</span>
                      {alert.acknowledged && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">ACK</span>
                      )}
                    </div>
                    <p className="text-xs opacity-80 mt-0.5">
                      Count: <span className="font-mono font-medium">{alert.count_value}</span>
                      <span className="mx-1 opacity-40">|</span>
                      Threshold: {alert.threshold_value}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  <span className="text-[10px] opacity-60">{formatTime(alert.created_at)}</span>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-white/10 hover:bg-white/20 transition-colors cursor-pointer"
                    >
                      ACK
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
