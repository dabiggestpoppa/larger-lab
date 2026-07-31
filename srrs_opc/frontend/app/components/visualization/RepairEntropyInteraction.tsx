/**
 * Phase 4 — Repair ↔ Entropy Interaction
 * Counterforce visualization showing repair vs entropy dynamics.
 */
"use client";

import { useMemo } from "react";
import { RepairEntropyDynamics, RepairEntropyBalance } from "../../lib/repair/RepairEntropyDynamics";

interface Props {
  observers: { zone: string; entropy: number; status: string }[];
  activeRepairs: { zone: string; strength: number }[];
}

export default function RepairEntropyInteraction({ observers, activeRepairs }: Props) {
  const dynamics = useMemo(() => new RepairEntropyDynamics(), []);
  const balances = useMemo(
    () => dynamics.computeBalance(observers, activeRepairs),
    [observers, activeRepairs, dynamics]
  );

  return (
    <div className="absolute top-4 right-4 space-y-1 max-w-[200px]">
      {balances.map((b) => (
        <div
          key={b.zone}
          className={`rounded px-2 py-1 text-xs border ${
            b.netForce > 0.3
              ? "bg-red-900/60 border-red-500/50"
              : b.netForce > 0
              ? "bg-amber-900/60 border-amber-500/50"
              : "bg-cyan-900/60 border-cyan-500/50"
          }`}
        >
          <div className="flex justify-between text-gray-300">
            <span>{b.zone}</span>
            <span>{(b.stability * 100).toFixed(0)}%</span>
          </div>
          {/* Force bar */}
          <div className="mt-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.abs(b.netForce) * 100}%`,
                background: b.netForce > 0 ? "#ef4444" : "#22d3ee",
                marginLeft: b.netForce > 0 ? "50%" : `${50 - Math.abs(b.netForce) * 50}%`,
              }}
            />
          </div>
          <div className="flex justify-between text-gray-500 mt-0.5">
            <span>🔧 {(b.repairForce * 100).toFixed(0)}</span>
            <span>🔥 {(b.entropyForce * 100).toFixed(0)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
