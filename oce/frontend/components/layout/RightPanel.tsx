"use client";

import { useTopologyStore } from "@/stores/topologyStore";

export default function RightPanel() {
  const { nodes, selectedObserverId, selectObserver } = useTopologyStore();
  const selectedObserver = nodes.find((n) => n.id === selectedObserverId) || null;

  return (
    <aside
      className="flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto"
      style={{ width: "var(--right-panel-width, 240px)" }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)] uppercase tracking-wider">
          Inspector
        </h2>
      </div>

      {/* Observer Selector */}
      <div className="px-4 py-2 border-b border-[var(--border-subtle)]">
        <select
          value={selectedObserverId || ""}
          onChange={(e) => selectObserver(e.target.value || null)}
          className="w-full text-[10px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded px-2 py-1"
        >
          <option value="">Select Observer...</option>
          {nodes.map((node) => (
            <option key={node.id} value={node.id}>
              {node.id} ({node.type})
            </option>
          ))}
        </select>
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
              selectedObserver.status === "degraded" ? "text-[var(--observer-degraded)]" :
              "text-[var(--observer-dormant)]"
            }`}>
              {selectedObserver.status}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Entropy</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{(selectedObserver.entropy * 100).toFixed(1)}%</p>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <p className="text-[10px] font-mono text-[var(--text-dim)]">No observer selected</p>
        </div>
      )}
    </aside>
  );
}