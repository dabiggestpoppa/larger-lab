"use client";

import { useState } from "react";

interface Proposal {
  id: string;
  title: string;
  status: "pending" | "approved" | "rejected";
  votes: { agent: string; vote: "yes" | "no" | "abstain" }[];
  quorum: number;
}

const mockProposals: Proposal[] = [
  { id: "prop-001", title: "Scale observer pool to 12", status: "approved", votes: [{ agent: "CC", vote: "yes" }, { agent: "OC2", vote: "yes" }, { agent: "AS", vote: "yes" }, { agent: "PM2", vote: "yes" }], quorum: 4 },
  { id: "prop-002", title: "Enable chaos injection schedule", status: "approved", votes: [{ agent: "CC", vote: "yes" }, { agent: "OC2", vote: "yes" }, { agent: "AS", vote: "abstain" }, { agent: "PM", vote: "yes" }], quorum: 3 },
  { id: "prop-003", title: "Migrate to O-6 Local Substrate", status: "pending", votes: [{ agent: "CC", vote: "yes" }, { agent: "OC2", vote: "yes" }], quorum: 4 },
];

export default function ConsensusPanel() {
  const [proposals] = useState<Proposal[]>(mockProposals);
  const [selectedProp, setSelectedProp] = useState<string | null>(null);

  const statusColor = (status: string) => {
    switch (status) {
      case "approved": return "text-[var(--accent-success)]";
      case "rejected": return "text-[var(--accent-danger)]";
      default: return "text-[var(--accent-warning)]";
    }
  };

  const voteColor = (vote: string) => {
    switch (vote) {
      case "yes": return "text-[var(--accent-success)]";
      case "no": return "text-[var(--accent-danger)]";
      default: return "text-[var(--text-muted)]";
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h3 className="text-xs font-mono font-bold text-[var(--text-primary)]">CONSENSUS ENGINE</h3>
        <p className="text-[10px] text-[var(--text-muted)] mt-1">O-2 Observer Consensus — {proposals.length} proposals</p>
      </div>

      <div className="flex-1 p-3 overflow-y-auto space-y-2">
        {proposals.map((prop) => (
          <div
            key={prop.id}
            onClick={() => setSelectedProp(selectedProp === prop.id ? null : prop.id)}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedProp === prop.id
                ? "bg-[var(--bg-tertiary)] border-[var(--accent-primary)]"
                : "bg-[var(--bg-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[var(--text-primary)]">{prop.title}</span>
              <span className={`text-[10px] font-mono uppercase ${statusColor(prop.status)}`}>{prop.status}</span>
            </div>

            {selectedProp === prop.id && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-[10px] font-mono">
                  <span className="text-[var(--text-muted)]">Quorum:</span>
                  <span className="text-[var(--text-primary)]">{prop.votes.filter(v => v.vote === "yes").length}/{prop.quorum}</span>
                </div>
                <div className="space-y-1">
                  {prop.votes.map((v) => (
                    <div key={v.agent} className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-[var(--text-secondary)]">{v.agent}</span>
                      <span className={voteColor(v.vote)}>{v.vote}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Approved</span>
            <p className="text-sm font-mono text-[var(--accent-success)]">{proposals.filter(p => p.status === "approved").length}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Pending</span>
            <p className="text-sm font-mono text-[var(--accent-warning)]">{proposals.filter(p => p.status === "pending").length}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">Rejected</span>
            <p className="text-sm font-mono text-[var(--accent-danger)]">{proposals.filter(p => p.status === "rejected").length}</p>
          </div>
        </div>
      </div>
    </div>
  );
}