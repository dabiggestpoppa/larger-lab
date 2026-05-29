"use client";

import { useState } from "react";
import { useTopologyStore } from "@/stores/topologyStore";
import { useUIStore } from "@/stores/uiStore";
import ConsensusPanel from "../panels/ConsensusPanel";
import SpawnPanel from "../panels/SpawnPanel";
import LearningPanel from "../panels/LearningPanel";

type Layer3Tab = "consensus" | "spawn" | "learning";

export default function RightPanel() {
  const { nodes, selectedObserverId, selectObserver } = useTopologyStore();
  const selectedObserver = nodes.find((n) => n.id === selectedObserverId) || null;
  const activeLayer = useUIStore((s) => s.activeLayer);
  const [activeTab, setActiveTab] = useState<Layer3Tab>("consensus");

  // Layer 3: Show orchestration panels
  if (activeLayer === "layer3") {
    return (
      <aside
        className="flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto"
        style={{ width: "var(--right-panel-width, 280px)" }}
      >
        <div className="flex border-b border-[var(--border-subtle)]">
          {(["consensus", "spawn", "learning"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-2 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                activeTab === tab
                  ? "bg-[var(--bg-tertiary)] text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto">
          {activeTab === "consensus" && <ConsensusPanel />}
          {activeTab === "spawn" && <SpawnPanel />}
          {activeTab === "learning" && <LearningPanel />}
        </div>
      </aside>
    );
  }

  // Layer 1/2: Show observer inspector
  return (
    <aside
      className="flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-secondary)] overflow-y-auto"
      style={{ width: "var(--right-panel-width, 240px)" }}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)] uppercase tracking-wider">
          Inspector
        </h2>
      </div>

      {/* Observer Selector */}
      <div className="px-4 py-2 border-b border-[var(--border-subtle)]">
        <select
          value={selectedObserverId || ""}
          onChange={(e) => selectObserver(e.target.value || null)}
          className="w-full text-[10px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] rounded px-2 py-1"
        >
          <option value="">Select Observer...</option>
          {nodes.map((node) => (
            <option key={node.id} value={node.id}>
              {node.id} ({node.type})
            </option>
          ))}
        </select>
      </div>

      {/* Observer Details */}
      {selectedObserver ? (
        <div className="p-4 space-y-3">
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">ID</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{selectedObserver.id}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Type</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{selectedObserver.type}</p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Status</span>
            <p className={`text-xs font-mono ${
              selectedObserver.status === "active" ? "text-[var(--observer-active)]" :
              selectedObserver.status === "synced" ? "text-[var(--observer-synced)]" :
              selectedObserver.status === "repairing" ? "text-[var(--observer-repairing)]" :
              selectedObserver.status === "degraded" ? "text-[var(--observer-degraded)]" :
              "text-[var(--observer-dormant)]"
            }`}>
              {selectedObserver.status}
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Entropy</span>
            <p className="text-xs font-mono text-[var(--text-primary)]">{(selectedObserver.entropy * 100).toFixed(1)}%</p>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <p className="text-[10px] font-mono text-[var(--text-dim)]">No observer selected</p>
        </div>
      )}
    </aside>
  );
}