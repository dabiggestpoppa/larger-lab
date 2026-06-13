"use client";

import { useEffect } from "react";
import ObservatoryCanvas from "./ObservatoryCanvas";
import { useTopologyStore } from "../../stores/topologyStore";

const VIEW_MODES = [
  { id: "topology", label: "TOPOLOGY" },
  { id: "entropy", label: "ENTROPY" },
  { id: "repair", label: "REPAIR" },
  { id: "sync", label: "SYNC" },
  { id: "routing", label: "ROUTING" },
] as const;

export default function TopologyPage() {
  const { viewMode, setViewMode, fetchTopology, isLoading, nodes, lastFetch } = useTopologyStore();

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000);
    return () => clearInterval(interval);
  }, [fetchTopology]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
            TOPOLOGY OBSERVATORY
          </h2>
          <span className="text-[10px] font-mono text-gray-500">
            {nodes.length} nodes | {isLoading ? "loading..." : lastFetch ? `updated ${new Date(lastFetch).toLocaleTimeString()}` : "not loaded"}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            {VIEW_MODES.map((mode) => (
              <button key={mode.id} onClick={() => setViewMode(mode.id)}
                className={`text-[10px] font-mono px-2 py-1 rounded ${viewMode === mode.id ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"}`}>
                {mode.label}
              </button>
            ))}
          </div>
          <button onClick={() => fetchTopology()} className="text-[10px] font-mono text-blue-400 hover:underline">↻ REFRESH</button>
        </div>
      </div>
      <div className="flex-1 relative">
        <ObservatoryCanvas />
      </div>
    </div>
  );
}