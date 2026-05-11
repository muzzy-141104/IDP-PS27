'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { API_URL } from '@/lib/supabase'

interface HeatmapViewerProps {
  /** Path returned by the backend, e.g. "static/density_map12345.jpg" */
  densityPath: string
  /** Path to the original uploaded image */
  originalPath?: string
  /** The crowd count associated with this heatmap */
  count?: number
  /** The model used */
  model?: string
  /** Compact mode — smaller card for embedding in the dashboard */
  compact?: boolean
}

export default function HeatmapViewer({
  densityPath,
  count,
  model,
  compact = false,
  originalPath,
}: HeatmapViewerProps) {
  const router = useRouter()
  const [isHovered, setIsHovered] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const imageUrl = densityPath.startsWith('http')
    ? densityPath
    : `${API_URL}/${densityPath}`

  const handleClick = () => {
    // Navigate to the heatmap page with the density path as query param
    const params = new URLSearchParams({
      src: densityPath,
      ...(originalPath && { original: originalPath }),
      ...(count !== undefined && { count: String(count) }),
      ...(model && { model }),
    })
    router.push(`/heatmap?${params.toString()}`)
  }

  if (imageError) {
    return (
      <div className={`glass flex items-center justify-center text-[var(--drishti-text-dim)] text-xs ${compact ? 'p-3' : 'p-6'}`}>
        <svg className="w-4 h-4 mr-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        Heatmap unavailable
      </div>
    )
  }

  return (
    <div
      className="group relative cursor-pointer"
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      id="heatmap-viewer"
    >
      {/* Animated glow border on hover */}
      <div
        className="absolute -inset-[1px] rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.4), rgba(6,182,212,0.4), rgba(34,197,94,0.4))',
          filter: 'blur(8px)',
        }}
      />

      {/* Card */}
      <div className={`relative glass overflow-hidden transition-all duration-300 ${
        isHovered ? 'shadow-lg shadow-indigo-500/10 scale-[1.01]' : ''
      } ${compact ? '' : 'p-1'}`}>

        {/* Header */}
        <div className={`flex items-center justify-between ${compact ? 'px-3 pt-3 pb-2' : 'px-4 pt-4 pb-3'}`}>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
              </svg>
            </div>
            <span className="text-[10px] uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
              Density Heatmap
            </span>
          </div>

          {/* Click hint */}
          <div className={`flex items-center gap-1 text-[10px] text-indigo-400 transition-all duration-300 ${
            isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
          }`}>
            <span>View Full</span>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </div>
        </div>

        {/* Heatmap image */}
        <div className={`relative overflow-hidden ${compact ? 'mx-3 mb-3 rounded-xl' : 'mx-4 mb-4 rounded-xl'}`}>
          {/* Loading skeleton */}
          {!imageLoaded && (
            <div className="absolute inset-0 bg-white/5 animate-pulse rounded-xl flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
            </div>
          )}

          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt="Crowd density heatmap"
            className={`w-full object-cover transition-all duration-500 ${
              compact ? 'h-36' : 'h-52'
            } ${imageLoaded ? 'opacity-100' : 'opacity-0'} ${
              isHovered ? 'scale-105 brightness-110' : 'scale-100 brightness-100'
            }`}
            style={{ borderRadius: 'inherit' }}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />

          {/* Gradient overlay at bottom */}
          <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />

          {/* Metadata badges on image */}
          <div className="absolute bottom-2 left-2 flex items-center gap-1.5">
            {count !== undefined && (
              <span className="px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] font-medium text-white">
                👥 {count} people
              </span>
            )}
            {model && (
              <span className="px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-sm border border-white/10 text-[10px] text-white/70">
                {model.toUpperCase()}
              </span>
            )}
          </div>

          {/* Expand icon on hover */}
          <div className={`absolute top-2 right-2 w-7 h-7 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 flex items-center justify-center transition-all duration-300 ${
            isHovered ? 'opacity-100 scale-100' : 'opacity-0 scale-75'
          }`}>
            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  )
}
