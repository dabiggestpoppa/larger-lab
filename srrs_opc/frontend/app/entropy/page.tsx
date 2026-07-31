"use client";

import { useTopologyStore } from "../stores/topologyStore";

export default function EntropyPage() {
  const { nodes } = useTopologyStore();

  const entropyData = nodes.map((n) => ({
    id: n.id,
    label: n.label,
    entropy: n.entropy,
    status: n.status,
  })).sort((a, b) => b.entropy - a.entropy);

  const maxEntropy = Math.max(...entropyData.map((d) => d.entropy), 0.01);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          ENTROPY FIELD VIEW
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {nodes.length} observers
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto observatory-scroll">
        {/* Entropy bars */}
        <div className="space-y-2">
          {entropyData.map((d) => (
            <div key={d.id} className="flex items-center gap-3">
              <span className="text-[10px] font-mono text-[var(--text-secondary)] w-24 truncate">
                {d.label}
              </span>
              <div className="flex-1 h-3 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${(d.entropy / maxEntropy) * 100}%`,
                    backgroundColor: d.entropy > 0.7 ? "var(--field-danger)" :
                      d.entropy > 0.4 ? "var(--field-warning)" : "var(--field-stable)"
                  }}
                />
              </div>
              <span className="text-[10px] font-mono text-[var(--text-muted)] w-12 text-right">
                {(d.entropy * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 p-4 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
          <h3 className="text-[10px] font-mono text-[var(--text-muted)] uppercase mb-2">Field Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Global Entropy</span>
              <p className="text-sm font-mono text-[var(--text-primary)]">
                {(entropyData.reduce((sum, d) => sum + d.entropy, 0) / entropyData.length * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">High Entropy</span>
              <p className="text-sm font-mono text-[var(--field-danger)]">
                {entropyData.filter((d) => d.entropy > 0.7).length}
              </p>
            </div>
            <div>
              <span className="text-[10px] font-mono text-[var(--text-muted)]">Stable</span>
              <p className="text-sm font-mono text-[var(--field-stable)]">
                {entropyData.filter((d) => d.entropy < 0.3).length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
