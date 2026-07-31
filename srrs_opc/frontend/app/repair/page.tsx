"use client";

import { useTopologyStore } from "../stores/topologyStore";

export default function RepairPage() {
  const { nodes, edges } = useTopologyStore();

  const repairEdges = edges.filter((e) => e.type === "repair");
  const repairingNodes = nodes.filter((n) => n.status === "repairing");

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          REPAIR CASCADE VIEWER
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {repairingNodes.length} active repairs
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto observatory-scroll">
        {/* Active Repairs */}
        <div className="space-y-3">
          <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Active Repairs</h3>
          {repairingNodes.length > 0 ? (
            repairingNodes.map((node) => (
              <div key={node.id} className="p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-[var(--observer-repairing)]">{node.label}</span>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">{node.repairState}</span>
                </div>
                <div className="mt-2 h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                  <div className="h-full bg-[var(--observer-repairing)] rounded-full repair-wave" style={{ width: "60%" }} />
                </div>
              </div>
            ))
          ) : (
            <p className="text-[10px] font-mono text-[var(--text-dim)]">No active repairs</p>
          )}
        </div>

        {/* Repair Chains */}
        <div className="mt-6 space-y-3">
          <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Repair Chains</h3>
          {repairEdges.length > 0 ? (
            repairEdges.map((edge, i) => (
              <div key={i} className="flex items-center gap-2 text-[10px] font-mono">
                <span className="text-[var(--observer-repairing)]">{edge.source}</span>
                <span className="text-[var(--text-muted)]">→</span>
                <span className="text-[var(--text-primary)]">{edge.target}</span>
                <span className="text-[var(--text-muted)]">({(edge.strength * 100).toFixed(0)}%)</span>
              </div>
            ))
          ) : (
            <p className="text-[10px] font-mono text-[var(--text-dim)]">No repair chains</p>
          )}
        </div>
      </div>
    </div>
  );
}
