"use client";

import { useState } from "react";
import Link from "next/link";
import { ExecutionMonitor } from "../components/ExecutionMonitor";
import { TaskDetail } from "../components/TaskDetail";
import { ExecutionAnalytics } from "../components/ExecutionAnalytics";
import { Activity, BarChart3, Play, ChevronRight, Plus } from "lucide-react";
import { ExecutionTask } from "../lib/api";

type Tab = "monitor" | "analytics" | "submit";

const tabs: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "monitor", label: "Monitor", icon: Activity },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "submit", label: "Submit Task", icon: Play },
];

export default function ExecutionPage() {
  const [activeTab, setActiveTab] = useState<Tab>("monitor");
  const [selectedTask, setSelectedTask] = useState<ExecutionTask | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Execution</h1>
          <p className="text-sm text-gray-500 mt-1">Task execution engine — submit, monitor, and analyze</p>
        </div>
        <Link href="/" className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1">
          <ChevronRight className="w-3 h-3 rotate-180" /> Back to Overview
        </Link>
      </div>

      <div className="flex gap-1 bg-[#111118] border border-[#27272a] rounded-lg p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {activeTab === "monitor" && <ExecutionMonitor />}
          {activeTab === "analytics" && <ExecutionAnalytics />}
          {activeTab === "submit" && (
            <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6">
              <h2 className="text-sm font-semibold text-gray-300 mb-4">Submit New Task</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Task Type</label>
                  <select className="w-full bg-[#1a1a24] border border-[#27272a] rounded-md px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500/50">
                    <option>Observer Task</option>
                    <option>Repair Task</option>
                    <option>Memory Consolidation</option>
                    <option>Entropy Compression</option>
                    <option>Custom</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Priority</label>
                  <select className="w-full bg-[#1a1a24] border border-[#27272a] rounded-md px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500/50">
                    <option>Normal</option>
                    <option>High</option>
                    <option>Critical</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Payload (JSON)</label>
                  <textarea
                    rows={6}
                    className="w-full bg-[#1a1a24] border border-[#27272a] rounded-md px-3 py-2 text-sm text-gray-200 font-mono focus:outline-none focus:border-indigo-500/50 resize-none"
                    placeholder='{"action": "observe", "target": "..."}'
                  />
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-md transition-colors">
                  <Plus className="w-4 h-4" /> Submit Task
                </button>
              </div>
            </div>
          )}
        </div>
        <div>
          {selectedTask ? (
            <TaskDetail task={selectedTask} onClose={() => setSelectedTask(null)} />
          ) : (
            <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
              <Activity className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Select a task to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
