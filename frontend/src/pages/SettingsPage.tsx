import { useQuery } from '@tanstack/react-query'
import { LogOut } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'

import { updateProfile } from '@/api/auth'
import { ApiError } from '@/api/errors'
import {
  fetchGenres,
  getGenrePreferences,
  getNotificationPreferences,
  getPlatformPreferences,
  saveGenrePreferences,
  savePlatformPreferences,
  updateNotificationPreferences,
} from '@/api/preferences'
import type {
  GenreContentType,
  GenrePreferenceItem,
  NotificationPreferences,
} from '@/api/preferences'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { ErrorState } from '@/components/ErrorState'
import { Input } from '@/components/Input'
import { SelectChip } from '@/components/SelectChip'
import { Skeleton } from '@/components/Skeleton'
import { Spinner } from '@/components/Spinner'
import { useToast } from '@/components/toast'
import { cn } from '@/lib/cn'
import { CONTENT_TYPES } from '@/lib/contentTypes'
import { PLATFORMS } from '@/lib/platforms'

const GENRE_TYPES: GenreContentType[] = ['movie', 'tv', 'anime', 'game']

/** Every genre, grouped by content type. Shared by the genre and muted-genre
 *  pickers; cached so both read one fetch. */
function useAllGenres() {
  return useQuery({
    queryKey: ['all-genres'],
    queryFn: async () => {
      const lists = await Promise.all(GENRE_TYPES.map((t) => fetchGenres(t)))
      return Object.fromEntries(
        GENRE_TYPES.map((t, i) => [t, lists[i]]),
      ) as Record<GenreContentType, string[]>
    },
    staleTime: 10 * 60_000,
  })
}

function Section({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: ReactNode
}) {
  return (
    <section className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
      <h2 className="text-lg font-semibold text-fg">{title}</h2>
      {description && (
        <p className="mt-1 text-sm text-fg-muted">{description}</p>
      )}
      <div className="mt-4">{children}</div>
    </section>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description?: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <span className="min-w-0">
        <span className="block text-sm font-medium text-fg">{label}</span>
        {description && (
          <span className="block text-xs text-fg-muted">{description}</span>
        )}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors',
          checked ? 'bg-brand' : 'bg-surface-3',
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform',
            checked ? 'translate-x-5' : 'translate-x-0.5',
          )}
          aria-hidden="true"
        />
      </button>
    </div>
  )
}

function toggleSet<T>(set: Set<T>, value: T): Set<T> {
  const next = new Set(set)
  if (next.has(value)) next.delete(value)
  else next.add(value)
  return next
}

function ProfileSection() {
  const { user, setUser } = useAuth()
  const { toast } = useToast()
  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? '')
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    try {
      const updated = await updateProfile({
        display_name: displayName,
        avatar_url: avatarUrl,
      })
      setUser(updated)
      toast({ title: 'Profile saved', tone: 'success' })
    } catch (err) {
      toast({
        title: 'Could not save your profile',
        description: err instanceof ApiError ? err.message : undefined,
        tone: 'error',
      })
    } finally {
      setSaving(false)
    }
  }

  const initial = (displayName || user?.email || '?').charAt(0).toUpperCase()

  return (
    <Section title="Profile" description="How you appear across EnVerse.">
      <div className="flex items-center gap-4">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt=""
            className="h-14 w-14 rounded-full bg-surface-2 object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        ) : (
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-3 text-xl font-semibold text-fg">
            {initial}
          </span>
        )}
        <div className="text-sm">
          <p className="font-medium text-fg">{user?.email}</p>
          <p className="text-fg-subtle">Email cannot be changed.</p>
        </div>
      </div>

      <div className="mt-4 space-y-4">
        <Input
          label="Display name"
          value={displayName}
          maxLength={100}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Your name"
        />
        <Input
          label="Avatar URL"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          placeholder="https://…"
          hint="Link to an image. Leave blank to use your initial."
        />
      </div>

      <div className="mt-4">
        <Button onClick={save} loading={saving}>
          Save profile
        </Button>
      </div>
    </Section>
  )
}

function GenresEditor({
  available,
  initial,
}: {
  available: Record<GenreContentType, string[]>
  initial: GenrePreferenceItem[]
}) {
  const { toast } = useToast()
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(initial.map((p) => `${p.content_type}::${p.genre}`)),
  )
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    try {
      const items: GenrePreferenceItem[] = [...selected].map((key) => {
        const [content_type, genre] = key.split('::')
        return { content_type: content_type as GenreContentType, genre: genre! }
      })
      await saveGenrePreferences(items)
      toast({ title: 'Genres saved', tone: 'success' })
    } catch (err) {
      toast({
        title: 'Could not save genres',
        description: err instanceof ApiError ? err.message : undefined,
        tone: 'error',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5">
      {GENRE_TYPES.map((type) => {
        const meta = CONTENT_TYPES[type]
        const Icon = meta.icon
        return (
          <div key={type}>
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-fg">
              <Icon
                size={15}
                style={{ color: meta.color }}
                aria-hidden="true"
              />
              {meta.plural}
            </h3>
            <div className="flex flex-wrap gap-2">
              {(available[type] ?? []).map((genre) => {
                const key = `${type}::${genre}`
                return (
                  <SelectChip
                    key={key}
                    label={genre}
                    selected={selected.has(key)}
                    onToggle={() => setSelected((s) => toggleSet(s, key))}
                  />
                )
              })}
            </div>
          </div>
        )
      })}
      <Button onClick={save} loading={saving}>
        Save genres
      </Button>
    </div>
  )
}

function GenresSection() {
  const genresQuery = useAllGenres()
  const savedQuery = useQuery({
    queryKey: ['genre-prefs'],
    queryFn: getGenrePreferences,
  })

  const ready = genresQuery.data && savedQuery.data
  const errored = genresQuery.isError || savedQuery.isError

  return (
    <Section
      title="Favourite genres"
      description="These tailor your dashboard and recommendations."
    >
      {errored ? (
        <ErrorState
          error={genresQuery.error ?? savedQuery.error}
          onRetry={() => {
            void genresQuery.refetch()
            void savedQuery.refetch()
          }}
        />
      ) : !ready ? (
        <div className="flex justify-center py-6">
          <Spinner label="Loading genres" />
        </div>
      ) : (
        <GenresEditor available={genresQuery.data} initial={savedQuery.data} />
      )}
    </Section>
  )
}

function PlatformsEditor({ initial }: { initial: string[] }) {
  const { toast } = useToast()
  const [selected, setSelected] = useState<Set<string>>(() => new Set(initial))
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    try {
      await savePlatformPreferences([...selected])
      toast({ title: 'Platforms saved', tone: 'success' })
    } catch (err) {
      toast({
        title: 'Could not save platforms',
        description: err instanceof ApiError ? err.message : undefined,
        tone: 'error',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map((platform) => (
          <SelectChip
            key={platform}
            label={platform}
            selected={selected.has(platform)}
            onToggle={() => setSelected((s) => toggleSet(s, platform))}
          />
        ))}
      </div>
      <Button onClick={save} loading={saving}>
        Save platforms
      </Button>
    </div>
  )
}

function PlatformsSection() {
  const savedQuery = useQuery({
    queryKey: ['platform-prefs'],
    queryFn: getPlatformPreferences,
  })

  return (
    <Section
      title="Your platforms"
      description="The streaming and game services you use."
    >
      {savedQuery.isLoading || !savedQuery.data ? (
        savedQuery.isError ? (
          <ErrorState
            error={savedQuery.error}
            onRetry={() => void savedQuery.refetch()}
          />
        ) : (
          <div className="flex justify-center py-6">
            <Spinner label="Loading platforms" />
          </div>
        )
      ) : (
        <PlatformsEditor initial={savedQuery.data} />
      )}
    </Section>
  )
}

function NotificationsEditor({
  initial,
  allGenres,
  genresLoading,
}: {
  initial: NotificationPreferences
  allGenres: string[]
  genresLoading: boolean
}) {
  const { toast } = useToast()
  const [prefs, setPrefs] = useState<NotificationPreferences>(initial)
  const [muted, setMuted] = useState<Set<string>>(
    () => new Set(initial.muted_genres),
  )
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    try {
      await updateNotificationPreferences({
        in_app_enabled: prefs.in_app_enabled,
        email_enabled: prefs.email_enabled,
        notify_releases: prefs.notify_releases,
        notify_schedules: prefs.notify_schedules,
        notify_updates: prefs.notify_updates,
        muted_genres: [...muted],
      })
      toast({ title: 'Notification settings saved', tone: 'success' })
    } catch (err) {
      toast({
        title: 'Could not save notifications',
        description: err instanceof ApiError ? err.message : undefined,
        tone: 'error',
      })
    } finally {
      setSaving(false)
    }
  }

  function set(key: keyof NotificationPreferences, value: boolean) {
    setPrefs((p) => ({ ...p, [key]: value }))
  }

  return (
    <div className="space-y-4">
      <div className="divide-y divide-border">
        <Toggle
          label="In-app notifications"
          description="The bell and the notifications page."
          checked={prefs.in_app_enabled}
          onChange={(v) => set('in_app_enabled', v)}
        />
        <Toggle
          label="Email notifications"
          description="A digest of what you follow."
          checked={prefs.email_enabled}
          onChange={(v) => set('email_enabled', v)}
        />
        <Toggle
          label="Releases"
          description="When something you follow comes out."
          checked={prefs.notify_releases}
          onChange={(v) => set('notify_releases', v)}
        />
        <Toggle
          label="Schedules"
          description="Upcoming episodes and fixtures."
          checked={prefs.notify_schedules}
          onChange={(v) => set('notify_schedules', v)}
        />
        <Toggle
          label="Updates"
          description="Changes to things you track."
          checked={prefs.notify_updates}
          onChange={(v) => set('notify_updates', v)}
        />
      </div>

      <div>
        <h3 className="mb-1 text-sm font-semibold text-fg">Muted genres</h3>
        <p className="mb-2 text-xs text-fg-muted">
          You will not be notified about titles in these genres.
        </p>
        {genresLoading ? (
          <Skeleton className="h-8 w-full" />
        ) : (
          <div className="flex flex-wrap gap-2">
            {allGenres.map((genre) => (
              <SelectChip
                key={genre}
                label={genre}
                selected={muted.has(genre)}
                onToggle={() => setMuted((s) => toggleSet(s, genre))}
              />
            ))}
          </div>
        )}
      </div>

      <Button onClick={save} loading={saving}>
        Save notifications
      </Button>
    </div>
  )
}

function NotificationsSection() {
  const prefsQuery = useQuery({
    queryKey: ['notification-prefs'],
    queryFn: getNotificationPreferences,
  })
  const genresQuery = useAllGenres()

  const allGenres = genresQuery.data
    ? [...new Set(Object.values(genresQuery.data).flat())].sort()
    : []

  return (
    <Section
      title="Notifications"
      description="Choose what you hear about and how."
    >
      {prefsQuery.isError ? (
        <ErrorState
          error={prefsQuery.error}
          onRetry={() => void prefsQuery.refetch()}
        />
      ) : prefsQuery.isLoading || !prefsQuery.data ? (
        <div className="flex justify-center py-6">
          <Spinner label="Loading notification settings" />
        </div>
      ) : (
        <NotificationsEditor
          initial={prefsQuery.data}
          allGenres={allGenres}
          genresLoading={genresQuery.isLoading}
        />
      )}
    </Section>
  )
}

export function SettingsPage() {
  const { logout } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
      toast({ title: 'Logged out', tone: 'success' })
      navigate('/')
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-fg">Settings</h1>

      <ProfileSection />
      <GenresSection />
      <PlatformsSection />
      <NotificationsSection />

      <Section
        title="Session"
        description="Sign out of EnVerse on this device."
      >
        <Button
          variant="outline"
          onClick={handleLogout}
          loading={loggingOut}
          leftIcon={<LogOut size={16} aria-hidden="true" />}
        >
          Log out
        </Button>
      </Section>
    </div>
  )
}
