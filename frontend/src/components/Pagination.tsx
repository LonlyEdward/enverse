import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from './Button'

interface PaginationProps {
  page: number
  pageCount: number
  onPageChange: (page: number) => void
}

/** Previous/next pager with a current-page readout. Kept simple: the API
 *  paginates by page number, so we only need to move one page at a time. */
export function Pagination({ page, pageCount, onPageChange }: PaginationProps) {
  if (pageCount <= 1) return null

  return (
    <nav
      className="flex items-center justify-center gap-4 py-6"
      aria-label="Pagination"
    >
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        leftIcon={<ChevronLeft size={16} aria-hidden="true" />}
      >
        Previous
      </Button>
      <span className="text-sm text-fg-muted" aria-current="page">
        Page {page} of {pageCount}
      </span>
      <Button
        variant="outline"
        size="sm"
        disabled={page >= pageCount}
        onClick={() => onPageChange(page + 1)}
      >
        Next
        <ChevronRight size={16} aria-hidden="true" />
      </Button>
    </nav>
  )
}
