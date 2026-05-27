"""
O-1-F9: ObserverHealthPanel
============================
Observer health metrics display.
"""

"use client";

import { useObserverStore } from "@/stores/observerStore";

export default function ObserverHealthPanel() {
  const observer = useObserverStore((s) => s.observer);

  const metrics = [
    {
      label: "Health",
      value: observer.status,
      color:
        observer.status === "healthy"
          ? "text-green-400"
          : observer.status === "degraded"
          ? "text-yellow-400"
          : observer.status === "recovering"
          ? "text-blue-400"
          : "text-red-400",
    },
    {
      label: "Continuity",
      value: `${(observer.continuityScore * 100).toFixed(1)}%`,
      color: "text-blue-400",
    },
    {
      label: "Entropy",
      value: observer.entropyState.level.toFixed(3),
      color:
        observer.entropyState.level > 0.7
          ? "text-red-400"
          : observer.entropyState.level > 0.4
          ? "text-yellow-400"
          : "text-green-400",
    },
    {
      label: "Entropy Trend",
      value: observer.entropyState.trend,
      color:
        observer.entropyState.trend === "rising"
          ? "text-red-400"
          : observer.entropyState.trend === "falling"
          ? "text-green-400"
          : "text-gray-400",
    },
    {
      label: "Active Agents",
      value: String(observer.activeAgents.length),
      color: "text-purple-400",
    },
    {
      label: "Repair",
      value: observer.repairState.active ? "Active" : "Idle",
      color: observer.repairState.active ? "text-yellow-400" : "text-gray-500",
    },
  ];

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Observer Health
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="flex justify-between items-center bg-gray-800/50 rounded px-3 py-2"
          >
            <span className="text-xs text-gray-500">{m.label}</span>
            <span className={`text-xs font-mono font-medium ${m.color}`}>
              {m.value}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-3 text-xs text-gray-600">
        Last updated: {observer.lastUpdated || "—"}
      </div>
    </div>
  );
}
