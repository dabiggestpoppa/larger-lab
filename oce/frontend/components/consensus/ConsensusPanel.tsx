"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function ConsensusPanel() {
  const { currentConsensus, consensusHistory, isConsensusActive } = useConsensusStore();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">OBSERVER CONSENSUS</h2>
        <div className="flex items-center gap-2">
          {isConsensusActive && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-accent-success animate-pulse" />
              <span className="text-xs text-accent-success">Active</span>
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Current Consensus */}
        {currentConsensus ? (
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-text-primary mb-3">Current Consensus</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Task Type</div>
                <div className="text-sm font-mono text-text-primary">{currentConsensus.task_type}</div>
              </div>
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Complexity</div>
                <div className="text-sm font-mono text-text-primary">{currentConsensus.complexity}</div>
              </div>
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Confidence</div>
                <div className="text-sm font-mono text-accent-primary">
                  {(currentConsensus.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Agreement</div>
                <div className="text-sm font-mono text-accent-success">
                  {(currentConsensus.agreement_score * 100).toFixed(0)}%
                </div>
              </div>
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Voters</div>
                <div className="text-sm font-mono text-text-primary">{currentConsensus.voter_count}</div>
              </div>
              <div className="p-2 rounded bg-bg-tertiary">
                <div className="text-xs text-text-muted">Spawn Required</div>
                <div className={`text-sm font-mono ${currentConsensus.spawn_required ? "text-accent-warning" : "text-text-muted"}`}>
                  {currentConsensus.spawn_required ? "Yes" : "No"}
                </div>
              </div>
            </div>

            {/* Routing Path */}
            <div className="mt-3">
              <div className="text-xs text-text-muted mb-1">Routing Path</div>
              <div className="flex items-center gap-1 flex-wrap">
                {currentConsensus.routing_path.map((step, i) => (
                  <span key={i} className="flex items-center gap-1">
                    <span className="px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary text-xs font-mono">
                      {step}
                    </span>
                    {i < currentConsensus.routing_path.length - 1 && (
                      <span className="text-text-muted">→</span>
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Capabilities */}
            {currentConsensus.required_capabilities.length > 0 && (
              <div className="mt-3">
                <div className="text-xs text-text-muted mb-1">Required Capabilities</div>
                <div className="flex flex-wrap gap-1">
                  {currentConsensus.required_capabilities.map((cap, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-bg-tertiary text-xs font-mono text-text-secondary">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Model */}
            <div className="mt-3">
              <div className="text-xs text-text-muted mb-1">Recommended Model</div>
              <div className="text-sm font-mono text-accent-primary">{currentConsensus.recommended_model}</div>
            </div>
          </div>
        ) : (
          <div className="card p-4 text-center">
            <p className="text-xs text-text-muted">No active consensus. Submit a task to begin.</p>
          </div>
        )}

        {/* History */}
        {consensusHistory.length > 0 && (
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-text-primary mb-3">
              History ({consensusHistory.length})
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {consensusHistory.slice().reverse().map((item, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded bg-bg-tertiary">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-text-primary">{item.task_type}</span>
                    <span className="text-xs text-text-muted">{item.complexity}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-accent-success">
                      {(item.agreement_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs text-text-muted">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
