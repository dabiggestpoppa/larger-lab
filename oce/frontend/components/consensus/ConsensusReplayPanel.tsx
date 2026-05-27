"use client";

import { useConsensusStore } from "@/stores/consensusStore";

export default function ConsensusReplayPanel() {
  const { replayHistory, selectedReplay, setSelectedReplay } = useConsensusStore();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-4 py-2 border-b border-border-light bg-bg-secondary">
        <h2 className="text-xs font-mono font-bold text-text-primary">CONSENSUS REPLAY</h2>
        <span className="ml-2 text-xs text-text-muted">({replayHistory.length})</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {replayHistory.length > 0 ? (
          <>
            {/* Replay List */}
            <div className="space-y-2">
              {replayHistory.map((item, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedReplay(item)}
                  className={`card p-3 cursor-pointer transition-colors ${
                    selectedReplay?.replay_id === item.replay_id
                      ? "border-accent-primary"
                      : "hover:border-border-light"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        item.outcome === "success" ? "bg-accent-success" :
                        item.outcome === "failure" ? "bg-accent-danger" : "bg-accent-warning"
                      }`} />
                      <span className="text-xs font-mono text-text-primary">
                        {item.consensus_result.task_type}
                      </span>
                    </div>
                    <span className="text-xs text-text-muted">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-text-muted">
                      {(item.consensus_result.confidence * 100).toFixed(0)}% confidence
                    </span>
                    <span className="text-xs text-text-muted">
                      {item.duration_ms}ms
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Replay Detail */}
            {selectedReplay && (
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-text-primary mb-3">Replay Detail</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 rounded bg-bg-tertiary">
                    <div className="text-xs text-text-muted">Task Type</div>
                    <div className="text-sm font-mono text-text-primary">{selectedReplay.consensus_result.task_type}</div>
                  </div>
                  <div className="p-2 rounded bg-bg-tertiary">
                    <div className="text-xs text-text-muted">Outcome</div>
                    <div className={`text-sm font-mono ${
                      selectedReplay.outcome === "success" ? "text-accent-success" :
                      selectedReplay.outcome === "failure" ? "text-accent-danger" : "text-accent-warning"
                    }`}>
                      {selectedReplay.outcome}
                    </div>
                  </div>
                  <div className="p-2 rounded bg-bg-tertiary">
                    <div className="text-xs text-text-muted">Agreement</div>
                    <div className="text-sm font-mono text-accent-success">
                      {(selectedReplay.consensus_result.agreement_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="p-2 rounded bg-bg-tertiary">
                    <div className="text-xs text-text-muted">Duration</div>
                    <div className="text-sm font-mono text-text-primary">{selectedReplay.duration_ms}ms</div>
                  </div>
                </div>

                <div className="mt-3">
                  <div className="text-xs text-text-muted mb-1">Routing Path</div>
                  <div className="flex items-center gap-1 flex-wrap">
                    {selectedReplay.consensus_result.routing_path.map((step, i) => (
                      <span key={i} className="flex items-center gap-1">
                        <span className="px-2 py-0.5 rounded bg-accent-primary/10 text-accent-primary text-xs font-mono">
                          {step}
                        </span>
                        {i < selectedReplay.consensus_result.routing_path.length - 1 && (
                          <span className="text-text-muted">→</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="card p-4 text-center">
            <p className="text-xs text-text-muted">No consensus replay history yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
