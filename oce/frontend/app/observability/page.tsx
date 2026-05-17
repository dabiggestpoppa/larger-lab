"use client";

import { useState } from "react";
import { MetricsPanel } from "../components/MetricsPanel";
import { TraceView } from "../components/TraceView";
import { AlertPanel } from "../components/AlertPanel";
import { SystemMap } from "../components/SystemMap";
import { Activity, GitBranch, Bell, Network, LayoutDashboard } from "lucide-react";

type Tab = "overview" | "metrics" | "traces" | "alerts" | "topology";

const tabs: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "metrics", label: "Metrics", icon: Activity },
  { id: "traces", label: "Traces", icon: GitBranch },
  { id: "alerts", label: "Alerts", icon: Bell },
  { id: "topology", label: "Topology", icon: Network },
];

export default function ObservabilityPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Observability</h1>
        <p className="text-sm text-gray-500 mt-1">
          Real-time system monitoring, event tracing, and alerting for the Operator Continuity Engine
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-[#111118] border border-[#27272a] rounded-lg p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                isActive
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                  : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="lg:col-span-2">
            <MetricsPanel />
          </div>
          <AlertPanel />
          <SystemMap />
        </div>
      )}

      {activeTab === "metrics" && <MetricsPanel />}
      {activeTab === "traces" && <TraceView />}
      {activeTab === "alerts" && <AlertPanel />}
      {activeTab === "topology" && <SystemMap />}
    </div>
  );
}
