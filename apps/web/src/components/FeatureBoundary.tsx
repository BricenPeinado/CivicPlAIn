import { Component, type ReactNode } from 'react';

export class FeatureBoundary extends Component<{ children: ReactNode; name: string }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <div className="state-card" role="alert"><h2>{this.props.name} unavailable</h2><p>Reload the workspace to retry loading this panel. Saved records are retained.</p><button className="text-button" onClick={() => window.location.reload()}>Reload workspace</button></div> : this.props.children;
  }
}
