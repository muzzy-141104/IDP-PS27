'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    name: 'Alerts',
    href: '/alerts',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
  },
  {
    name: 'Heatmap',
    href: '/heatmap',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
      </svg>
    ),
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-screen w-[68px] bg-[#08090f] border-r border-[var(--drishti-border)] flex flex-col items-center py-6 z-50">
      {/* Logo */}
      <div className="mb-8 relative flex items-center justify-center">
        <div className="w-9 h-9 rounded bg-gradient-to-br from-indigo-600 to-cyan-500 flex items-center justify-center text-white font-extrabold text-sm tracking-wider border border-white/10 shadow-[0_0_15px_rgba(79,70,229,0.25)]">
          DR
        </div>
        <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 border border-[#08090f]" />
      </div>

      {/* Navigation */}
      <nav className="flex flex-col items-center gap-3 flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              id={`nav-${item.name.toLowerCase()}`}
              className={`
                relative w-10 h-10 rounded flex items-center justify-center
                transition-all duration-200 group border
                ${isActive
                  ? 'bg-indigo-600/10 text-indigo-400 border-indigo-500/30 shadow-[inset_0_0_8px_rgba(99,102,241,0.05)]'
                  : 'text-[var(--drishti-text-muted)] border-transparent hover:text-[var(--drishti-text)] hover:bg-white/[0.02]'
                }
              `}
              title={item.name}
            >
              {item.icon}
              {isActive && (
                <div className="absolute left-0 w-0.5 h-4 bg-indigo-500" />
              )}
              {/* Tooltip */}
              <span className="absolute left-full ml-3 px-2.5 py-1 rounded bg-[#0c0d14] text-[10px] uppercase tracking-wider font-bold text-[var(--drishti-text)] opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none whitespace-nowrap border border-[var(--drishti-border)] shadow-xl z-[99]">
                {item.name}
              </span>
            </Link>
          )
        })}
      </nav>

      {/* Status indicator */}
      <div className="mt-auto flex flex-col items-center">
        <div className="w-8 h-8 rounded border border-[var(--drishti-border)] bg-white/[0.01] flex items-center justify-center" title="System Online">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </div>
    </aside>
  )
}
