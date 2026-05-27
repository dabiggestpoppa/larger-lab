"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function ObserverSpecializationMap() {
  const { specializations } = useConsensusStore();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">OBSERVER SPECIALIZATIONS</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {specializations.length > 0 ? (
          <div className="grid grid-cols-1 gap-3">
            {specializations.map((spec, i) => (
              <div key={i} className="card p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-accent-success" />
                    <span className="text-sm font-mono text-text-primary">{spec.observer_id}</span>
                  </div>
                  <span className="text-xs text-text-muted">{spec.observer_type}</span>
                </div>

                <div className="flex items-center gap-3 mb-2">
                  <div className="flex-1">
                    <div className="text-xs text-text-muted">Accuracy</div>
                    <div className="h-1.5 rounded-full bg-bg-tertiary mt-1">
                      <div
                        className="h-full rounded-full bg-accent-success"
                        style={{ width: `${spec.accuracy * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs font-mono text-accent-success">
                    {(spec.accuracy * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="text-xs text-text-muted">
                  Tasks completed: {spec.tasks_completed}
                </div>

                {spec.specializations.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {spec.specializations.map((s, j) => (
                      <span key={j} className="px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary text-xs font-mono">
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-4 text-center">
            <p className="text-xs text-text-muted">No observer specializations yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
