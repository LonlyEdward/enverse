import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

import { Button } from './Button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Catches render-time errors anywhere below it so one broken view cannot take
 *  down the whole app. React has no hook equivalent, so this stays a class. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Kept to the console for now; a real error reporter can hook in here.
    console.error('Unhandled UI error:', error, info.componentStack)
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div
          role="alert"
          className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center"
        >
          <h1 className="text-2xl font-semibold text-fg">
            This page hit a snag
          </h1>
          <p className="max-w-sm text-sm text-fg-muted">
            An unexpected error stopped this view from rendering. Reloading
            usually clears it.
          </p>
          <Button onClick={() => window.location.reload()}>Reload page</Button>
        </div>
      )
    }
    return this.props.children
  }
}
