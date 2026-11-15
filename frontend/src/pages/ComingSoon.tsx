import { Hammer } from 'lucide-react'

import { EmptyState } from '@/components/EmptyState'

/** Placeholder for routes whose full screens arrive in later build phases.
 *  Kept honest: it says the plumbing works and the screen is still to come,
 *  rather than pretending to be a finished feature. */
export function ComingSoon({ title }: { title: string }) {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <EmptyState
        icon={Hammer}
        title={`${title} is on the way`}
        description="The foundation is in place. This screen is built in a later phase of the project."
      />
    </div>
  )
}
