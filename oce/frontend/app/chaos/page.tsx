"use client";

import { useSessionStore } from "@/stores/sessionStore";

export default function ChaosPage() {
  const sessions = useSessionStore((s) => s.sessions);
  const chaosSessions = sessions.filter((s) => s.type === "chaos" || s.type === "semantic");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-text-primary">Chaos Testing</h1>
        <p className="text-xs text-text-secondary mt-1">Chaos engineering and semantic test monitoring</p>
      </div>

      {/* Phase 11.4.1+11.4.2 Semantic Test Results */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Phase 11.4.1 — Memory Contradiction Injection</h2>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[
            { label: "SDI", value: "0.0000", threshold: "< 0.15", pass: true },
            { label: "RIS", value: "1.0000", threshold: "> 0.92", pass: true },
            { label: "OCS", value: "0.9500", threshold: "> 0.85", pass: true },
            { label: "APS", value: "1.0000", threshold: ">= 1.0", pass: true },
          ].map((m) => (
            <div key={m.label} className="p-3 rounded-lg bg-bg-tertiary text-center">
              <div className="text-xs text-text-muted">{m.label}</div>
              <div className={`text-lg font-bold ${m.pass ? "text-accent-success" : "text-accent-danger"}`}>{m.value}</div>
              <div className="text-xs text-text-muted">threshold: {m.threshold}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "FAR", value: "0.0000", threshold: "< 0.05", pass: true },
            { label: "RVA", value: "1.0000", threshold: "> 0.95", pass: true },
            { label: "SIS", value: "1.0000", threshold: "> 0.90", pass: true },
            { label: "TVT", value: "0.0000", threshold: "< 45s", pass: true },
          ].map((m) => (
            <div key={m.label} className="p-3 rounded-lg bg-bg-tertiary text-center">
              <div className="text-xs text-text-muted">{m.label}</div>
              <div className={`text-lg font-bold ${m.pass ? "text-accent-success" : "text-accent-danger"}`}>{m.value}</div>
              <div className="text-xs text-text-muted">threshold: {m.threshold}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Test Categories */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Contradiction Test Categories</h2>
        <div className="space-y-2">
          {[
            { id: "1A", name: "Simple Goal Conflict", result: "PASS", detail: "divergence=1.0, detected, anchors intact" },
            { id: "1B", name: "Authority Conflict", result: "PASS", detail: "resolution <1s, consensus 95%" },
            { id: "1C", name: "Temporal Memory Conflict", result: "PASS", detail: "impossible transition detected" },
            { id: "1D", name: "False Event History", result: "PASS", detail: "all 3 fabricated events rejected" },
            { id: "1E", name: "Observer Split Memory", result: "PASS", detail: "divergence detected, convergence achieved" },
            { id: "2A", name: "False Health Report", result: "PASS", detail: "rejected (heartbeat stale)" },
            { id: "2B", name: "False Memory Recovery", result: "PASS", detail: "rejected (vector index corrupted)" },
            { id: "2C", name: "False Topology Stability", result: "PASS", detail: "rejected (consensus unstable)" },
            { id: "2D", name: "False Event Fabric Recovery", result: "PASS", detail: "rejected (streams fragmented)" },
          ].map((test) => (
            <div key={test.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg-tertiary transition-colors">
              <span className="badge badge-success text-xs w-10 text-center">{test.result}</span>
              <span className="text-xs font-medium text-text-primary w-8">{test.id}</span>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-text-primary">{test.name}</div>
                <div className="text-xs text-text-muted">{test.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chaos Sessions */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-text-primary mb-3">Chaos Sessions</h2>
        <div className="space-y-2">
          {chaosSessions.map((session) => (
            <div key={session.id} className="flex items-center gap-3 p-3 rounded-lg border border-border-light">
              <span className={`badge badge-${session.status === "running" ? "info" : session.status === "completed" ? "success" : "danger"}`}>
                {session.status}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-text-primary">{session.name}</div>
                <div className="text-xs text-text-muted">{session.type} · {session.cycles} cycles · amp {session.amplification}x</div>
              </div>
              <div className="text-xs text-text-secondary">{session.passRate}% pass</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
