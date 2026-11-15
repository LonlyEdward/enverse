import { Outlet } from 'react-router-dom'

import { ErrorBoundary } from '@/components/ErrorBoundary'
import { VerifyEmailBanner } from '@/components/VerifyEmailBanner'
import { BottomTabs } from './BottomTabs'
import { TopBar } from './TopBar'

/** The app shell: top bar everywhere, bottom tabs on mobile, and the routed
 *  page in between. The extra bottom padding on mobile clears the tab bar. */
export function AppLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <TopBar />
      <VerifyEmailBanner />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 pb-24 pt-6 md:pb-10">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
      <BottomTabs />
    </div>
  )
}
