/**
 * Phase 4 — Collapse Indicator
 * Pre-collapse warning visualization.
 */
"use client";

import { useMemo } from "react";

interface CollapseRisk {
  zone: string;
  score: number;
  factors: string[];
  timeToCollapse: number | null;
}

interface Props {
  risks: CollapseRisk[];
}

export default function CollapseIndicator({ risks }: Props) {
  const critical = useMemo(() => risks.filter((r) => r.score > 0.5), [risks]);
  const warnings = useMemo(() => risks.filter((r) => r.score > 0.3 && r.score <= 0.5), [risks]);

  if (risks.length === 0) return null;

  return (
    <div className="absolute bottom-12 left-4 space-y-2 max-w-xs">
      {critical.map((r) => (
        <div
          key={r.zone}
          className="bg-red-900/80 border border-red-500 rounded-lg px-3 py-2 text-xs animate-pulse"
        >
          <div className="flex items-center gap-2 text-red-300 font-bold">
            <span>⚠</span>
            <span>Collapse Risk: {r.zone}</span>
          </div>
          <div className="text-red-400 mt-1">
            Score: {(r.score * 100).toFixed(0)}%
          </div>
          {r.timeToCollapse && (
            <div className="text-red-400">
              Est. collapse: {(r.timeToCollapse / 1000).toFixed(0)}s
            </div>
          )}
          <div className="text-red-400/70 mt-1 space-y-0.5">
            {r.factors.map((f, i) => (
              <div key={i}>• {f}</div>
            ))}
          </div>
        </div>
      ))}

      {warnings.map((r) => (
        <div
          key={r.zone}
          className="bg-amber-900/60 border border-amber-500 rounded-lg px-3 py-1.5 text-xs"
        >
          <div className="flex items-center gap-2 text-amber-300">
            <span>⚡</span>
            <span>Warning: {r.zone} ({(r.score * 100).toFixed(0)}%)</span>
          </div>
        </div>
      ))}
    </div>
  );
}
