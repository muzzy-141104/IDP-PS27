'use client'

import { useState, useEffect } from 'react'
import { API_URL, type Alert } from '@/lib/supabase'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/alerts?limit=200`)
      const data = await res.json()
      if (Array.isArray(data)) setAlerts(data)
    } catch {}
    setIsLoading(false)
  }

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

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'all') return true
    if (filter === 'active') return !a.acknowledged
    return a.alert_type === filter
  })

  const alertBadge = (type: string) => {
    const styles: Record<string, string> = {
      warning: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
      critical: 'bg-red-500/15 text-red-400 border-red-500/20',
      escalated: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
    }
    return styles[type] || styles.warning
  }

  const formatDate = (ts: string) => {
    try {
      return new Date(ts).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
      })
    } catch { return ts }
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          <span className="gradient-text">Alert History</span>
        </h1>
        <p className="text-xs text-[var(--drishti-text-dim)] mt-1">
          Review and manage threshold breach events
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-6">
        {['all', 'active', 'warning', 'critical', 'escalated'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              filter === f
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                : 'bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)] hover:bg-white/10'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <div className="ml-auto text-xs text-[var(--drishti-text-dim)]">
          {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Table */}
      <div className="glass overflow-hidden">
        {isLoading ? (
          <div className="p-12 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-[var(--drishti-text-muted)]">No alerts found</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--drishti-border)]">
                <th className="text-left px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Type</th>
                <th className="text-left px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Count</th>
                <th className="text-left px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Threshold</th>
                <th className="text-left px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Time</th>
                <th className="text-right px-4 py-3 text-xs text-[var(--drishti-text-dim)] uppercase tracking-wider font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert, i) => (
                <tr key={alert.id || i} className="border-b border-[var(--drishti-border)] hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${alertBadge(alert.alert_type)}`}>
                      {alert.alert_type === 'critical' ? '🚨' : alert.alert_type === 'escalated' ? '🆘' : '⚠️'}
                      {alert.alert_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-medium text-[var(--drishti-text)]">{alert.count_value}</td>
                  <td className="px-4 py-3 text-[var(--drishti-text-muted)]">{alert.threshold_value}</td>
                  <td className="px-4 py-3">
                    {alert.acknowledged ? (
                      <span className="text-xs text-green-400 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                        Acknowledged
                      </span>
                    ) : (
                      <span className="text-xs text-yellow-400 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                        Active
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--drishti-text-muted)]">{formatDate(alert.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 transition-colors cursor-pointer"
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
