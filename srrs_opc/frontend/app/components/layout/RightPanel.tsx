"use client";

import { useState } from "react";

interface ObserverDetails {
  id: string;
  type: string;
  status: string;
  entropy: number;
  syncScore: number;
  repairState: string;
  connections: number;
}

export default function RightPanel() {
  const [selectedObserver, setSelectedObserver] = useState<ObserverDetails | null>(null);

  return (
    <aside
      className="flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto observatory-scroll"
      style={{ width: "var(--right-panel-width)" }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)] uppercase tracking-wider">
          Inspector
        </h2>
      </div>

      {/* Observer Details */}
      {selectedObserver ? (
        <div className="p-4 space-y-3">
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">ID</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{selectedObserver.id}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Type</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{selectedObserver.type}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Status</span>
            <p className={`text-xs font-mono ${
              selectedObserver.status === "active" ? "text-[var(--observer-active)]" :
              selectedObserver.status === "synced" ? "text-[var(--observer-synced)]" :
              selectedObserver.status === "repairing" ? "text-[var(--observer-repairing)]" :
              "text-[var(--observer-dormant)]"
            }`}>
              {selectedObserver.status}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Entropy</span>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${selectedObserver.entropy * 100}%`,
                    backgroundColor: selectedObserver.entropy > 0.7 ? "var(--field-danger)" :
                      selectedObserver.entropy > 0.4 ? "var(--field-warning)" : "var(--field-stable)"
                  }}
                />
              </div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">
                {(selectedObserver.entropy * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Sync Score</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">
              {(selectedObserver.syncScore * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Connections</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{selectedObserver.connections}</p>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <p className="text-[10px] font-mono text-[var(--text-muted)] text-center">
            Select an observer to inspect
          </p>
        </div>
      )}

      {/* Event Feed */}
      <div className="border-t border-[var(--border-subtle)] p-4">
        <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase mb-2">Event Feed</h3>
        <div className="space-y-1 max-h-40 overflow-y-auto observatory-scroll">
          <div className="text-[10px] font-mono text-[var(--text-dim)]">
            No recent events
          </div>
        </div>
      </div>
    </aside>
  );
}
