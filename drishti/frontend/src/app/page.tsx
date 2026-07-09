'use client'

import { useState, useEffect } from 'react'
import LiveCounter from '@/components/LiveCounter'
import MediaUpload from '@/components/MediaUpload'
import AlertConsole from '@/components/AlertConsole'
import ModelSelector from '@/components/ModelSelector'
import StatCard from '@/components/StatCard'
import CameraFeed from '@/components/CameraFeed'
import { API_URL, type CountEvent } from '@/lib/supabase'

export default function DashboardPage() {
  const [model, setModel] = useState('yolo')
  const [mode, setMode] = useState<'upload' | 'stream'>('upload')
  const [streamUrl, setStreamUrl] = useState('http://192.168.137.253:5000/video_feed')
  const [count, setCount] = useState(0)
  const [threshold, setThreshold] = useState(500)
  const [trend, setTrend] = useState<'up' | 'down' | 'stable'>('stable')
  const [totalToday, setTotalToday] = useState(0)
  const [maxToday, setMaxToday] = useState(0)
  const [alertCount, setAlertCount] = useState(0)
  const prevCount = { current: 0 }

  // SSE for real-time counts
  useEffect(() => {
    let eventSource: EventSource | null = null

    const connect = () => {
      eventSource = new EventSource(`${API_URL}/ws/count`)

      eventSource.onmessage = (event) => {
        try {
          const data: CountEvent = JSON.parse(event.data)
          const newCount = data.count ?? 0

          if (newCount > prevCount.current) setTrend('up')
          else if (newCount < prevCount.current) setTrend('down')
          else setTrend('stable')

          prevCount.current = newCount
          setCount(newCount)
          setThreshold(data.threshold ?? 500)

          if ((data as any).source_type !== 'stream') {
            setTotalToday(prev => prev + 1)
          }
          setMaxToday(prev => Math.max(prev, newCount))
          if (data.alert_type) setAlertCount(prev => prev + 1)
        } catch {}
      }

      eventSource.onerror = () => {
        eventSource?.close()
        setTimeout(connect, 5000)
      }
    }

    connect()
    return () => eventSource?.close()
  }, [])

  const handleResult = (r: { count: number; density_path?: string; alert?: unknown }) => {
    if (r.count >= 0) {
      const prev = count
      setCount(r.count)
      setTotalToday(p => p + 1)
      setMaxToday(p => Math.max(p, r.count))
      if (r.count > prev) setTrend('up')
      else if (r.count < prev) setTrend('down')
      else setTrend('stable')
      if (r.alert) setAlertCount(p => p + 1)
    }
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">
          <span className="gradient-text">DRISHTI</span>
          <span className="text-[var(--drishti-text-muted)] font-normal text-lg ml-3">Dashboard</span>
        </h1>
        <p className="text-xs text-[var(--drishti-text-dim)] mt-1">
          Density Recognition and Intelligent Surveillance for Hazard Threshold Identification
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={<svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>}
          label="Current Count"
          value={count}
          trend={trend}
          color="indigo"
        />
        <StatCard
          icon={<svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>}
          label="Scans Today"
          value={totalToday}
          color="cyan"
        />
        <StatCard
          icon={<svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" /></svg>}
          label="Peak Count"
          value={maxToday}
          color="purple"
        />
        <StatCard
          icon={<svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>}
          label="Alerts Today"
          value={alertCount}
          trend={alertCount > 0 ? 'up' : 'stable'}
          color="red"
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-12 gap-4" style={{ minHeight: 'calc(100vh - 280px)' }}>
        {/* Left column — Counter + Model */}
        <div className="col-span-3 space-y-4">
          <LiveCounter count={count} trend={trend} threshold={threshold} model={model} />
          <ModelSelector selected={model} onChange={setModel} />
        </div>

        {/* Center — Media Upload & Analysis */}
        <div className="col-span-6 flex flex-col gap-4">
          <div className="glass p-4 flex items-center justify-between flex-shrink-0">
            <span className="text-[10px] uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
              Source Mode
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setMode('upload')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  mode === 'upload' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'bg-white/5 text-[var(--drishti-text-muted)] border border-transparent hover:bg-white/10'
                }`}
              >
                Upload Media
              </button>
              <button
                onClick={() => setMode('stream')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  mode === 'stream' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'bg-white/5 text-[var(--drishti-text-muted)] border border-transparent hover:bg-white/10'
                }`}
              >
                Live Stream
              </button>
            </div>
          </div>

          {mode === 'stream' ? (
            <div className="glass p-4 flex flex-col gap-4 flex-1 min-h-0">
              <div className="flex-shrink-0">
                <label className="text-xs text-[var(--drishti-text-muted)] mb-1 block">Stream URL</label>
                <input 
                  type="text" 
                  value={streamUrl}
                  onChange={(e) => setStreamUrl(e.target.value)}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500/50 transition-colors"
                  placeholder="e.g., http://192.168.1.100:5000/video_feed"
                />
              </div>
              <div className="flex-1 min-h-0 relative">
                 <CameraFeed model={model} source={streamUrl} />
              </div>
            </div>
          ) : (
            <div className="flex-1 min-h-0">
              <MediaUpload model={model} threshold={threshold} onResult={handleResult} />
            </div>
          )}
        </div>

        {/* Right — Alert console */}
        <div className="col-span-3">
          <AlertConsole />
        </div>
      </div>
    </div>
  )
}
