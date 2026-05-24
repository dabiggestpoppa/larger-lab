"use client";

import { useTopologyStore } from "../stores/topologyStore";

const modes = [
  { id: "topology", label: "Topology", icon: "◉" },
  { id: "entropy", label: "Entropy", icon: "▦" },
  { id: "repair", label: "Repair", icon: "◈" },
  { id: "sync", label: "Sync", icon: "◎" },
  { id: "routing", label: "Routing", icon: "▣" },
] as const;

export default function ViewModeSelector() {
  const { viewMode, setViewMode } = useTopologyStore();

  return (
    <div className="flex items-center gap-1">
      {modes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => setViewMode(mode.id)}
          className={`flex items-center gap-1 px-2 py-1 text-[10px] font-mono rounded transition-colors ${
            viewMode === mode.id
              ? "bg-[var(--bg-elevated)] text-[var(--field-active)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
          }`}
        >
          <span>{mode.icon}</span>
          {mode.label}
        </button>
      ))}
    </div>
  );
}
