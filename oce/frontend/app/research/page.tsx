"use client";

import { useEffect, useState } from "react";
import { useResearchStore } from "@/stores/researchStore";
import Link from "next/link";

const DOMAINS = [
  "agent_orchestration",
  "memory_systems",
  "distributed_cognition",
  "knowledge_graphs",
  "vector_retrieval",
  "reinforcement_learning",
  "attention_mechanisms",
  "inference_optimization",
  "llm_systems",
  "market_microstructure",
  "topology_network_theory",
  "entropy_systems",
  "causal_inference",
  "graph_neural_networks",
  "self_supervised_learning",
];

export default function ResearchHubPage() {
  const {
    papers, paperLoading, paperError, paperQuery, paperDomain,
    stats, agents, doctrine,
    setPaperQuery, setPaperDomain,
    fetchPapers, fetchStats, fetchAgents, fetchDoctrine, triggerIngest,
  } = useResearchStore();

  const [ingestDomains, setIngestDomains] = useState<string[]>([]);
  const [ingestRunning, setIngestRunning] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchAgents();
    fetchDoctrine();
  }, [fetchStats, fetchAgents, fetchDoctrine]);

  const handleSearch = () => {
    fetchPapers(paperQuery, paperDomain);
  };

  const handleIngest = async () => {
    setIngestRunning(true);
    await triggerIngest(ingestDomains.length > 0 ? ingestDomains : undefined);
    setIngestRunning(false);
    fetchStats();
  };

  const toggleDomain = (d: string) => {
    setIngestDomains((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-[var(--text-primary)]">Research Hub</h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Sovereign research mesh — autonomous ingestion, distillation, and agent loops
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/research/graph"
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Knowledge Graph
          </Link>
          <Link
            href="/research/doctrine"
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Doctrine Library
          </Link>
          <Link
            href="/research/agents"
            className="btn-secondary text-xs px-3 py-1.5"
          >
            Research Agents
          </Link>
        </div>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Papers</div>
            <div className="text-lg font-mono font-bold text-[var(--text-primary)] mt-1">
              {stats.papers_ingested}
            </div>
          </div>
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Distilled</div>
            <div className="text-lg font-mono font-bold text-[var(--accent-success)] mt-1">
              {stats.papers_distilled}
            </div>
          </div>
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Graph</div>
            <div className="text-lg font-mono font-bold text-[var(--text-primary)] mt-1">
              {stats.graph_nodes} nodes
            </div>
          </div>
          <div className="card p-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Agents</div>
            <div className="text-lg font-mono font-bold text-[var(--text-primary)] mt-1">
              {stats.agents_spawned}
            </div>
          </div>
        </div>
      )}

      {/* Manual Ingest */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Manual Ingestion</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {DOMAINS.map((d) => (
            <button
              key={d}
              onClick={() => toggleDomain(d)}
              className={`text-[10px] px-2 py-1 rounded border font-mono ${
                ingestDomains.includes(d)
                  ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)]"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <button
          onClick={handleIngest}
          disabled={ingestRunning}
          className="btn-primary text-xs px-4 py-2"
        >
          {ingestRunning ? "Ingesting..." : "Trigger Ingestion"}
        </button>
      </div>

      {/* Paper Search */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Paper Search</h2>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={paperQuery}
            onChange={(e) => setPaperQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search papers..."
            className="flex-1 input text-xs"
          />
          <select
            value={paperDomain}
            onChange={(e) => setPaperDomain(e.target.value)}
            className="input text-xs w-48"
          >
            <option value="">All domains</option>
            {DOMAINS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <button onClick={handleSearch} className="btn-primary text-xs px-4">
            Search
          </button>
        </div>

        {paperLoading && <div className="text-xs text-[var(--text-muted)]">Loading...</div>}
        {paperError && <div className="text-xs text-[var(--accent-danger)]">{paperError}</div>}

        <div className="space-y-2 max-h-96 overflow-y-auto">
          {papers.map((p) => (
            <div key={p.id} className="p-3 bg-[var(--bg-tertiary)] rounded border border-[var(--border-default)]">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-[var(--text-primary)] truncate">
                    {p.title}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] mt-1">
                    {p.year} · {p.source} · {p.citation_count} citations
                  </div>
                </div>
                {p.doi && (
                  <a
                    href={`https://doi.org/${p.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-[var(--accent-primary)] ml-2 shrink-0"
                  >
                    DOI ↗
                  </a>
                )}
              </div>
            </div>
          ))}
          {papers.length === 0 && !paperLoading && (
            <div className="text-xs text-[var(--text-muted)] text-center py-4">
              No papers yet. Trigger ingestion to begin.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
