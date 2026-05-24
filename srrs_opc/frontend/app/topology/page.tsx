"use client";

import ObservatoryCanvas from "./ObservatoryCanvas";
import ViewModeSelector from "./ViewModeSelector";
import FilterPanel from "./FilterPanel";

export default function TopologyPage() {
  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
            TOPOLOGY OBSERVATORY
          </h2>
        </div>
        <div className="flex items-center gap-4">
          <ViewModeSelector />
          <FilterPanel />
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative">
        <ObservatoryCanvas />
      </div>
    </div>
  );
}
