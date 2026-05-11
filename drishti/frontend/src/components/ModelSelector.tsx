'use client'

interface ModelSelectorProps {
  selected: string
  onChange: (model: string) => void
}

const models = [
  {
    id: 'yolo',
    name: 'YOLO-CROWD',
    description: 'Detection-based counting',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    ),
    color: 'from-cyan-400 to-blue-500',
    badge: 'Fast',
  },
  {
    id: 'csrnet',
    name: 'CSRNet',
    description: 'Density map estimation',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
      </svg>
    ),
    color: 'from-purple-400 to-pink-500',
    badge: 'Dense',
  },
]

export default function ModelSelector({ selected, onChange }: ModelSelectorProps) {
  return (
    <div className="glass p-4" id="model-selector">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-[var(--drishti-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
        <span className="text-xs uppercase tracking-widest text-[var(--drishti-text-muted)] font-medium">
          Model
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {models.map((model) => {
          const isSelected = selected === model.id
          return (
            <button
              key={model.id}
              onClick={() => onChange(model.id)}
              id={`model-${model.id}`}
              className={`
                relative p-3 rounded-xl border transition-all duration-300 text-left cursor-pointer
                ${isSelected
                  ? 'border-indigo-500/40 bg-indigo-500/10 shadow-lg shadow-indigo-500/5'
                  : 'border-[var(--drishti-border)] bg-transparent hover:border-[var(--drishti-border-hover)] hover:bg-white/[0.02]'
                }
              `}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <div className={`p-1.5 rounded-lg ${isSelected ? `bg-gradient-to-br ${model.color} text-white` : 'bg-white/5 text-[var(--drishti-text-muted)]'} transition-all`}>
                  {model.icon}
                </div>
                {isSelected && (
                  <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-indigo-400" />
                )}
              </div>
              <h3 className={`text-sm font-semibold ${isSelected ? 'text-[var(--drishti-text)]' : 'text-[var(--drishti-text-muted)]'}`}>
                {model.name}
              </h3>
              <p className="text-[10px] text-[var(--drishti-text-dim)] mt-0.5">{model.description}</p>
              <span className={`inline-block mt-1.5 text-[10px] px-1.5 py-0.5 rounded-full ${isSelected ? 'bg-indigo-500/20 text-indigo-300' : 'bg-white/5 text-[var(--drishti-text-dim)]'}`}>
                {model.badge}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
