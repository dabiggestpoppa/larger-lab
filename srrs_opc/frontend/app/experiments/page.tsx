"use client";

import { useState } from "react";

interface Experiment {
  id: string;
  name: string;
  status: "running" | "complete" | "failed";
  startTime: string;
  perturbations: number;
  recoveryRate: number;
  continuityScore: number;
}

const mockExperiments: Experiment[] = [
  { id: "exp-001", name: "Chaos Amp 3.0x", status: "complete", startTime: "2026-05-23T10:31:00Z", perturbations: 84, recoveryRate: 0.875, continuityScore: 0.92 },
  { id: "exp-002", name: "Memory Contradiction", status: "complete", startTime: "2026-05-23T15:00:00Z", perturbations: 9, recoveryRate: 1.0, continuityScore: 0.95 },
  { id: "exp-003", name: "False Repair Signal", status: "complete", startTime: "2026-05-23T16:00:00Z", perturbations: 4, recoveryRate: 1.0, continuityScore: 0.98 },
  { id: "exp-004", name: "72h Continuity", status: "running", startTime: "2026-05-23T11:20:00Z", perturbations: 0, recoveryRate: 0.0, continuityScore: 0.0 },
];

export default function ExperimentsPage() {
  const [experiments] = useState<Experiment[]>(mockExperiments);
  const [selectedExp, setSelectedExp] = useState<string | null>(null);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          EXPERIMENT SESSION VIEWER
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {experiments.length} experiments
        </span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto observatory-scroll">
        <div className="space-y-3">
          {experiments.map((exp) => (
            <div
              key={exp.id}
              onClick={() => setSelectedExp(selectedExp === exp.id ? null : exp.id)}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedExp === exp.id
                  ? "bg-[var(--bg-elevated)] border-[var(--field-active)]"
                  : "bg-[var(--bg-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    exp.status === "running" ? "bg-[var(--field-warning)] node-pulse" :
                    exp.status === "complete" ? "bg-[var(--field-stable)]" :
                    "bg-[var(--field-danger)]"
                  }`} />
                  <span className="text-xs font-mono text-[var(--text-primary)]">{exp.name}</span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-muted)]">{exp.status}</span>
              </div>

              {selectedExp === exp.id && (
                <div className="mt-3 grid grid-cols-3 gap-4">
                  <div>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">Perturbations</span>
                    <p className="text-xs font-mono text-[var(--text-primary)]">{exp.perturbations}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">Recovery</span>
                    <p className="text-xs font-mono text-[var(--text-primary)]">
                      {exp.recoveryRate > 0 ? `${(exp.recoveryRate * 100).toFixed(1)}%` : "—"}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">Continuity</span>
                    <p className="text-xs font-mono text-[var(--text-primary)]">
                      {exp.continuityScore > 0 ? `${(exp.continuityScore * 100).toFixed(1)}%` : "—"}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
