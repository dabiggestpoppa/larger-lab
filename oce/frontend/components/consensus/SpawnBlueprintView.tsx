"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function SpawnBlueprintView() {
  const { currentConsensus } = useConsensusStore();

  if (!currentConsensus?.spawn_required) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center px-4 py-2 border-b border-border-light bg-bg-secondary">
          <h2 className="text-xs font-mono font-bold text-text-primary">SPAWN BLUEPRINT</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-4">
          <p className="text-xs text-text-muted">No spawn required for current task.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">SPAWN BLUEPRINT</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Execution Plan</h3>
          <div className="space-y-3">
            {/* Task Info */}
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 rounded bg-accent-primary/10 text-accent-primary text-xs font-mono">
                {currentConsensus.task_type}
              </span>
              <span className="px-2 py-1 rounded bg-bg-tertiary text-text-secondary text-xs font-mono">
                {currentConsensus.complexity}
              </span>
              <span className="px-2 py-1 rounded bg-accent-success/10 text-accent-success text-xs font-mono">
                {(currentConsensus.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>

            {/* Routing Steps */}
            <div>
              <div className="text-xs text-text-muted mb-2">Execution Steps</div>
              <div className="space-y-1">
                {currentConsensus.routing_path.map((step, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-accent-primary/10 text-accent-primary text-xs font-mono flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="text-sm font-mono text-text-primary">{step}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Capabilities */}
            {currentConsensus.required_capabilities.length > 0 && (
              <div>
                <div className="text-xs text-text-muted mb-2">Required Capabilities</div>
                <div className="flex flex-wrap gap-1">
                  {currentConsensus.required_capabilities.map((cap, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-accent-warning/10 text-accent-warning text-xs font-mono">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Model */}
            <div>
              <div className="text-xs text-text-muted mb-1">Recommended Model</div>
              <div className="text-sm font-mono text-accent-primary">{currentConsensus.recommended_model}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
