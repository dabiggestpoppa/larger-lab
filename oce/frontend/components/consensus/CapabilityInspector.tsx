"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function CapabilityInspector() {
  const { capabilities } = useConsensusStore();

  const availableCount = capabilities.filter((c) => c.available).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">CAPABILITIES</h2>
        <span className="text-xs text-text-muted">
          {availableCount}/{capabilities.length} available
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {capabilities.length > 0 ? (
          capabilities.map((cap, i) => (
            <div key={i} className="card p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${cap.available ? "bg-accent-success" : "bg-accent-danger"}`} />
                  <span className="text-sm font-mono text-text-primary">{cap.name}</span>
                </div>
                <span className={`text-xs font-mono ${cap.available ? "text-accent-success" : "text-accent-danger"}`}>
                  {cap.available ? "Available" : "Unavailable"}
                </span>
              </div>

              {cap.description && (
                <p className="text-xs text-text-muted mb-2">{cap.description}</p>
              )}

              {cap.observers.length > 0 && (
                <div>
                  <div className="text-xs text-text-muted mb-1">Provided by:</div>
                  <div className="flex flex-wrap gap-1">
                    {cap.observers.map((obs, j) => (
                      <span key={j} className="px-2 py-0.5 rounded bg-bg-tertiary text-xs font-mono text-text-secondary">
                        {obs}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="card p-4 text-center">
            <p className="text-xs text-text-muted">No capabilities registered yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
