/**
 * Phase 3 — Experiment Loader
 * Load experiment sessions for replay.
 */
"use client";

import { useState } from "react";

interface ExperimentSession {
  id: string;
  name: string;
  timestamp: string;
  duration: number;
  frameCount: number;
  status: "complete" | "running" | "failed";
}

export default function ExperimentLoader({ onLoad }: { onLoad: (session: ExperimentSession) => void }) {
  const [sessions, setSessions] = useState<ExperimentSession[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/experiments/sessions");
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {
      // Demo data
      setSessions([
        { id: "exp_001", name: "Chaos 20x Test", timestamp: new Date().toISOString(), duration: 3600, frameCount: 1200, status: "complete" },
        { id: "exp_002", name: "Memory Contradiction", timestamp: new Date().toISOString(), duration: 600, frameCount: 200, status: "complete" },
        { id: "exp_003", name: "Adversarial Drift", timestamp: new Date().toISOString(), duration: 1800, frameCount: 600, status: "complete" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900/80 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-gray-300">Experiment Sessions</h3>
        <button onClick={loadSessions} disabled={loading}
          className="text-xs px-2 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50">
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {sessions.length === 0 ? (
        <p className="text-xs text-gray-500">No sessions found. Click refresh to load.</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => onLoad(s)}
              className="w-full text-left p-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-600 transition-colors"
            >
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-200">{s.name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  s.status === "complete" ? "bg-green-600/30 text-green-400" :
                  s.status === "running" ? "bg-amber-600/30 text-amber-400" :
                  "bg-red-600/30 text-red-400"
                }`}>
                  {s.status}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {s.frameCount} frames • {(s.duration / 60).toFixed(0)}min • {new Date(s.timestamp).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
