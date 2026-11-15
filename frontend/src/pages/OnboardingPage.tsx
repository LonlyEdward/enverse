import { useQuery } from '@tanstack/react-query'
import { Check, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/errors'
import {
  addFavorite,
  fetchGenres,
  followTeam,
  saveGenrePreferences,
  savePlatformPreferences,
  searchContent,
  searchTeams,
} from '@/api/preferences'
import type { GenreContentType, GenrePreferenceItem } from '@/api/preferences'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { Input } from '@/components/Input'
import { SelectChip } from '@/components/SelectChip'
import { Spinner } from '@/components/Spinner'
import { useToast } from '@/components/toast'
import { cn } from '@/lib/cn'
import { CONTENT_TYPES } from '@/lib/contentTypes'
import { PLATFORMS } from '@/lib/platforms'
import { useDebouncedValue } from '@/lib/useDebouncedValue'

const GENRE_TYPES: GenreContentType[] = ['movie', 'tv', 'anime', 'game']
const STEPS = ['Genres', 'Platforms', 'Teams', 'Favourites'] as const
const ONBOARDED_KEY = 'enverse-onboarded'

export function OnboardingPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { isVerified } = useAuth()

  const [step, setStep] = useState(0)
  const [genres, setGenres] = useState<Set<string>>(new Set())
  const [platforms, setPlatforms] = useState<Set<string>>(new Set())
  const [followed, setFollowed] = useState<Set<number>>(new Set())
  const [favorites, setFavorites] = useState<Set<string>>(new Set())
  const [finishing, setFinishing] = useState(false)

  const genresQuery = useQuery({
    queryKey: ['onboarding-genres'],
    queryFn: async () => {
      const lists = await Promise.all(GENRE_TYPES.map((t) => fetchGenres(t)))
      return Object.fromEntries(
        GENRE_TYPES.map((t, i) => [t, lists[i]]),
      ) as Record<GenreContentType, string[]>
    },
  })

  function toggle<T>(set: Set<T>, value: T): Set<T> {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    return next
  }

  function finishLater() {
    try {
      localStorage.setItem(ONBOARDED_KEY, '1')
    } catch {
      // ignore
    }
  }

  async function handleFinish() {
    setFinishing(true)
    try {
      const items: GenrePreferenceItem[] = [...genres].map((key) => {
        const [content_type, genre] = key.split('::')
        return { content_type: content_type as GenreContentType, genre: genre! }
      })
      await Promise.all([
        saveGenrePreferences(items),
        savePlatformPreferences([...platforms]),
      ])
      finishLater()
      toast({ title: 'You are all set', tone: 'success' })
      navigate('/', { replace: true })
    } catch (err) {
      toast({
        title: 'Could not save your preferences',
        description: err instanceof ApiError ? err.message : undefined,
        tone: 'error',
      })
    } finally {
      setFinishing(false)
    }
  }

  function handleSkip() {
    finishLater()
    navigate('/', { replace: true })
  }

  const isLast = step === STEPS.length - 1

  return (
    <div className="mx-auto max-w-2xl py-4">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2" aria-hidden="true">
          {STEPS.map((label, i) => (
            <span
              key={label}
              className={cn(
                'h-1.5 rounded-full transition-all',
                i === step ? 'w-8 bg-brand' : 'w-4 bg-surface-3',
              )}
            />
          ))}
        </div>
        <button
          type="button"
          onClick={handleSkip}
          className="cursor-pointer text-sm font-medium text-fg-muted hover:text-fg"
        >
          Skip for now
        </button>
      </div>

      <p className="text-sm text-fg-subtle">
        Step {step + 1} of {STEPS.length}
      </p>
      <h1 className="mt-1 text-2xl font-semibold text-fg">
        {step === 0 && 'What do you like to watch and play?'}
        {step === 1 && 'Where do you watch and play?'}
        {step === 2 && 'Follow your teams'}
        {step === 3 && 'Add a few favourites'}
      </h1>
      <p className="mt-1 mb-6 text-sm text-fg-muted">
        {step === 0 &&
          'Pick the genres you enjoy. We use these to tailor your feed.'}
        {step === 1 &&
          'Choose the services you use so we can show the right titles.'}
        {step === 2 &&
          'Search for football clubs to follow their fixtures and results.'}
        {step === 3 && 'Optional — search for anything you already love.'}
      </p>

      <div className="min-h-[18rem]">
        {step === 0 && (
          <GenresStep
            query={genresQuery}
            selected={genres}
            onToggle={(key) => setGenres((s) => toggle(s, key))}
          />
        )}
        {step === 1 && (
          <div className="flex flex-wrap gap-2">
            {PLATFORMS.map((p) => (
              <SelectChip
                key={p}
                label={p}
                selected={platforms.has(p)}
                onToggle={() => setPlatforms((s) => toggle(s, p))}
              />
            ))}
          </div>
        )}
        {step === 2 && (
          <TeamsStep
            isVerified={isVerified}
            followed={followed}
            onFollow={async (id) => {
              try {
                await followTeam(id)
                setFollowed((s) => new Set(s).add(id))
              } catch (err) {
                toast({
                  title: 'Could not follow that team',
                  description:
                    err instanceof ApiError ? err.message : undefined,
                  tone: 'error',
                })
              }
            }}
          />
        )}
        {step === 3 && (
          <FavoritesStep
            isVerified={isVerified}
            favorites={favorites}
            onFavorite={async (ct, id) => {
              try {
                await addFavorite(ct, id)
                setFavorites((s) => new Set(s).add(`${ct}::${id}`))
              } catch (err) {
                toast({
                  title: 'Could not save that favourite',
                  description:
                    err instanceof ApiError ? err.message : undefined,
                  tone: 'error',
                })
              }
            }}
          />
        )}
      </div>

      <div className="mt-8 flex items-center justify-between border-t border-border pt-5">
        <Button
          variant="ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
        >
          Back
        </Button>
        {isLast ? (
          <Button onClick={handleFinish} loading={finishing}>
            Finish
          </Button>
        ) : (
          <Button onClick={() => setStep((s) => s + 1)}>Continue</Button>
        )}
      </div>
    </div>
  )
}

function GenresStep({
  query,
  selected,
  onToggle,
}: {
  query: ReturnType<typeof useQuery<Record<GenreContentType, string[]>, Error>>
  selected: Set<string>
  onToggle: (key: string) => void
}) {
  if (query.isLoading) {
    return (
      <div className="flex justify-center py-10">
        <Spinner label="Loading genres" />
      </div>
    )
  }
  if (query.isError || !query.data) {
    return (
      <ErrorState error={query.error} onRetry={() => void query.refetch()} />
    )
  }

  return (
    <div className="space-y-6">
      {GENRE_TYPES.map((type) => {
        const meta = CONTENT_TYPES[type]
        const Icon = meta.icon
        return (
          <div key={type}>
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-fg">
              <Icon
                size={15}
                style={{ color: meta.color }}
                aria-hidden="true"
              />
              {meta.plural}
            </h2>
            <div className="flex flex-wrap gap-2">
              {query.data[type].map((genre) => {
                const key = `${type}::${genre}`
                return (
                  <SelectChip
                    key={key}
                    label={genre}
                    selected={selected.has(key)}
                    onToggle={() => onToggle(key)}
                  />
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function VerifyNote() {
  return (
    <EmptyState
      title="Verify your email first"
      description="Following teams and saving favourites needs a verified email. You can finish the rest now and come back to this later."
    />
  )
}

function TeamsStep({
  isVerified,
  followed,
  onFollow,
}: {
  isVerified: boolean
  followed: Set<number>
  onFollow: (id: number) => void
}) {
  const [term, setTerm] = useState('')
  const debounced = useDebouncedValue(term, 300)
  const enabled = debounced.trim().length >= 2
  const teams = useQuery({
    queryKey: ['onboarding-teams', debounced],
    queryFn: () => searchTeams(debounced.trim()),
    enabled,
  })

  if (!isVerified) return <VerifyNote />

  return (
    <div className="space-y-4">
      <Input
        label="Search teams"
        hideLabel
        placeholder="Search for a club, e.g. Arsenal"
        leftIcon={<Search size={16} aria-hidden="true" />}
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />
      {enabled && teams.isLoading && (
        <div className="flex justify-center py-6">
          <Spinner label="Searching teams" />
        </div>
      )}
      {enabled && teams.data && teams.data.length === 0 && (
        <p className="py-4 text-center text-sm text-fg-muted">
          No teams match “{debounced}”.
        </p>
      )}
      <ul className="divide-y divide-border">
        {teams.data?.map((team) => {
          const isFollowed = followed.has(team.id)
          return (
            <li key={team.id} className="flex items-center gap-3 py-2.5">
              <img
                src={team.logo_url}
                alt=""
                className="h-9 w-9 rounded-full bg-surface-2 object-contain"
                loading="lazy"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">
                  {team.name}
                </p>
                <p className="truncate text-xs text-fg-subtle">
                  {team.competition}
                </p>
              </div>
              <Button
                variant={isFollowed ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => onFollow(team.id)}
                disabled={isFollowed}
                leftIcon={
                  isFollowed ? (
                    <Check size={16} aria-hidden="true" />
                  ) : undefined
                }
              >
                {isFollowed ? 'Following' : 'Follow'}
              </Button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function FavoritesStep({
  isVerified,
  favorites,
  onFavorite,
}: {
  isVerified: boolean
  favorites: Set<string>
  onFavorite: (contentType: string, id: number) => void
}) {
  const [term, setTerm] = useState('')
  const debounced = useDebouncedValue(term, 300)
  const enabled = debounced.trim().length >= 2
  const results = useQuery({
    queryKey: ['onboarding-search', debounced],
    queryFn: () => searchContent(debounced.trim()),
    enabled,
  })

  if (!isVerified) return <VerifyNote />

  return (
    <div className="space-y-4">
      <Input
        label="Search titles"
        hideLabel
        placeholder="Search movies, TV, anime or games"
        leftIcon={<Search size={16} aria-hidden="true" />}
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />
      {enabled && results.isLoading && (
        <div className="flex justify-center py-6">
          <Spinner label="Searching" />
        </div>
      )}
      {enabled && results.data && results.data.length === 0 && (
        <p className="py-4 text-center text-sm text-fg-muted">
          Nothing matches “{debounced}”.
        </p>
      )}
      <ul className="divide-y divide-border">
        {results.data?.map((item) => {
          const key = `${item.content_type}::${item.id}`
          const saved = favorites.has(key)
          return (
            <li key={key} className="flex items-center gap-3 py-2.5">
              <img
                src={item.poster_url}
                alt=""
                className="h-14 w-10 shrink-0 rounded bg-surface-2 object-cover"
                loading="lazy"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-fg">
                  {item.title}
                </p>
                <p className="truncate text-xs text-fg-subtle">
                  {item.subtitle}
                </p>
              </div>
              <Button
                variant={saved ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => onFavorite(item.content_type, item.id)}
                disabled={saved}
                leftIcon={
                  saved ? <Check size={16} aria-hidden="true" /> : undefined
                }
              >
                {saved ? 'Added' : 'Add'}
              </Button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
