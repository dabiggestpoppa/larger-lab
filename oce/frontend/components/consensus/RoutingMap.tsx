"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function RoutingMap() {
  const { routingDecisions, currentRoute } = useConsensusStore();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">ROUTING MAP</h2>
        {currentRoute && (
          <span className="text-xs font-mono text-accent-primary">{currentRoute}</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Current Route Visualization */}
        {currentRoute && (
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-text-primary mb-3">Active Route</h3>
            <div className="flex items-center gap-2 flex-wrap">
              {currentRoute.split("→").map((step, i) => (
                <span key={i} className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-lg bg-accent-primary/10 text-accent-primary text-sm font-mono">
                    {step.trim()}
                  </span>
                  {i < currentRoute.split("→").length - 1 && (
                    <span className="text-text-muted">→</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Routing Decisions */}
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Routing Decisions ({routingDecisions.length})
          </h3>
          {routingDecisions.length > 0 ? (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {routingDecisions.slice().reverse().map((decision, i) => (
                <div key={i} className="p-3 rounded bg-bg-tertiary">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-text-primary">{decision.task_domain}</span>
                    <span className="text-xs text-accent-success">
                      {(decision.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="text-xs text-text-muted">Route:</span>
                    <span className="px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary text-xs font-mono">
                      {decision.selected_route}
                    </span>
                  </div>
                  {decision.alternatives.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap mt-1">
                      <span className="text-xs text-text-muted">Alternatives:</span>
                      {decision.alternatives.map((alt, j) => (
                        <span key={j} className="px-2 py-0.5 rounded bg-bg-tertiary text-xs font-mono text-text-muted">
                          {alt}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="text-xs text-text-muted mt-1">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted">No routing decisions yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
