/**
 * Phase 5 — Repair Engine Visualization
 * Repair detection and coordination display.
 */
"use client";

import { useMemo } from "react";
import { useRepairStore } from "../../stores/repairStore";

interface RepairEvent {
  id: string;
  source: string;
  target: string;
  type: "trigger" | "propagation" | "complete" | "fail";
  timestamp: number;
  strength: number;
}

export default function RepairEngine() {
  const { activeRepairs, completedRepairs, failedRepairs } = useRepairStore();

  const stats = useMemo(() => {
    const total = activeRepairs.length + completedRepairs.length + failedRepairs.length;
    const successRate = total > 0 ? (completedRepairs.length / total) * 100 : 0;
    const avgStrength = activeRepairs.length > 0
      ? activeRepairs.reduce((s, r) => s + r.strength, 0) / activeRepairs.length
      : 0;
    return { total, successRate, avgStrength };
  }, [activeRepairs, completedRepairs, failedRepairs]);

  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-bold text-gray-300 mb-3">Repair Engine</h3>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-gray-800 rounded p-2 text-center">
          <div className="text-lg font-bold text-cyan-400">{activeRepairs.length}</div>
          <div className="text-xs text-gray-500">Active</div>
        </div>
        <div className="bg-gray-800 rounded p-2 text-center">
          <div className="text-lg font-bold text-green-400">{completedRepairs.length}</div>
          <div className="text-xs text-gray-500">Complete</div>
        </div>
        <div className="bg-gray-800 rounded p-2 text-center">
          <div className="text-lg font-bold text-red-400">{failedRepairs.length}</div>
          <div className="text-xs text-gray-500">Failed</div>
        </div>
      </div>

      {/* Success rate bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Success Rate</span>
          <span>{stats.successRate.toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 to-green-500 rounded-full transition-all"
            style={{ width: `${stats.successRate}%` }}
          />
        </div>
      </div>

      {/* Active repairs list */}
      {activeRepairs.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs text-gray-500 font-bold">Active Repairs</div>
          {activeRepairs.slice(0, 5).map((r) => (
            <div key={r.id} className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-gray-300">{r.source} → {r.target}</span>
              <span className="text-gray-500 ml-auto">{(r.strength * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
