"use client";

import { useState } from "react";
import VaultViewer from "@/components/vault/VaultViewer";
import GraphViz from "@/components/vault/GraphViz";
import { useVaultStore } from "@/stores/vaultStore";

type VaultTab = "notes" | "graph";

export default function VaultPage() {
  const [activeTab, setActiveTab] = useState<VaultTab>("notes");
  const selectedNote = useVaultStore((s) => s.selectedNote);
  const selectedNode = useVaultStore((s) => s.selectedNode);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
            O2C VAULT
          </h2>
          <div className="flex items-center gap-1 ml-4">
            <button
              onClick={() => setActiveTab("notes")}
              className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${
                activeTab === "notes"
                  ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)] hover:text-[var(--text-primary)]"
              }`}
            >
              NOTES
            </button>
            <button
              onClick={() => setActiveTab("graph")}
              className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${
                activeTab === "graph"
                  ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)] hover:text-[var(--text-primary)]"
              }`}
            >
              GRAPH
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {activeTab === "notes" && selectedNote && (
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {selectedNote.title}
            </span>
          )}
          {activeTab === "graph" && selectedNode && (
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {selectedNode.label} ({selectedNode.category})
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "notes" ? (
          <VaultViewer />
        ) : (
          <GraphViz />
        )}
      </div>
    </div>
  );
}
