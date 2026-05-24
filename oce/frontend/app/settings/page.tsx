export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-text-primary">Settings</h1>
        <p className="text-xs text-text-secondary mt-1">OCE configuration</p>
      </div>

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-text-primary">Connection</h2>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-text-muted">Backend</span>
            <span className="text-text-primary">:8000</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">WebSocket</span>
            <span className="text-accent-success">Connected</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Frontend</span>
            <span className="text-text-primary">:3000</span>
          </div>
        </div>
      </div>

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-text-primary">System</h2>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-text-muted">Version</span>
            <span className="text-text-primary">OCE v2.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Phase</span>
            <span className="text-text-primary">Phase 11 — Operational Validation</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Mode</span>
            <span className="text-text-primary">Autopilot</span>
          </div>
        </div>
      </div>
    </div>
  );
}
