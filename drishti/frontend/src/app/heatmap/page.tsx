'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Suspense, useState, useRef, useEffect } from 'react'
import { API_URL } from '@/lib/supabase'

function HeatmapContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  const src = searchParams.get('src')
  const original = searchParams.get('original')
  const count = searchParams.get('count')
  const model = searchParams.get('model')

  const [zoom, setZoom] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [imageLoaded, setImageLoaded] = useState(false)
  const [originalLoaded, setOriginalLoaded] = useState(false)
  const [showOriginal, setShowOriginal] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const activePath = showOriginal ? (original || src) : src
  const imageUrl = activePath
    ? activePath.startsWith('http')
      ? activePath
      : `${API_URL}/${activePath}`
    : null

  // Determine severity based on count
  const countNum = count ? parseInt(count) : null
  const severity =
    countNum !== null
      ? countNum > 750
        ? 'critical'
        : countNum > 500
        ? 'warning'
        : 'normal'
      : null

  const severityConfig = {
    critical: {
      label: 'CRITICAL',
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      glow: 'shadow-red-500/20',
      gradient: 'from-red-500 to-rose-600',
      icon: '🚨',
    },
    warning: {
      label: 'WARNING',
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      glow: 'shadow-yellow-500/20',
      gradient: 'from-yellow-400 to-orange-500',
      icon: '⚠️',
    },
    normal: {
      label: 'SAFE',
      color: 'text-green-400',
      bg: 'bg-green-500/10',
      border: 'border-green-500/30',
      glow: 'shadow-green-500/20',
      gradient: 'from-green-400 to-emerald-500',
      icon: '✅',
    },
  }

  const config = severity ? severityConfig[severity] : null

  // Zoom controls
  const zoomIn = () => setZoom((z) => Math.min(z + 0.25, 4))
  const zoomOut = () => {
    setZoom((z) => {
      const next = Math.max(z - 0.25, 0.5)
      if (next <= 1) setPosition({ x: 0, y: 0 })
      return next
    })
  }
  const resetZoom = () => {
    setZoom(1)
    setPosition({ x: 0, y: 0 })
  }

  // Mouse wheel zoom
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault()
      if (e.deltaY < 0) {
        setZoom((z) => Math.min(z + 0.1, 4))
      } else {
        setZoom((z) => {
          const next = Math.max(z - 0.1, 0.5)
          if (next <= 1) setPosition({ x: 0, y: 0 })
          return next
        })
      }
    }

    container.addEventListener('wheel', handleWheel, { passive: false })
    return () => container.removeEventListener('wheel', handleWheel)
  }, [])

  // Drag to pan
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => setIsDragging(false)

  if (!imageUrl) {
    return (
      <div className="p-6 animate-fade-in">
        <div className="glass p-12 flex flex-col items-center justify-center gap-4" style={{ minHeight: 'calc(100vh - 120px)' }}>
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20 flex items-center justify-center">
            <svg className="w-9 h-9 text-orange-400/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-[var(--drishti-text)]">No Heatmap Available</h2>
          <p className="text-sm text-[var(--drishti-text-muted)] text-center max-w-md">
            Upload an image or video on the Dashboard and run analysis to generate a density heatmap.
          </p>
          <button
            onClick={() => router.push('/')}
            className="mt-2 px-5 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-sm text-indigo-400 hover:bg-indigo-500/20 transition-all cursor-pointer"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/')}
              className="w-8 h-8 rounded-lg bg-white/5 border border-[var(--drishti-border)] flex items-center justify-center hover:bg-white/10 transition-colors cursor-pointer"
            >
              <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-bold">
                <span className="gradient-text">Density</span>
                <span className="text-[var(--drishti-text-muted)] font-normal text-base ml-2">Heatmap Analysis</span>
              </h1>
              <p className="text-[10px] text-[var(--drishti-text-dim)] mt-0.5">
                Crowd density visualization • Click and drag to pan, scroll to zoom
              </p>
            </div>
          </div>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-white/5 border border-[var(--drishti-border)]">
            <button onClick={zoomOut} className="w-7 h-7 rounded-lg hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer text-[var(--drishti-text-muted)]">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.5 12h-15" />
              </svg>
            </button>
            <span className="text-xs font-mono text-[var(--drishti-text)] w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button onClick={zoomIn} className="w-7 h-7 rounded-lg hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer text-[var(--drishti-text-muted)]">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </button>
            <div className="w-px h-4 bg-[var(--drishti-border)] mx-1" />
            <button onClick={resetZoom} className="w-7 h-7 rounded-lg hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer text-[var(--drishti-text-muted)]" title="Reset zoom">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 180px)' }}>
        {/* Main heatmap view */}
        <div className="col-span-9">
          <div
            ref={containerRef}
            className="glass h-full overflow-hidden relative"
            style={{ cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Loading state */}
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/5">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-10 h-10 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                  <span className="text-xs text-[var(--drishti-text-dim)]">Loading heatmap...</span>
                </div>
              </div>
            )}

            {/* Heatmap image */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageUrl ?? undefined}
              alt={showOriginal ? "Original image" : "Crowd density heatmap"}
              className={`w-full h-full object-contain transition-opacity duration-500 select-none ${
                (showOriginal ? originalLoaded : imageLoaded) ? 'opacity-100' : 'opacity-0'
              }`}
              style={{
                transform: `scale(${zoom}) translate(${position.x / zoom}px, ${position.y / zoom}px)`,
                transition: isDragging ? 'none' : 'transform 0.3s ease-out',
              }}
              onLoad={() => {
                if (showOriginal) setOriginalLoaded(true)
                else setImageLoaded(true)
              }}
              draggable={false}
            />

            {/* Zoom level indicator */}
            {zoom !== 1 && (
              <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 text-xs font-mono text-white">
                {Math.round(zoom * 100)}%
              </div>
            )}

            {/* Color legend */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2">
              <div className="px-3 py-2 rounded-xl bg-black/50 backdrop-blur-sm border border-white/10">
                <p className="text-[9px] uppercase tracking-wider text-white/50 mb-1.5">Density Scale</p>
                <div className="flex items-center gap-1.5">
                  <div className="h-2 w-20 rounded-full" style={{
                    background: 'linear-gradient(90deg, #1e3a5f, #2563eb, #22d3ee, #facc15, #f97316, #ef4444)'
                  }} />
                  <div className="flex justify-between w-20">
                    <span className="text-[8px] text-white/40">Low</span>
                    <span className="text-[8px] text-white/40">High</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Side panel — Stats & Controls */}
        <div className="col-span-3 flex flex-col gap-4">
          {/* Analysis Result */}
          {config && countNum !== null && (
            <div className={`glass p-4 ${config.border} border animate-slide-in`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">Analysis Result</span>
                <span className="text-lg">{config.icon}</span>
              </div>

              <div className="mb-3">
                <p className="text-[10px] uppercase tracking-wider text-[var(--drishti-text-dim)]">People Detected</p>
                <p className={`text-3xl font-bold bg-gradient-to-r ${config.gradient} bg-clip-text text-transparent`}>
                  {countNum}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${config.bg} ${config.color} border ${config.border}`}>
                  {config.label}
                </span>
                {model && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)]">
                    {model.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* View Mode Toggle */}
          <div className="glass p-4">
            <span className="text-[10px] uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium block mb-3">View Mode</span>
            <div className="flex gap-2">
              <button
                onClick={() => setShowOriginal(false)}
                className={`flex-1 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  !showOriginal
                    ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                    : 'bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)] hover:bg-white/10'
                }`}
              >
                🔥 Heatmap
              </button>
              <button
                onClick={() => setShowOriginal(true)}
                className={`flex-1 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                  showOriginal
                    ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                    : 'bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)] hover:bg-white/10'
                }`}
                disabled={!original}
                title={!original ? "Original image not available" : "Show original image"}
              >
                🖼️ Original
              </button>
            </div>
          </div>

          {/* Quick Info */}
          <div className="glass p-4 flex-1">
            <span className="text-[10px] uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium block mb-3">Heatmap Info</span>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
                  </svg>
                </div>
                <div>
                  <p className="text-[10px] text-[var(--drishti-text-dim)]">Type</p>
                  <p className="text-xs text-[var(--drishti-text)]">Crowd Density Map</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                  </svg>
                </div>
                <div>
                  <p className="text-[10px] text-[var(--drishti-text-dim)]">Visualization</p>
                  <p className="text-xs text-[var(--drishti-text)]">Hot regions = higher crowd density</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                </div>
                <div>
                  <p className="text-[10px] text-[var(--drishti-text-dim)]">Controls</p>
                  <p className="text-xs text-[var(--drishti-text)]">Scroll to zoom, drag to pan</p>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/')}
              className="flex-1 px-4 py-2.5 rounded-xl bg-white/5 border border-[var(--drishti-border)] text-xs text-[var(--drishti-text-muted)] hover:bg-white/10 transition-all cursor-pointer"
            >
              ← Dashboard
            </button>
            <a
              href={imageUrl}
              download
              className="flex-1 px-4 py-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-xs text-indigo-400 hover:bg-indigo-500/20 transition-all text-center"
            >
              ↓ Download
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function HeatmapPage() {
  return (
    <Suspense fallback={
      <div className="p-6 flex items-center justify-center" style={{ minHeight: 'calc(100vh - 48px)' }}>
        <div className="w-10 h-10 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    }>
      <HeatmapContent />
    </Suspense>
  )
}
