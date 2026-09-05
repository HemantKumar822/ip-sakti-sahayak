// src/components/ErrorBoundary.tsx
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public override state: ErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log exception context for diagnostic telemetry
    console.error('Unhandled React Error caught by ErrorBoundary:', error, errorInfo);
  }

  private handleReset = (): void => {
    // Clear session storage and URL query parameter to avoid restoring faulty state
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('ip_sakti_session_id');
        const url = new URL(window.location.href);
        url.searchParams.delete('session');
        window.history.replaceState(null, '', url.pathname);
      } catch {
        // Fallback for sandboxed browser environments
      }
    }

    // Reset local error state
    this.setState({ hasError: false, error: null });

    // Call external reset callback if provided
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleReload = (): void => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  public override render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="sk-portal" role="alert" style={{ alignItems: 'center' }}>
          <div className="sk-card" style={{ maxWidth: '560px' }}>
            <p className="sk-eyebrow" style={{ color: 'var(--status-error)', display: 'inline-flex', gap: 'var(--space-sm)', alignItems: 'center' }}>
              <AlertTriangle size={15} aria-hidden="true" />
              <span>SYSTEM FAULT // RECOVERY WORKBENCH</span>
            </p>
            <h2 className="sk-h2" style={{ marginTop: 'var(--space-sm)' }}>
              Something broke rendering this view
            </h2>
            <p className="sk-body" style={{ marginTop: 'var(--space-sm)' }}>
              Resetting clears the stored session and returns to a clean desk. Your corpus and history on the server are untouched.
            </p>
            {this.state.error && (
              <pre className="sk-mini" style={{ marginTop: 'var(--space-md)', padding: 'var(--space-md)', background: 'var(--canvas-soft)', border: '1px solid var(--hairline)', borderRadius: 'var(--radius-sm)', overflowX: 'auto' }}>
                {this.state.error.message || String(this.state.error)}
              </pre>
            )}
            <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-lg)' }}>
              <button type="button" className="sk-btn sk-btn-primary sk-btn-sm" onClick={this.handleReset}>
                Reset Workspace
              </button>
              <button type="button" className="sk-btn sk-btn-sm" onClick={this.handleReload}>
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
