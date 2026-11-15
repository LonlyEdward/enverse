import { useGames } from '@/api/hooks/lists'
import type { GameQuery } from '@/api/hooks/lists'
import { CatalogBrowse, PAGE_SIZE } from '@/components/CatalogBrowse'

export function GamesPage() {
  return (
    <CatalogBrowse
      title="Games"
      genreType="game"
      statusTabs={[
        { value: '', label: 'All' },
        { value: 'upcoming', label: 'Upcoming' },
        { value: 'released', label: 'Released' },
      ]}
      buildQuery={({ status, genre, page }): GameQuery => ({
        status: (status || undefined) as GameQuery['status'],
        genre: genre || undefined,
        page,
        page_size: PAGE_SIZE,
      })}
      useList={useGames}
    />
  )
}
