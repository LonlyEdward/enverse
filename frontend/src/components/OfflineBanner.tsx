import { WifiOff } from 'lucide-react'
import { useEffect, useState } from 'react'

/** A persistent banner shown whenever the browser reports it is offline, so a
 *  failed load reads as "no connection" rather than "the app is broken". */
export function OfflineBanner() {
  const [offline, setOffline] = useState(
    () => typeof navigator !== 'undefined' && !navigator.onLine,
  )

  useEffect(() => {
    function update() {
      setOffline(!navigator.onLine)
    }
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => {
      window.removeEventListener('online', update)
      window.removeEventListener('offline', update)
    }
  }, [])

  if (!offline) return null

  return (
    <div className="border-b border-danger/25 bg-danger/10" role="status">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2.5">
        <WifiOff size={18} className="shrink-0 text-danger" aria-hidden="true" />
        <p className="text-sm text-fg">
          You are offline. Some things may not load until your connection is
          back.
        </p>
      </div>
    </div>
  )
}
