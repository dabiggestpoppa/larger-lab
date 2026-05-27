/* Fixed docstring */

"use client";

import { useObserverStore } from "@/stores/observerStore";

const statusColors: Record<string, string> = {
  healthy: "bg-green-500",
  degraded: "bg-yellow-500",
  recovering: "bg-blue-500",
  failed: "bg-red-500",
};

const statusLabels: Record<string, string> = {
  healthy: "Healthy",
  degraded: "Degraded",
  recovering: "Recovering",
  failed: "Failed",
};

export default function ObserverStatus() {
  const observer = useObserverStore((s) => s.observer);

  return (
    <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <div
          className={`w-2.5 h-2.5 rounded-full ${statusColors[observer.status]} animate-pulse`}
        />
        <span className="text-xs font-medium text-gray-300">
          {statusLabels[observer.status]}
        </span>
      </div>

      {/* Continuity score */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-gray-500">Continuity:</span>
        <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-500"
            style={{ width: `${observer.continuityScore * 100}%` }}
          />
        </div>
        <span className="text-xs text-gray-400">
          {(observer.continuityScore * 100).toFixed(0)}%
        </span>
      </div>

      {/* Active agents */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-gray-500">Agents:</span>
        <span className="text-xs font-mono text-gray-300">
          {observer.activeAgents.length}
        </span>
      </div>

      {/* Request count */}
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-gray-500">Requests:</span>
        <span className="text-xs font-mono text-gray-300">
          {observer.requestCount}
        </span>
      </div>
    </div>
  );
}
