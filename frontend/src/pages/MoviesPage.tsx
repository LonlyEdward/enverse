import { useMovies } from '@/api/hooks/lists'
import type { MovieQuery } from '@/api/hooks/lists'
import { CatalogBrowse, PAGE_SIZE } from '@/components/CatalogBrowse'

export function MoviesPage() {
  return (
    <CatalogBrowse
      title="Movies"
      genreType="movie"
      statusTabs={[
        { value: '', label: 'All' },
        { value: 'now_showing', label: 'In cinemas' },
        { value: 'upcoming', label: 'Upcoming' },
        { value: 'recent', label: 'Recently released' },
      ]}
      buildQuery={({ status, genre, page }): MovieQuery => ({
        status: (status || undefined) as MovieQuery['status'],
        genre: genre || undefined,
        page,
        page_size: PAGE_SIZE,
      })}
      useList={useMovies}
    />
  )
}
