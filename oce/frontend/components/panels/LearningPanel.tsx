"use client";

import { useState } from "react";

interface LearningMetric {
  name: string;
  value: number;
  trend: "up" | "down" | "stable";
  unit: string;
}

interface PatternEntry {
  id: string;
  pattern: string;
  confidence: number;
  occurrences: number;
  lastSeen: string;
}

const mockMetrics: LearningMetric[] = [
  { name: "Routing Accuracy", value: 0.94, trend: "up", unit: "%" },
  { name: "Failure Prediction", value: 0.87, trend: "up", unit: "%" },
  { name: "Workflow Efficiency", value: 0.78, trend: "stable", unit: "%" },
  { name: "Adaptation Rate", value: 0.65, trend: "up", unit: "/hr" },
];

const mockPatterns: PatternEntry[] = [
  { id: "pat-001", pattern: "entropy_spike → repair_trigger", confidence: 0.92, occurrences: 47, lastSeen: "2026-05-28T08:45:00Z" },
  { id: "pat-002", pattern: "consensus_failure → retry_with_quorum+1", confidence: 0.88, occurrences: 23, lastSeen: "2026-05-28T07:30:00Z" },
  { id: "pat-003", pattern: "spawn_timeout → reduce_context_50%", confidence: 0.81, occurrences: 15, lastSeen: "2026-05-28T06:15:00Z" },
  { id: "pat-004", pattern: "memory_drift → checkpoint_rollback", confidence: 0.76, occurrences: 9, lastSeen: "2026-05-28T05:00:00Z" },
];

export default function LearningPanel() {
  const [metrics] = useState<LearningMetric[]>(mockMetrics);
  const [patterns] = useState<PatternEntry[]>(mockPatterns);
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);

  const trendIcon = (trend: string) => {
    switch (trend) {
      case "up": return "↑";
      case "down": return "↓";
      default: return "→";
    }
  };

  const trendColor = (trend: string) => {
    switch (trend) {
      case "up": return "text-[var(--accent-success)]";
      case "down": return "text-[var(--accent-danger)]";
      default: return "text-[var(--text-muted)]";
    }
  };

  const confidenceColor = (conf: number) => {
    if (conf >= 0.9) return "text-[var(--accent-success)]";
    if (conf >= 0.7) return "text-[var(--accent-warning)]";
    return "text-[var(--accent-danger)]";
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h3 className="text-xs font-mono font-bold text-[var(--text-primary)]">FIELD LEARNING</h3>
        <p className="text-[10px] text-[var(--text-muted)] mt-1">O-4 Learning Metrics — {patterns.length} patterns</p>
      </div>

      <div className="flex-1 p-3 overflow-y-auto space-y-4">
        {/* Metrics */}
        <div>
          <h4 className="text-[10px] font-mono text-[var(--text-muted)] uppercase mb-2">Metrics</h4>
          <div className="grid grid-cols-2 gap-2">
            {metrics.map((m) => (
              <div key={m.name} className="p-2 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-subtle)]">
                <span className="text-[10px] font-mono text-[var(--text-muted)]">{m.name}</span>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-sm font-mono text-[var(--text-primary)]">
                    {m.unit === "%" ? `${(m.value * 100).toFixed(0)}%` : m.value.toFixed(2)}
                  </span>
                  <span className={`text-[10px] font-mono ${trendColor(m.trend)}`}>{trendIcon(m.trend)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Patterns */}
        <div>
          <h4 className="text-[10px] font-mono text-[var(--text-muted)] uppercase mb-2">Learned Patterns</h4>
          <div className="space-y-2">
            {patterns.map((pat) => (
              <div
                key={pat.id}
                onClick={() => setSelectedPattern(selectedPattern === pat.id ? null : pat.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedPattern === pat.id
                    ? "bg-[var(--bg-tertiary)] border-[var(--accent-primary)]"
                    : "bg-[var(--bg-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[var(--text-primary)] truncate flex-1">{pat.pattern}</span>
                  <span className={`text-[10px] font-mono ml-2 ${confidenceColor(pat.confidence)}`}>
                    {(pat.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                {selectedPattern === pat.id && (
                  <div className="mt-2 space-y-1 text-[10px] font-mono">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">Occurrences</span>
                      <span className="text-[var(--text-primary)]">{pat.occurrences}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-muted)]">Last Seen</span>
                      <span className="text-[var(--text-primary)]">{new Date(pat.lastSeen).toLocaleTimeString()}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}