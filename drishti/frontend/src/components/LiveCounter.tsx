'use client'

import { useEffect, useState, useRef } from 'react'

interface LiveCounterProps {
  count: number
  trend?: 'up' | 'down' | 'stable'
  threshold: number
  model: string
}

export default function LiveCounter({ count, trend = 'stable', threshold, model }: LiveCounterProps) {
  const [displayCount, setDisplayCount] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)
  const prevCount = useRef(count)

  // Animate count changes
  useEffect(() => {
    if (count === prevCount.current) return
    setIsAnimating(true)

    const start = prevCount.current
    const end = count
    const duration = 600
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayCount(Math.round(start + (end - start) * eased))

      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setIsAnimating(false)
        prevCount.current = count
      }
    }

    requestAnimationFrame(animate)
  }, [count])

  const isOverThreshold = count > threshold
  const severity = count > threshold * 1.5 ? 'critical' : count > threshold ? 'warning' : 'normal'

  const severityColors = {
    normal: 'from-indigo-500 to-cyan-400',
    warning: 'from-yellow-400 to-orange-500',
    critical: 'from-red-500 to-rose-600',
  }

  const trendIcons = {
    up: '↑',
    down: '↓',
    stable: '→',
  }

  const trendColors = {
    up: 'text-red-400',
    down: 'text-green-400',
    stable: 'text-[var(--drishti-text-muted)]',
  }

  return (
    <div className={`glass p-6 relative overflow-hidden ${isOverThreshold ? 'animate-pulse-glow' : ''}`}
      id="live-counter">
      {/* Background glow effect */}
      <div className={`absolute inset-0 opacity-10 bg-gradient-to-br ${severityColors[severity]} rounded-2xl`} />

      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="status-dot live" />
            <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
              Live Count
            </span>
          </div>
          <span className="text-xs px-2 py-1 rounded-full bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)]">
            {model.toUpperCase()}
          </span>
        </div>

        {/* Count */}
        <div className="flex items-end gap-3 mb-3">
          <span
            className={`text-6xl font-bold tabular-nums bg-gradient-to-r ${severityColors[severity]} bg-clip-text text-transparent ${isAnimating ? 'animate-count-up' : ''}`}
          >
            {displayCount.toLocaleString()}
          </span>
          <span className={`text-2xl mb-1 ${trendColors[trend]} transition-colors`}>
            {trendIcons[trend]}
          </span>
        </div>

        {/* Threshold bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-[var(--drishti-text-muted)] mb-1.5">
            <span>Threshold: {threshold}</span>
            <span className={severity !== 'normal' ? 'text-red-400 font-medium' : ''}>
              {Math.round((count / threshold) * 100)}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${severityColors[severity]} transition-all duration-700 ease-out`}
              style={{ width: `${Math.min((count / threshold) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Alert badge */}
        {isOverThreshold && (
          <div className="mt-3 flex items-center gap-2 text-xs animate-slide-in">
            <span className={`px-2 py-0.5 rounded-full font-medium ${severity === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
              {severity === 'critical' ? '⚠ CRITICAL' : '⚠ WARNING'}
            </span>
            <span className="text-[var(--drishti-text-dim)]">
              Threshold exceeded
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
