'use client'

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  color?: string
}

export default function StatCard({ icon, label, value, trend, trendValue, color = 'indigo' }: StatCardProps) {
  const colorMap: Record<string, string> = {
    indigo: 'from-indigo-500 to-indigo-600',
    cyan: 'from-cyan-400 to-cyan-600',
    green: 'from-green-400 to-green-600',
    red: 'from-red-400 to-red-600',
    yellow: 'from-yellow-400 to-yellow-600',
    purple: 'from-purple-400 to-purple-600',
  }

  const trendColors: Record<string, string> = {
    up: 'text-rose-400',
    down: 'text-emerald-400',
    stable: 'text-[var(--drishti-text-dim)]',
  }

  const trendIcons: Record<string, string> = {
    up: '▲',
    down: '▼',
    stable: '■',
  }

  return (
    <div className="tech-card bg-[#0b0c13] hover:border-indigo-500/20 hover:shadow-[0_0_15px_rgba(99,102,241,0.05)] transition-all duration-300">
      <div className="flex items-start justify-between">
        <div className="p-1.5 rounded bg-white/[0.02] border border-white/5 text-[var(--drishti-text-muted)]">
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-1 font-mono text-[10px] ${trendColors[trend]}`}>
            <span>{trendIcons[trend]}</span>
            {trendValue && <span>{trendValue}</span>}
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-extrabold tracking-tight font-mono text-[var(--drishti-text)]">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        <p className="text-[10px] uppercase tracking-wider text-[var(--drishti-text-muted)] mt-1 font-semibold">{label}</p>
      </div>
    </div>
  )
}
