import { useAnime } from '@/api/hooks/lists'
import type { AnimeQuery } from '@/api/hooks/lists'
import { CatalogBrowse, PAGE_SIZE } from '@/components/CatalogBrowse'

export function AnimePage() {
  return (
    <CatalogBrowse
      title="Anime"
      genreType="anime"
      statusTabs={[
        { value: '', label: 'All' },
        { value: 'releasing', label: 'Airing now' },
        { value: 'not_yet_released', label: 'Upcoming' },
        { value: 'finished', label: 'Finished' },
      ]}
      buildQuery={({ status, genre, page }): AnimeQuery => ({
        airing_status: (status || undefined) as AnimeQuery['airing_status'],
        genre: genre || undefined,
        page,
        page_size: PAGE_SIZE,
      })}
      useList={useAnime}
    />
  )
}
