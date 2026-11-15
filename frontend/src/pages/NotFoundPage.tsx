import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/Button'
import { EmptyState } from '@/components/EmptyState'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <EmptyState
        icon={Compass}
        title="Page not found"
        description="The page you were looking for does not exist or has moved."
        action={
          <Link to="/">
            <Button variant="outline">Back to home</Button>
          </Link>
        }
      />
    </div>
  )
}
