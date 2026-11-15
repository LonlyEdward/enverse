import { useQuery } from '@tanstack/react-query'
import { Bell, Bookmark, Clock, Heart } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/errors'
import {
  addToList,
  getLibraryStatus,
  removeFromList,
  STATUS_KEY,
} from '@/api/library'
import type { LibraryStatus, ListKind } from '@/api/library'
import { useAuth } from '@/auth/AuthContext'
import { cn } from '@/lib/cn'
import { Spinner } from './Spinner'
import { useToast } from './toast'

const DEFAULT_STATUS: LibraryStatus = {
  favorite: false,
  watchlist: false,
  bookmark: false,
  following: false,
  notifications_enabled: null,
}

/** Per-item library state with optimistic toggles and rollback. */
function useItemLibrary(
  contentType: string,
  objectId: number,
  enabled: boolean,
) {
  const query = useQuery({
    queryKey: ['lib-status', contentType, objectId],
    queryFn: () => getLibraryStatus(contentType, objectId),
    enabled,
  })
  const [overrides, setOverrides] = useState<Partial<LibraryStatus>>({})
  const [rowIds, setRowIds] = useState<Partial<Record<ListKind, number>>>({})

  const status: LibraryStatus = {
    ...DEFAULT_STATUS,
    ...query.data,
    ...overrides,
  }

  async function toggle(kind: ListKind) {
    const key = STATUS_KEY[kind]
    const currently = Boolean(status[key])
    setOverrides((o) => ({ ...o, [key]: !currently }))
    try {
      if (!currently) {
        const row = await addToList(kind, contentType, objectId)
        setRowIds((r) => ({ ...r, [kind]: row.id }))
      } else {
        // The status endpoint does not return row ids, so when we don't already
        // know it (saved in a past session) a POST gets it back idempotently.
        let id = rowIds[kind]
        if (id == null) id = (await addToList(kind, contentType, objectId)).id
        await removeFromList(kind, id)
        setRowIds((r) => ({ ...r, [kind]: undefined }))
      }
    } catch (err) {
      setOverrides((o) => ({ ...o, [key]: currently })) // rollback
      throw err
    }
  }

  return { status, toggle, loading: enabled && query.isLoading }
}

function ActionButton({
  icon: Icon,
  label,
  active,
  activeColor,
  onClick,
}: {
  icon: LucideIcon
  label: string
  active: boolean
  activeColor: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-medium transition-colors',
        active
          ? 'border-transparent text-white'
          : 'border-border bg-surface text-fg-muted hover:border-border-strong hover:text-fg',
      )}
      style={active ? { backgroundColor: activeColor } : undefined}
    >
      <Icon
        size={16}
        aria-hidden="true"
        fill={active ? 'currentColor' : 'none'}
      />
      {label}
    </button>
  )
}

interface ActionBarProps {
  contentType: string
  objectId: number
  /** Watchlist is rejected for football teams, so hide it there. */
  showWatchlist?: boolean
}

export function ActionBar({
  contentType,
  objectId,
  showWatchlist = true,
}: ActionBarProps) {
  const { status: authStatus, isVerified } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const enabled = authStatus === 'authenticated' && isVerified
  const { status, toggle, loading } = useItemLibrary(
    contentType,
    objectId,
    enabled,
  )

  function guarded(kind: ListKind) {
    return () => {
      if (authStatus !== 'authenticated') {
        navigate('/login', { state: { next: location.pathname } })
        return
      }
      if (!isVerified) {
        toast({
          title: 'Verify your email to save items',
          description: 'Check your inbox, or resend the link from the banner.',
          tone: 'info',
        })
        return
      }
      toggle(kind).catch((err) =>
        toast({
          title: 'That did not work',
          description: err instanceof ApiError ? err.message : undefined,
          tone: 'error',
        }),
      )
    }
  }

  if (loading) {
    return (
      <div className="flex h-10 items-center">
        <Spinner label="Loading your saved state" size={18} />
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-2">
      <ActionButton
        icon={Heart}
        label={status.favorite ? 'Favourited' : 'Favourite'}
        active={status.favorite}
        activeColor="var(--brand)"
        onClick={guarded('favorites')}
      />
      {showWatchlist && (
        <ActionButton
          icon={Clock}
          label={status.watchlist ? 'In watchlist' : 'Watchlist'}
          active={status.watchlist}
          activeColor="var(--c-tv)"
          onClick={guarded('watchlist')}
        />
      )}
      <ActionButton
        icon={Bookmark}
        label={status.bookmark ? 'Bookmarked' : 'Bookmark'}
        active={status.bookmark}
        activeColor="var(--c-game)"
        onClick={guarded('bookmarks')}
      />
      <ActionButton
        icon={Bell}
        label={status.following ? 'Following' : 'Follow'}
        active={status.following}
        activeColor="var(--c-football)"
        onClick={guarded('following')}
      />
    </div>
  )
}
