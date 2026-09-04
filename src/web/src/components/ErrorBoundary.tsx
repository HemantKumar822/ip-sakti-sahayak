// src/components/ErrorBoundary.tsx
import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import './ErrorBoundary.css';

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
        <div className="error-boundary-wrapper" role="alert">
          <div className="error-boundary-card">
            <div className="error-boundary-header">
              <div className="error-boundary-icon">
                <AlertTriangle size={24} />
              </div>
              <span className="error-boundary-eyebrow">
                SYSTEM FAULT // RECOVERY WORKBENCH
              </span>
            </div>

            <h2 className="error-boundary-title">
              Application Encountered an Unhandled State
            </h2>

            <p className="error-boundary-desc">
              An unhandled rendering exception occurred. You can reset the workspace session to return to a clean operational state.
            </p>

            {this.state.error && (
              <pre className="error-boundary-details">
                {this.state.error.message || String(this.state.error)}
              </pre>
            )}

            <div className="error-boundary-actions">
              <button
                type="button"
                className="error-reset-btn"
                onClick={this.handleReset}
              >
                Reset Workspace
              </button>
              <button
                type="button"
                className="error-reload-btn"
                onClick={this.handleReload}
              >
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
