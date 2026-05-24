/**
 * Phase 5 — Stabilization Metrics
 * Recovery statistics display.
 */
"use client";

import { useMemo } from "react";
import { useRepairStore } from "../../stores/repairStore";
import { useContinuityStore } from "../../stores/continuityStore";

export default function StabilizationMetrics() {
  const { completedRepairs, failedRepairs, activeRepairs } = useRepairStore();
  const { checkpoints } = useContinuityStore();

  const stats = useMemo(() => {
    const total = completedRepairs.length + failedRepairs.length + activeRepairs.length;
    const successRate = total > 0 ? (completedRepairs.length / total) * 100 : 0;
    const avgRepairStrength = completedRepairs.length > 0
      ? completedRepairs.reduce((s, r) => s + r.strength, 0) / completedRepairs.length
      : 0;

    const passCount = checkpoints.filter((c) => c.status === "PASS").length;
    const failCount = checkpoints.filter((c) => c.status === "FAIL").length;
    const avgDrift = checkpoints.length > 0
      ? checkpoints.reduce((s, c) => s + (c.drift_score || 0), 0) / checkpoints.length
      : 0;

    return { total, successRate, avgRepairStrength, passCount, failCount, avgDrift };
  }, [completedRepairs, failedRepairs, activeRepairs, checkpoints]);

  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-bold text-gray-300 mb-3">Stabilization Metrics</h3>

      <div className="space-y-3">
        {/* Repair success */}
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Repair Success</span>
            <span className="text-cyan-400">{stats.successRate.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-500 rounded-full"
              style={{ width: `${stats.successRate}%` }}
            />
          </div>
        </div>

        {/* Drift trend */}
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Avg Drift</span>
            <span className={stats.avgDrift < 0.3 ? "text-cyan-400" : "text-amber-400"}>
              {(stats.avgDrift * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${stats.avgDrift < 0.3 ? "bg-cyan-500" : "bg-amber-500"}`}
              style={{ width: `${Math.min(100, stats.avgDrift * 200)}%` }}
            />
          </div>
        </div>

        {/* Checkpoint summary */}
        <div className="flex gap-2 text-xs">
          <span className="text-green-400">✓ {stats.passCount}</span>
          <span className="text-red-400">✗ {stats.failCount}</span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">Avg strength: {(stats.avgRepairStrength * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
