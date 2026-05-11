'use client'

import { useState } from 'react'
import { API_URL } from '@/lib/supabase'

interface ThresholdSettingsProps {
  threshold: number
  onThresholdChange: (value: number) => void
}

export default function ThresholdSettings({ threshold, onThresholdChange }: ThresholdSettingsProps) {
  const [value, setValue] = useState(threshold)
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await fetch(`${API_URL}/api/settings/threshold`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ threshold: value }),
      })
      onThresholdChange(value)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // Silently handle — still update locally
      onThresholdChange(value)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="glass p-6" id="threshold-settings">
      <div className="flex items-center gap-2 mb-6">
        <svg className="w-5 h-5 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <h3 className="text-sm font-semibold text-[var(--drishti-text)]">Alert Threshold</h3>
      </div>

      {/* Large number display */}
      <div className="text-center mb-6">
        <span className="text-5xl font-bold tabular-nums gradient-text">{value}</span>
        <p className="text-xs text-[var(--drishti-text-dim)] mt-2">people before warning is triggered</p>
      </div>

      {/* Slider */}
      <div className="mb-6">
        <input
          type="range"
          min="50"
          max="2000"
          step="25"
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          className="w-full h-1.5 rounded-full appearance-none bg-white/10 accent-indigo-500 cursor-pointer"
          id="threshold-slider"
        />
        <div className="flex justify-between mt-2 text-[10px] text-[var(--drishti-text-dim)]">
          <span>50</span>
          <span>500</span>
          <span>1000</span>
          <span>1500</span>
          <span>2000</span>
        </div>
      </div>

      {/* Escalation levels */}
      <div className="space-y-2 mb-6">
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-yellow-500/5 border border-yellow-500/10">
          <div className="flex items-center gap-2">
            <span className="text-sm">⚠️</span>
            <span className="text-xs text-yellow-400">Warning</span>
          </div>
          <span className="text-xs font-mono text-yellow-400">&gt; {value}</span>
        </div>
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-500/5 border border-red-500/10">
          <div className="flex items-center gap-2">
            <span className="text-sm">🚨</span>
            <span className="text-xs text-red-400">Critical</span>
          </div>
          <span className="text-xs font-mono text-red-400">&gt; {Math.round(value * 1.5)}</span>
        </div>
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-orange-500/5 border border-orange-500/10">
          <div className="flex items-center gap-2">
            <span className="text-sm">🆘</span>
            <span className="text-xs text-orange-400">Escalated (SMS)</span>
          </div>
          <span className="text-xs font-mono text-orange-400">&gt; {Math.round(value * 1.5)}</span>
        </div>
      </div>

      {/* Number input + Save */}
      <div className="flex gap-2">
        <input
          type="number"
          value={value}
          onChange={(e) => setValue(Number(e.target.value))}
          min={50}
          max={10000}
          className="flex-1 px-3 py-2 rounded-xl bg-white/5 border border-[var(--drishti-border)] text-sm text-[var(--drishti-text)] focus:outline-none focus:border-indigo-500/40 transition-colors"
          id="threshold-input"
        />
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
            saved
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30'
          }`}
          id="threshold-save-btn"
        >
          {isSaving ? '...' : saved ? '✓ Saved' : 'Save'}
        </button>
      </div>
    </div>
  )
}
