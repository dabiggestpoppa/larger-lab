"use client";

import { useTopologyStore } from "../stores/topologyStore";

export default function AttractorsPage() {
  const { nodes, clusters } = useTopologyStore();

  // Group nodes by status as simple "attractor basins"
  const basins = {
    stable: nodes.filter((n) => n.entropy < 0.3 && n.syncScore > 0.8),
    active: nodes.filter((n) => n.status === "active"),
    entropic: nodes.filter((n) => n.entropy > 0.5),
    isolated: nodes.filter((n) => n.status === "dormant" || n.status === "failed"),
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          ATTRACTOR BASIN VIEW
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {clusters.length} clusters detected
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto observatory-scroll">
        {/* Attractor Basins */}
        <div className="space-y-4">
          {Object.entries(basins).map(([name, basinNodes]) => (
            <div key={name} className="p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase">{name}</h3>
                <span className="text-[10px] font-mono text-[var(--text-primary)]">{basinNodes.length} observers</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {basinNodes.map((node) => (
                  <span
                    key={node.id}
                    className="px-2 py-1 text-[10px] font-mono rounded bg-[var(--bg-tertiary)]"
                    style={{
                      color: name === "stable" ? "var(--field-stable)" :
                        name === "entropic" ? "var(--field-danger)" :
                        name === "isolated" ? "var(--observer-dormant)" :
                        "var(--observer-active)"
                    }}
                  >
                    {node.label}
                  </span>
                ))}
                {basinNodes.length === 0 && (
                  <span className="text-[10px] font-mono text-[var(--text-dim)]">None</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
