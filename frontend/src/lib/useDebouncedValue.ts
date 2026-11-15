import { useEffect, useState } from 'react'

/** Return a copy of `value` that only updates after it has stopped changing
 *  for `delay` ms — used to avoid firing a search on every keystroke. */
export function useDebouncedValue<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(id)
  }, [value, delay])

  return debounced
}
