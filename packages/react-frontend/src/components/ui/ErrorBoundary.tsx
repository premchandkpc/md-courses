import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: undefined }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full text-infra-500 text-sm font-mono p-8">
          <div className="text-center">
            <div className="text-accent-red text-lg mb-2">Component Error</div>
            <div className="text-infra-400 text-xs">{this.state.error?.message}</div>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="mt-4 px-4 py-1.5 rounded text-xs font-mono bg-infra-700 text-infra-200 hover:bg-infra-600 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
