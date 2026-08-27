// Global error boundary: catches any render/lifecycle error in the tree below it
// and shows a friendly full-page fallback instead of a blank white screen.
//
// Wrapped around the whole app in main.jsx, so it also covers a crash in
// AuthProvider or the router. Recovery actions use window.location (not the
// router) because the router tree is exactly what may have just thrown.

import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    // Surface the crash for debugging; a production build would forward this to
    // an error-reporting service instead.
    console.error('Unhandled UI error:', error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="error-screen">
        <div className="card error-state">
          <span className="error-state-icon" aria-hidden="true">🧭</span>
          <h1 className="error-state-title">Something went wrong</h1>
          <p className="error-state-text">
            An unexpected error stopped this page from loading. Reloading usually
            fixes it — if it keeps happening, please try again in a little while.
          </p>
          {import.meta.env.DEV && this.state.error && (
            <pre className="error-state-detail">
              {String(this.state.error?.stack || this.state.error)}
            </pre>
          )}
          <div className="error-state-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              Reload page
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => window.location.assign('/')}
            >
              Back to homepage
            </button>
          </div>
        </div>
      </div>
    )
  }
}
