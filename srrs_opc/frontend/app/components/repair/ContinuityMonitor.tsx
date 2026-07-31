/**
 * Phase 5 — Continuity Monitor
 * Drift scanning dashboard.
 */
"use client";

import { useMemo } from "react";
import { useContinuityStore } from "../../stores/continuityStore";

export default function ContinuityMonitor() {
  const { checkpoints, currentDrift, observerHealth } = useContinuityStore();

  const healthPercent = useMemo(() => {
    if (!observerHealth) return 0;
    const { alive = 0, degraded = 0, dead = 0 } = observerHealth as any;
    const total = Number(alive) + Number(degraded) + Number(dead);
    if (total === 0) return 100;
    return Math.round((alive / total) * 100);
  }, [observerHealth]);

  const driftLevel = useMemo(() => {
    if (currentDrift < 0.2) return { label: "Stable", color: "text-cyan-400", bg: "bg-cyan-500" };
    if (currentDrift < 0.5) return { label: "Warning", color: "text-amber-400", bg: "bg-amber-500" };
    return { label: "Critical", color: "text-red-400", bg: "bg-red-500" };
  }, [currentDrift]);

  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-bold text-gray-300 mb-3">Continuity Monitor</h3>

      {/* Health score */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative w-16 h-16">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="#374151"
              strokeWidth="3"
            />
            <path
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke={healthPercent > 60 ? "#22d3ee" : healthPercent > 30 ? "#fbbf24" : "#ef4444"}
              strokeWidth="3"
              strokeDasharray={`${healthPercent}, 100`}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-gray-200">{healthPercent}%</span>
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-300">System Health</div>
          <div className={`text-xs ${driftLevel.color}`}>
            Drift: {driftLevel.label} ({(currentDrift * 100).toFixed(0)}%)
          </div>
        </div>
      </div>

      {/* Observer health bars */}
      {observerHealth && (
        <div className="space-y-1 mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400" />
            <span className="text-xs text-gray-400">Alive: {observerHealth.alive || 0}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="text-xs text-gray-400">Degraded: {observerHealth.degraded || 0}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-xs text-gray-400">Dead: {observerHealth.dead || 0}</span>
          </div>
        </div>
      )}

      {/* Checkpoint history */}
      {checkpoints.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 font-bold mb-1">Checkpoints</div>
          <div className="flex gap-1">
            {checkpoints.slice(-10).map((cp, i) => (
              <div
                key={i}
                className={`w-3 h-3 rounded-sm ${
                  cp.status === "PASS" ? "bg-green-500" : "bg-red-500"
                }`}
                title={`Drift: ${cp.drift_score?.toFixed(2) || "?"}`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
