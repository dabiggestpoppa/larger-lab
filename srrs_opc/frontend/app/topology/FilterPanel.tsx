"use client";

import { useTopologyStore } from "../stores/topologyStore";

export default function FilterPanel() {
  const { filters, setFilter } = useTopologyStore();

  return (
    <div className="flex items-center gap-2">
      {/* Entropy filter */}
      <select
        value={filters.entropyLevel}
        onChange={(e) => setFilter("entropyLevel", e.target.value)}
        className="text-[10px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded px-2 py-1"
      >
        <option value="all">All Entropy</option>
        <option value="low">Low (&lt;0.3)</option>
        <option value="medium">Medium (0.3-0.7)</option>
        <option value="high">High (&gt;0.7)</option>
      </select>

      {/* Status filter */}
      <select
        value={filters.syncState || ""}
        onChange={(e) => setFilter("syncState", e.target.value || null)}
        className="text-[10px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded px-2 py-1"
      >
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="synced">Synced</option>
        <option value="repairing">Repairing</option>
        <option value="dormant">Dormant</option>
        <option value="failed">Failed</option>
      </select>
    </div>
  );
}
