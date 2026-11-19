import { Search } from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Logo } from '@/components/Logo'
import { NotificationBell } from '@/components/NotificationBell'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useToast } from '@/components/toast'
import { cn } from '@/lib/cn'
import { SECTION_LINKS } from './nav'

function sectionClass({ isActive }: { isActive: boolean }): string {
  return cn(
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'text-fg' : 'text-fg-muted hover:text-fg',
  )
}

export function TopBar() {
  const { status, user, logout } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    toast({ title: 'Logged out', tone: 'success' })
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/85 backdrop-blur-md">
      <div className="flex h-16 w-full items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Logo />

        <nav
          className="hidden items-center gap-1 lg:flex"
          aria-label="Sections"
        >
          {SECTION_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className={sectionClass}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-1">
          <NavLink
            to="/search"
            aria-label="Search"
            className="flex h-10 w-10 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <Search size={18} aria-hidden="true" />
          </NavLink>
          <ThemeToggle />
          {status === 'authenticated' && <NotificationBell />}

          {status === 'authenticated' ? (
            <div className="hidden items-center gap-1 sm:flex">
              <NavLink to="/dashboard" className={sectionClass}>
                For you
              </NavLink>
              <NavLink to="/library" className={sectionClass}>
                Library
              </NavLink>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Log out
              </Button>
              <NavLink
                to="/settings"
                title="Settings"
                aria-label="Settings"
                className="ml-1 flex h-9 w-9 items-center justify-center overflow-hidden rounded-full bg-surface-3 text-sm font-semibold text-fg transition-shadow hover:ring-2 hover:ring-[var(--ring)]"
              >
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : (
                  (user?.display_name || user?.email || '?')
                    .charAt(0)
                    .toUpperCase()
                )}
              </NavLink>
            </div>
          ) : (
            status === 'anonymous' && (
              <Button
                size="sm"
                className="ml-1"
                onClick={() => navigate('/login')}
              >
                Log in
              </Button>
            )
          )}
        </div>
      </div>
    </header>
  )
}
