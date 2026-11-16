import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Unmount anything rendered between tests so they stay isolated.
afterEach(() => {
  cleanup()
})
