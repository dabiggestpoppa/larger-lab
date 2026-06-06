"use client";

import { useEffect, useState } from "react";
import { useResearchStore } from "@/stores/researchStore";

const STATUS_BADGES: Record<string, string> = {
  pending: "badge-neutral",
  running: "badge-warning",
  completed: "badge-success",
  failed: "badge-danger",
  abandoned: "badge-neutral",
};

export default function ResearchAgentsPage() {
  const {
    agents, agentLoading, agentError,
    gaps, gapLoading,
    fetchAgents, fetchGaps, spawnAgent,
  } = useResearchStore();

  const [query, setQuery] = useState("");
  const [spawning, setSpawning] = useState(false);

  useEffect(() => {
    fetchAgents();
    fetchGaps();
  }, [fetchAgents, fetchGaps]);

  const handleSpawn = async () => {
    if (!query.trim()) return;
    setSpawning(true);
    await spawnAgent(query.trim());
    setQuery("");
    setSpawning(false);
  };

  const runningCount = agents.filter((a) => a.status === "running").length;
  const pendingCount = agents.filter((a) => a.status === "pending").length;
  const completedCount = agents.filter((a) => a.status === "completed").length;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-lg font-bold text-[var(--text-primary)]">Research Agents</h1>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Autonomous research agents spawned on detected knowledge gaps
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card p-3">
          <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Total</div>
          <div className="text-lg font-mono font-bold text-[var(--text-primary)] mt-1">{agents.length}</div>
        </div>
        <div className="card p-3">
          <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Running</div>
          <div className="text-lg font-mono font-bold text-[var(--accent-warning)] mt-1">{runningCount}</div>
        </div>
        <div className="card p-3">
          <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Pending</div>
          <div className="text-lg font-mono font-bold text-[var(--text-primary)] mt-1">{pendingCount}</div>
        </div>
        <div className="card p-3">
          <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Completed</div>
          <div className="text-lg font-mono font-bold text-[var(--accent-success)] mt-1">{completedCount}</div>
        </div>
      </div>

      {/* Manual spawn */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Spawn Research Agent</h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSpawn()}
            placeholder="Research query (e.g., 'graph neural networks for multi-agent orchestration')"
            className="flex-1 input text-xs"
          />
          <button
            onClick={handleSpawn}
            disabled={spawning || !query.trim()}
            className="btn-primary text-xs px-4 py-2"
          >
            {spawning ? "Spawning..." : "Spawn"}
          </button>
        </div>
      </div>

      {/* Knowledge Gaps */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
          Detected Knowledge Gaps
        </h2>
        {gapLoading && <div className="text-xs text-[var(--text-muted)]">Loading...</div>}
        {gaps.length === 0 && !gapLoading && (
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No gaps detected yet. Run gap detection after ingestion.
          </div>
        )}
        <div className="space-y-2">
          {gaps.map((gap) => (
            <div key={gap.id} className="flex items-center justify-between p-2 bg-[var(--bg-tertiary)] rounded">
              <div>
                <div className="text-xs text-[var(--text-primary)]">{gap.concept}</div>
                <div className="text-[10px] text-[var(--text-muted)]">{gap.domain} · {gap.reason}</div>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {(gap.score * 100).toFixed(0)}%
                </div>
                <button
                  onClick={() => { setQuery(gap.concept); }}
                  className="text-[10px] text-[var(--accent-primary)] hover:underline"
                >
                  Research
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent list */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Agent Queue</h2>
        {agentLoading && <div className="text-xs text-[var(--text-muted)]">Loading...</div>}
        {agentError && <div className="text-xs text-[var(--accent-danger)]">{agentError}</div>}
        {agents.length === 0 && !agentLoading && (
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No research agents yet. Spawn one above or wait for autonomous gap detection.
          </div>
        )}
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.task_id} className="flex items-center justify-between p-3 bg-[var(--bg-tertiary)] rounded border border-[var(--border-default)]">
              <div className="flex-1 min-w-0">
                <div className="text-xs text-[var(--text-primary)] truncate">{agent.query}</div>
                <div className="text-[10px] text-[var(--text-muted)] mt-1 font-mono">
                  {agent.task_id.slice(0, 12)} · priority={agent.priority}
                  {agent.confidence > 0 && ` · confidence=${agent.confidence.toFixed(2)}`}
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className={`badge ${STATUS_BADGES[agent.status] || "badge-neutral"}`}>
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
