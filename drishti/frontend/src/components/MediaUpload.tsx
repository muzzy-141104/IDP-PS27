'use client'

import { useState, useRef } from 'react'
import { API_URL } from '@/lib/supabase'
import HeatmapViewer from './HeatmapViewer'

interface MediaUploadProps {
  model: string
  threshold: number
  onResult?: (result: { count: number; density_path?: string; original_path?: string; alert?: unknown }) => void
}

const MAX_FILE_SIZE_MB = 200

type ProcessingStep = 'uploading' | 'extracting' | 'analyzing' | null

export default function MediaUpload({ model, threshold, onResult }: MediaUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [step, setStep] = useState<ProcessingStep>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [result, setResult] = useState<{ count: number; density_path?: string; original_path?: string } | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [fileSize, setFileSize] = useState<string | null>(null)
  const [fileType, setFileType] = useState<'image' | 'video' | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const xhrRef = useRef<XMLHttpRequest | null>(null)

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleFile = async (file: File) => {
    // Size check
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File too large (${formatSize(file.size)}). Max ${MAX_FILE_SIZE_MB}MB.`)
      return
    }

    setFileName(file.name)
    setFileSize(formatSize(file.size))
    setResult(null)
    setErrorMsg(null)

    const isVideo = file.type.startsWith('video/')
    setFileType(isVideo ? 'video' : 'image')

    // Show preview
    const url = URL.createObjectURL(file)
    setPreview(url)

    // Upload with progress via XHR
    setIsProcessing(true)
    setStep('uploading')
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('model', model)

    try {
      const data = await new Promise<{ count: number; density_path?: string; original_path?: string; alert?: unknown }>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhrRef.current = xhr

        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100)
            setUploadProgress(pct)
            if (pct >= 100) {
              setStep(isVideo ? 'extracting' : 'analyzing')
            }
          }
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              resolve(JSON.parse(xhr.responseText))
            } catch {
              reject(new Error('Invalid JSON response'))
            }
          } else {
            reject(new Error(`Server error: ${xhr.status}`))
          }
        }

        xhr.onerror = () => reject(new Error('Network error'))
        xhr.ontimeout = () => reject(new Error('Request timed out'))
        xhr.timeout = 120_000  // 2 min timeout

        xhr.open('POST', `${API_URL}/api/count`)
        xhr.send(formData)

        // After upload completes, switch to analyzing step
        xhr.upload.onloadend = () => {
          setStep('analyzing')
        }
      })

      setResult(data)
      onResult?.(data)
    } catch (err) {
      setResult({ count: -1 })
      setErrorMsg(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsProcessing(false)
      setStep(null)
      setUploadProgress(0)
      xhrRef.current = null
    }
  }

  const handleCancel = () => {
    xhrRef.current?.abort()
    setIsProcessing(false)
    setStep(null)
    setUploadProgress(0)
  }

  const handleReset = () => {
    handleCancel()
    setPreview(null)
    setFileName(null)
    setFileSize(null)
    setFileType(null)
    setResult(null)
    setErrorMsg(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const severity = result && result.count >= 0
    ? result.count > threshold * 1.5 ? 'critical' : result.count > threshold ? 'warning' : 'normal'
    : null

  const severityColors: Record<string, string> = {
    normal: 'from-green-400 to-emerald-500',
    warning: 'from-yellow-400 to-orange-500',
    critical: 'from-red-500 to-rose-600',
  }

  return (
    <div className="tech-card bg-[#0b0c13] h-full flex flex-col" id="media-upload">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
            Analyze Media
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)]">
            {model.toUpperCase()}
          </span>
          {preview && (
            <button onClick={handleReset} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-[var(--drishti-text-muted)] border border-[var(--drishti-border)] hover:bg-white/10 transition-colors cursor-pointer">
              ✕ Clear
            </button>
          )}
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 min-h-0">
        {!preview ? (
          /* Drop zone */
          <div
            className={`h-full border-2 border-dashed rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer ${
              isDragging
                ? 'border-indigo-500/50 bg-indigo-500/5'
                : 'border-[var(--drishti-border)] hover:border-[var(--drishti-border-hover)] hover:bg-white/[0.01]'
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
              accept="image/*,video/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleFile(file)
              }}
            />

            <div className="flex flex-col items-center gap-4 p-8">
              {/* Icon */}
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-cyan-500/10 border border-indigo-500/20 flex items-center justify-center">
                <svg className="w-7 h-7 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.338-2.32 3 3 0 013.438 3.42A3.75 3.75 0 0118 19.5H6.75z" />
                </svg>
              </div>

              {/* Text */}
              <div className="text-center">
                <p className="text-sm font-medium text-[var(--drishti-text)]">
                  Drop an image or video here
                </p>
                <p className="text-xs text-[var(--drishti-text-dim)] mt-1">
                  or click to browse • JPG, PNG, MP4, AVI
                </p>
              </div>

              {/* Format badges */}
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-md bg-white/5 text-[10px] text-[var(--drishti-text-dim)] border border-[var(--drishti-border)]">
                  🖼️ Images
                </span>
                <span className="px-2 py-0.5 rounded-md bg-white/5 text-[10px] text-[var(--drishti-text-dim)] border border-[var(--drishti-border)]">
                  🎬 Videos
                </span>
              </div>
            </div>
          </div>
        ) : (
          /* Preview + Result */
          <div className="h-full flex flex-col gap-3">
            {/* Media preview */}
            <div className="relative flex-1 min-h-0 rounded-xl overflow-hidden bg-black/30">
              {isProcessing && step === 'analyzing' && <div className="scan-line" />}
              {fileType === 'video' ? (
                <video
                  ref={videoRef}
                  src={preview}
                  className="w-full h-full object-contain"
                  controls
                  muted
                  autoPlay={false}
                />
              ) : (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={preview}
                  alt="Uploaded media"
                  className="w-full h-full object-contain"
                />
              )}

              {/* File info overlay */}
              <div className="absolute top-3 left-3 flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 text-xs font-medium text-white">
                  {fileType === 'video' ? '🎬' : '🖼️'} {fileName}
                </span>
                {fileSize && (
                  <span className="px-2 py-1 rounded-lg bg-black/50 backdrop-blur-sm border border-white/10 text-[10px] text-white/60">
                    {fileSize}
                  </span>
                )}
              </div>

              {/* Processing overlay with progress */}
              {isProcessing && (
                <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center">
                  <div className="flex flex-col items-center gap-4 w-64">
                    {/* Steps */}
                    <div className="w-full space-y-2.5">
                      {/* Step 1: Upload */}
                      <div className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          step === 'uploading' ? 'bg-indigo-500/30 border border-indigo-500' : 'bg-green-500/20 border border-green-500/50'
                        }`}>
                          {step === 'uploading' ? (
                            <div className="w-3 h-3 border border-indigo-300/30 border-t-indigo-300 rounded-full animate-spin" />
                          ) : (
                            <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-medium ${step === 'uploading' ? 'text-white' : 'text-white/50'}`}>
                              Uploading
                            </span>
                            {step === 'uploading' && (
                              <span className="text-xs font-mono text-indigo-300">{uploadProgress}%</span>
                            )}
                          </div>
                          {step === 'uploading' && (
                            <div className="h-1 rounded-full bg-white/10 mt-1.5 overflow-hidden">
                              <div className="h-full rounded-full bg-indigo-500 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Step 2: Extract (video only) */}
                      {fileType === 'video' && (
                        <div className="flex items-center gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                            step === 'extracting' ? 'bg-indigo-500/30 border border-indigo-500'
                            : step === 'analyzing' ? 'bg-green-500/20 border border-green-500/50'
                            : 'bg-white/5 border border-white/10'
                          }`}>
                            {step === 'extracting' ? (
                              <div className="w-3 h-3 border border-indigo-300/30 border-t-indigo-300 rounded-full animate-spin" />
                            ) : step === 'analyzing' ? (
                              <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                            ) : (
                              <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                            )}
                          </div>
                          <span className={`text-xs font-medium ${step === 'extracting' ? 'text-white' : step === 'analyzing' ? 'text-white/50' : 'text-white/20'}`}>
                            Extracting frame
                          </span>
                        </div>
                      )}

                      {/* Step 3: Analyze */}
                      <div className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                          step === 'analyzing' ? 'bg-indigo-500/30 border border-indigo-500' : 'bg-white/5 border border-white/10'
                        }`}>
                          {step === 'analyzing' ? (
                            <div className="w-3 h-3 border border-indigo-300/30 border-t-indigo-300 rounded-full animate-spin" />
                          ) : (
                            <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                          )}
                        </div>
                        <span className={`text-xs font-medium ${step === 'analyzing' ? 'text-white' : 'text-white/20'}`}>
                          Running {model.toUpperCase()} inference
                        </span>
                      </div>
                    </div>

                    {/* Cancel button */}
                    <button
                      onClick={handleCancel}
                      className="text-xs px-3 py-1 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Result badge overlay */}
              {result && result.count >= 0 && !isProcessing && (
                <div className="absolute bottom-3 right-3 animate-slide-in">
                  <div className={`px-4 py-2 rounded-xl bg-black/60 backdrop-blur-md border ${
                    severity === 'critical' ? 'border-red-500/40' : severity === 'warning' ? 'border-yellow-500/40' : 'border-green-500/40'
                  }`}>
                    <div className="flex items-center gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-white/60">People Detected</p>
                        <p className={`text-2xl font-bold bg-gradient-to-r ${severityColors[severity!]} bg-clip-text text-transparent`}>
                          {result.count}
                        </p>
                      </div>
                      {severity !== 'normal' && (
                        <span className={`text-lg ${severity === 'critical' ? 'animate-pulse' : ''}`}>
                          {severity === 'critical' ? '🚨' : '⚠️'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Result details bar */}
            {result && result.count >= 0 && !isProcessing && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-stretch gap-3">
                  {/* Left stats column */}
                  <div className="flex-1 grid grid-cols-2 gap-2">
                    {/* Count card */}
                    <div className="col-span-2 p-3 rounded-xl bg-white/[0.03] border border-[var(--drishti-border)] flex items-center justify-between">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-[var(--drishti-text-dim)]">Crowd Count</p>
                        <p className="text-2xl font-bold gradient-text">{result.count}</p>
                      </div>
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        severity === 'critical' ? 'bg-red-500/10' : severity === 'warning' ? 'bg-yellow-500/10' : 'bg-green-500/10'
                      }`}>
                        <span className="text-xl">
                          {severity === 'critical' ? '🚨' : severity === 'warning' ? '⚠️' : '✅'}
                        </span>
                      </div>
                    </div>

                    {/* Model card */}
                    <div className="p-2.5 rounded-xl bg-white/[0.03] border border-[var(--drishti-border)]">
                      <p className="text-[10px] uppercase tracking-wider text-[var(--drishti-text-dim)]">Model</p>
                      <p className="text-xs font-semibold text-[var(--drishti-text)] mt-0.5">{model.toUpperCase()}</p>
                    </div>

                    {/* Status card */}
                    <div className="p-2.5 rounded-xl bg-white/[0.03] border border-[var(--drishti-border)]">
                      <p className="text-[10px] uppercase tracking-wider text-[var(--drishti-text-dim)]">Status</p>
                      <p className={`text-xs font-semibold mt-0.5 ${
                        severity === 'critical' ? 'text-red-400' : severity === 'warning' ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {severity === 'critical' ? 'CRITICAL' : severity === 'warning' ? 'WARNING' : 'SAFE'}
                      </p>
                    </div>

                    {/* New Upload button */}
                    <button
                      onClick={handleReset}
                      className="col-span-2 p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-all cursor-pointer flex items-center justify-center gap-2"
                    >
                      <span className="text-xs font-bold text-indigo-400">ANALYZE ANOTHER</span>
                      <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>

                  {/* Right heatmap column */}
                  {result.density_path && (
                    <div className="w-56 flex-shrink-0">
                      <HeatmapViewer 
                        densityPath={result.density_path} 
                        originalPath={result.original_path}
                        count={result.count} 
                        model={model} 
                        compact={true} 
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Error state */}
            {result && result.count < 0 && !isProcessing && (
              <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15 animate-fade-in">
                <div className="flex items-center gap-2">
                  <span className="text-red-400">⚠</span>
                  <div>
                    <p className="text-xs font-medium text-red-400">Analysis failed</p>
                    <p className="text-[10px] text-red-400/60 mt-0.5">
                      {errorMsg || `Check if the backend server is running at ${API_URL}`}
                    </p>
                  </div>
                  <button onClick={handleReset} className="ml-auto text-xs px-2 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 cursor-pointer transition-colors">
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* Size error (no upload attempted) */}
            {errorMsg && !result && !isProcessing && (
              <div className="p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/15 animate-fade-in mt-2">
                <div className="flex items-center gap-2">
                  <span className="text-yellow-400">⚠</span>
                  <p className="text-xs text-yellow-400">{errorMsg}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
