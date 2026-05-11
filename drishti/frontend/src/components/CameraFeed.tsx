'use client'

import { useState } from 'react'
import { API_URL } from '@/lib/supabase'

interface CameraFeedProps {
  model: string
  source?: string
}

export default function CameraFeed({ model, source = './demo.avi' }: CameraFeedProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const streamUrl = `${API_URL}/stream/${model}?source=${encodeURIComponent(source)}`

  return (
    <div className="glass p-4 relative overflow-hidden" id="camera-feed">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
            Live Feed
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`status-dot ${hasError ? 'idle' : 'live'}`} />
          <span className="text-xs text-[var(--drishti-text-muted)]">
            {hasError ? 'Disconnected' : 'Streaming'}
          </span>
        </div>
      </div>

      {/* Video Feed */}
      <div className="relative aspect-video rounded-xl overflow-hidden bg-black/30">
        {isLoading && !hasError && (
          <div className="absolute inset-0 flex items-center justify-center bg-[var(--drishti-surface)]">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
              <span className="text-xs text-[var(--drishti-text-muted)]">Connecting to stream...</span>
            </div>
          </div>
        )}

        {hasError && (
          <div className="absolute inset-0 flex items-center justify-center bg-[var(--drishti-surface)]">
            <div className="flex flex-col items-center gap-3 text-center px-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <span className="text-sm text-[var(--drishti-text-muted)]">Stream unavailable</span>
              <span className="text-xs text-[var(--drishti-text-dim)]">Start the backend server to enable live feed</span>
            </div>
          </div>
        )}

        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={streamUrl}
          alt="Live camera feed"
          className={`w-full h-full object-contain ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-500`}
          onLoad={() => { setIsLoading(false); setHasError(false) }}
          onError={() => { setIsLoading(false); setHasError(true) }}
        />

        {/* Model badge overlay */}
        <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 text-xs font-medium text-white">
          {model.toUpperCase()}
        </div>

        {/* Recording indicator */}
        {!hasError && !isLoading && (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/20 backdrop-blur-sm border border-red-500/30">
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs font-medium text-red-400">REC</span>
          </div>
        )}
      </div>
    </div>
  )
}
