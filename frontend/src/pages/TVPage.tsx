import { useTV } from '@/api/hooks/lists'
import type { TVQuery } from '@/api/hooks/lists'
import { CatalogBrowse, PAGE_SIZE } from '@/components/CatalogBrowse'

export function TVPage() {
  return (
    <CatalogBrowse
      title="TV shows"
      genreType="tv"
      statusTabs={[
        { value: '', label: 'All' },
        { value: 'returning', label: 'Returning' },
        { value: 'ended', label: 'Ended' },
        { value: 'canceled', label: 'Canceled' },
      ]}
      buildQuery={({ status, genre, page }): TVQuery => ({
        status: (status || undefined) as TVQuery['status'],
        genre: genre || undefined,
        page,
        page_size: PAGE_SIZE,
      })}
      useList={useTV}
    />
  )
}
