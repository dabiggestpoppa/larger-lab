"use client";

import { useState } from "react";
import ConsensusPanel from "@/components/consensus/ConsensusPanel";
import RoutingMap from "@/components/consensus/RoutingMap";
import SpawnBlueprintView from "@/components/consensus/SpawnBlueprintView";
import ObserverSpecializationMap from "@/components/consensus/ObserverSpecializationMap";
import ConsensusReplayPanel from "@/components/consensus/ConsensusReplayPanel";
import CapabilityInspector from "@/components/consensus/CapabilityInspector";

const tabs = [
  { id: "consensus", label: "Consensus", component: ConsensusPanel },
  { id: "routing", label: "Routing", component: RoutingMap },
  { id: "blueprint", label: "Blueprint", component: SpawnBlueprintView },
  { id: "specialization", label: "Specialization", component: ObserverSpecializationMap },
  { id: "replay", label: "Replay", component: ConsensusReplayPanel },
  { id: "capabilities", label: "Capabilities", component: CapabilityInspector },
];

export default function ConsensusPage() {
  const [activeTab, setActiveTab] = useState("consensus");
  const ActiveComponent = tabs.find((t) => t.id === activeTab)?.component || ConsensusPanel;

  return (
    <div className="flex flex-col h-full">
      {/* Tab Bar */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-border-light bg-bg-secondary overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`text-xs px-3 py-1.5 rounded-md whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? "bg-accent-primary/10 text-accent-primary font-medium"
                : "text-text-secondary hover:bg-bg-tertiary hover:text-text-primary"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <ActiveComponent />
      </div>
    </div>
  );
}
