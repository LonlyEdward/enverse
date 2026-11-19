import { NavLink } from 'react-router-dom'

import { cn } from '@/lib/cn'
import { BOTTOM_TABS } from './nav'

/** Fixed bottom navigation for mobile and tablet. Hidden from lg up, where the
 *  top bar's section nav takes over. */
export function BottomTabs() {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-bg/95 backdrop-blur-md lg:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <ul className="mx-auto flex max-w-xl">
        {BOTTOM_TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <li key={tab.to} className="flex-1">
              <NavLink
                to={tab.to}
                end={tab.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors',
                    isActive ? 'text-brand' : 'text-fg-subtle hover:text-fg',
                  )
                }
              >
                <Icon size={20} aria-hidden="true" />
                {tab.label}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
