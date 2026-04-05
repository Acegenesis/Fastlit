import React from "react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  nodeId?: string;
}

interface ErrorBoundaryState {
  error: Error | null;
  retryKey: number;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null, retryKey: 0 };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error, retryKey: 0 };
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (prevProps.nodeId !== this.props.nodeId && this.state.error) {
      this.setState({ error: null, retryKey: this.state.retryKey + 1 });
    }
  }

  private handleRetry = () => {
    this.setState((state) => ({ error: null, retryKey: state.retryKey + 1 }));
  };

  render() {
    if (this.state.error) {
      return (
        <div className="my-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          <div className="font-medium">Component render failed</div>
          <div className="mt-1 break-words">{this.state.error.message}</div>
          <button
            type="button"
            className="mt-3 rounded bg-white px-3 py-1 text-sm text-red-700 shadow-sm ring-1 ring-red-200"
            onClick={this.handleRetry}
          >
            Retry
          </button>
        </div>
      );
    }
    return <React.Fragment key={this.state.retryKey}>{this.props.children}</React.Fragment>;
  }
}
