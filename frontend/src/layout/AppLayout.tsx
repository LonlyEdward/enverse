import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'

import { ErrorBoundary } from '@/components/ErrorBoundary'
import { OfflineBanner } from '@/components/OfflineBanner'
import { Spinner } from '@/components/Spinner'
import { VerifyEmailBanner } from '@/components/VerifyEmailBanner'
import { BottomTabs } from './BottomTabs'
import { TopBar } from './TopBar'

/** The app shell: top bar everywhere, bottom tabs on mobile, and the routed
 *  page in between. The extra bottom padding on mobile clears the tab bar. */
export function AppLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      {/* Keyboard users can jump straight past the nav to the page content. */}
      <a
        href="#main-content"
        className="sr-only focus-visible:not-sr-only focus-visible:fixed focus-visible:left-4 focus-visible:top-4 focus-visible:z-50 focus-visible:rounded-lg focus-visible:bg-surface focus-visible:px-4 focus-visible:py-2 focus-visible:text-sm focus-visible:font-medium focus-visible:text-fg focus-visible:shadow-[var(--shadow-pop)] focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
      >
        Skip to content
      </a>
      <TopBar />
      <OfflineBanner />
      <VerifyEmailBanner />
      <main
        id="main-content"
        className="mx-auto w-full max-w-7xl flex-1 px-4 pb-24 pt-6 md:pb-10"
      >
        <ErrorBoundary>
          {/* Routes are lazy chunks; the shell stays while one loads. */}
          <Suspense
            fallback={
              <div className="flex min-h-[50vh] items-center justify-center">
                <Spinner label="Loading page" />
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
      <BottomTabs />
    </div>
  )
}
