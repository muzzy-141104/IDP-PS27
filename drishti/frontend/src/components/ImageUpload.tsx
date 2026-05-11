'use client'

import { useState, useRef } from 'react'
import { API_URL } from '@/lib/supabase'

interface ImageUploadProps {
  model: string
  onResult?: (result: { count: number; density_path?: string; alert?: unknown }) => void
}

export default function ImageUpload({ model, onResult }: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<{ count: number; density_path?: string } | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    // Show preview
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target?.result as string)
    reader.readAsDataURL(file)

    // Upload
    setIsProcessing(true)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('model', model)

    try {
      const res = await fetch(`${API_URL}/api/count`, { method: 'POST', body: formData })
      const data = await res.json()
      setResult(data)
      onResult?.(data)
    } catch {
      setResult({ count: -1 })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="glass p-4" id="image-upload">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M6.75 7.5h.008v.008H6.75V7.5z" />
        </svg>
        <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
          Image Analysis
        </span>
      </div>

      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
          isDragging ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-[var(--drishti-border)] hover:border-[var(--drishti-border-hover)]'
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
          }}
        />

        {preview ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img src={preview} alt="Preview" className="max-h-32 mx-auto rounded-lg mb-2" />
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--drishti-text-dim)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <p className="text-xs text-[var(--drishti-text-muted)]">Drop image or click to upload</p>
          </div>
        )}
      </div>

      {/* Processing */}
      {isProcessing && (
        <div className="mt-3 flex items-center gap-2 text-xs text-indigo-400">
          <div className="w-3 h-3 border border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
          Running inference with {model.toUpperCase()}...
        </div>
      )}

      {/* Result */}
      {result && !isProcessing && (
        <div className={`mt-3 p-3 rounded-xl ${result.count >= 0 ? 'bg-green-500/5 border border-green-500/10' : 'bg-red-500/5 border border-red-500/10'} animate-fade-in`}>
          {result.count >= 0 ? (
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--drishti-text-muted)]">Crowd Count:</span>
              <span className="text-lg font-bold gradient-text">{result.count}</span>
            </div>
          ) : (
            <p className="text-xs text-red-400">Inference failed. Is the backend running?</p>
          )}
        </div>
      )}
    </div>
  )
}
