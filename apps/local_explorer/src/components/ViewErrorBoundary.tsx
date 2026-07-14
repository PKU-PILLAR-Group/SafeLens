import React from "react";
import { AlertTriangle, Check, Copy, LayoutDashboard, RefreshCw, X } from "lucide-react";
import { LazyRetryGenerationContext } from "./retryableLazy";

interface ViewErrorBoundaryProps {
  children: React.ReactNode;
  resetKey: string;
  viewLabel: string;
  variant?: "view" | "dialog";
  onOpenOverview?: () => void;
  onDismiss?: () => void;
}

interface ViewErrorBoundaryState {
  error: Error | null;
  retry: number;
  componentStack: string;
  copyStatus: "idle" | "copied" | "failed";
  errorResetKey: string | null;
}

export class ViewErrorBoundary extends React.Component<
  ViewErrorBoundaryProps,
  ViewErrorBoundaryState
> {
  state: ViewErrorBoundaryState = {
    error: null,
    retry: 0,
    componentStack: "",
    copyStatus: "idle",
    errorResetKey: null
  };
  private fallbackRef = React.createRef<HTMLElement>();

  static getDerivedStateFromError(error: Error): Partial<ViewErrorBoundaryState> {
    return { error };
  }

  componentDidCatch(_error: Error, info: React.ErrorInfo) {
    this.setState({
      componentStack: info.componentStack ?? "",
      errorResetKey: this.props.resetKey
    });
    window.requestAnimationFrame(() => this.fallbackRef.current?.focus());
  }

  componentDidUpdate() {
    if (
      this.state.error &&
      this.state.errorResetKey !== null &&
      this.state.errorResetKey !== this.props.resetKey
    ) {
      this.setState({
        error: null,
        retry: 0,
        componentStack: "",
        copyStatus: "idle",
        errorResetKey: null
      });
    }
  }

  private retryView = () => {
    this.setState((current) => ({
      error: null,
      retry: current.retry + 1,
      componentStack: "",
      copyStatus: "idle",
      errorResetKey: null
    }));
  };

  private copyDiagnostics = async () => {
    const error = this.state.error;
    if (!error) return;
    const diagnostics = {
      schemaVersion: "1.0",
      kind: this.props.variant === "dialog"
        ? "safelens-dialog-render-error"
        : "safelens-view-render-error",
      view: this.props.viewLabel,
      context: this.props.resetKey,
      error: { name: error.name, message: error.message },
      componentStack: this.state.componentStack.trim(),
      location: window.location.href,
      userAgent: navigator.userAgent,
      capturedAt: new Date().toISOString()
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(diagnostics, null, 2));
      this.setState({ copyStatus: "copied" });
    } catch {
      this.setState({ copyStatus: "failed" });
    }
  };

  private handleDialogKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      this.props.onDismiss?.();
      return;
    }
    if (event.key !== "Tab") return;
    const dialog = this.fallbackRef.current;
    if (!dialog) return;
    const focusable = Array.from(dialog.querySelectorAll<HTMLElement>(
      "button:not(:disabled), summary, [href], [tabindex]:not([tabindex='-1'])"
    ));
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  render() {
    if (!this.state.error) {
      return (
        <LazyRetryGenerationContext.Provider value={this.state.retry}>
          <React.Fragment key={this.state.retry}>{this.props.children}</React.Fragment>
        </LazyRetryGenerationContext.Provider>
      );
    }

    if (this.props.variant === "dialog") {
      return (
        <div
          className="compare-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) this.props.onDismiss?.();
          }}
        >
          <aside
            ref={this.fallbackRef}
            className="compare-drawer compare-error-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`${this.props.viewLabel} error`}
            tabIndex={-1}
            onKeyDown={this.handleDialogKeyDown}
          >
            <header className="compare-error-heading">
              <AlertTriangle size={20} />
              <div>
                <strong>{this.props.viewLabel} could not be opened</strong>
                <span>The workspace and pinned evidence are unchanged.</span>
              </div>
              <button aria-label={`Close ${this.props.viewLabel.toLowerCase()} error`} onClick={this.props.onDismiss}>
                <X size={18} />
              </button>
            </header>
            <details className="compare-error-detail">
              <summary>Technical detail</summary>
              <code>{this.state.error.name}: {this.state.error.message}</code>
              <small>{this.props.resetKey}</small>
            </details>
            <div className="compare-error-actions">
              <button onClick={this.retryView}>
                <RefreshCw size={14} /> Retry comparison
              </button>
              <button onClick={this.props.onDismiss}>
                <X size={14} /> Close
              </button>
              <button aria-live="polite" onClick={() => void this.copyDiagnostics()}>
                {this.state.copyStatus === "copied" ? <Check size={14} /> : <Copy size={14} />}
                {this.state.copyStatus === "copied"
                  ? "Copied"
                  : this.state.copyStatus === "failed"
                    ? "Copy failed"
                    : "Copy diagnostics"}
              </button>
            </div>
          </aside>
        </div>
      );
    }

    return (
      <section
        ref={this.fallbackRef}
        className="view-error-state"
        role="alert"
        aria-label={`${this.props.viewLabel} view error`}
        tabIndex={-1}
      >
        <AlertTriangle size={20} />
        <div>
          <strong>{this.props.viewLabel} could not be rendered</strong>
          <span>Your run, token selection, Timeline, pins, and Inspector are unchanged.</span>
          <details>
            <summary>Technical detail</summary>
            <code>{this.state.error.name}: {this.state.error.message}</code>
            <small>{this.props.resetKey}</small>
          </details>
        </div>
        <div className="view-error-actions">
          <button onClick={this.retryView}>
            <RefreshCw size={14} /> Retry view
          </button>
          <button onClick={this.props.onOpenOverview} disabled={!this.props.onOpenOverview}>
            <LayoutDashboard size={14} /> Open Overview
          </button>
          <button aria-live="polite" onClick={() => void this.copyDiagnostics()}>
            {this.state.copyStatus === "copied" ? <Check size={14} /> : <Copy size={14} />}
            {this.state.copyStatus === "copied"
              ? "Copied"
              : this.state.copyStatus === "failed"
                ? "Copy failed"
                : "Copy diagnostics"}
          </button>
        </div>
      </section>
    );
  }
}
