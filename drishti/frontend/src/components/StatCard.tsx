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
    up: 'text-red-400',
    down: 'text-green-400',
    stable: 'text-[var(--drishti-text-dim)]',
  }

  const trendIcons: Record<string, string> = {
    up: '↑',
    down: '↓',
    stable: '→',
  }

  return (
    <div className="glass p-4 hover:scale-[1.02] transition-transform duration-300">
      <div className="flex items-start justify-between">
        <div className={`p-2 rounded-xl bg-gradient-to-br ${colorMap[color] || colorMap.indigo} bg-opacity-20`}
          style={{ background: `linear-gradient(135deg, ${color === 'indigo' ? 'rgba(99,102,241,0.15)' : color === 'cyan' ? 'rgba(6,182,212,0.15)' : color === 'green' ? 'rgba(34,197,94,0.15)' : color === 'red' ? 'rgba(239,68,68,0.15)' : color === 'yellow' ? 'rgba(234,179,8,0.15)' : 'rgba(168,85,247,0.15)'} 0%, transparent 100%)` }}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center gap-0.5 text-xs ${trendColors[trend]}`}>
            <span>{trendIcons[trend]}</span>
            {trendValue && <span>{trendValue}</span>}
          </div>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold tabular-nums text-[var(--drishti-text)]">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        <p className="text-xs text-[var(--drishti-text-muted)] mt-0.5">{label}</p>
      </div>
    </div>
  )
}
