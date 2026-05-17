"use client";

import { useState } from "react";
import { ExecutionMonitor } from "../components/ExecutionMonitor";
import { TaskDetail } from "../components/TaskDetail";
import { ExecutionAnalytics } from "../components/ExecutionAnalytics";
import { Activity, BarChart3, FileText, Play } from "lucide-react";
import { ExecutionTask } from "../lib/api";

type Tab = "monitor" | "analytics" | "submit";

export default function ExecutionPage() {
  const [activeTab, setActiveTab] = useState<Tab>("monitor");
  const [selectedTask, setSelectedTask] = useState<ExecutionTask | null>(null);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-white">Execution</h1>
        <p className="text-sm text-gray-500 mt-1">
          Task execution engine — submit, monitor, and analyze task execution
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-[#111118] border border-[#27272a] rounded-lg p-1">
        <TabButton
          active={activeTab === "monitor"}
          onClick={() => setActiveTab("monitor")}
          icon={Activity}
          label="Monitor"
        />
        <TabButton
          active={activeTab === "analytics"}
          onClick={() => setActiveTab("analytics")}
          icon={BarChart3}
          label="Analytics"
        />
        <TabButton
          active={activeTab === "submit"}
          onClick={() => setActiveTab("submit")}
          icon={Play}
          label="Submit Task"
        />
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {activeTab === "monitor" && <ExecutionMonitor />}
          {activeTab === "analytics" && <ExecutionAnalytics />}
          {activeTab === "submit" && <SubmitTaskForm />}
        </div>

        <div>
          {selectedTask ? (
            <TaskDetail task={selectedTask} onClose={() => setSelectedTask(null)} />
          ) : (
            <div className="bg-[#111118] border border-[#27272a] rounded-lg p-6 text-center">
              <FileText className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Select a task to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon: Icon, label }: {
  active: boolean;
  onClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
        active
          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
          : "text-gray-400 hover:text-gray-200 hover:bg-[#1a1a24]"
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );
}

function SubmitTaskForm() {
  const [taskType, setTaskType] = useState("skill_call");
  const [payload, setPayload] = useState('{"skill_name": "test", "params": {}}');
  const [priority, setPriority] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ task_id: string; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const parsedPayload = JSON.parse(payload);
      const res = await fetch("http://localhost:8000/execution/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: taskType,
          payload: parsedPayload,
          priority,
          source: "dashboard",
        }),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-[#111118] border border-[#27272a] rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Submit Task</h3>

      <div>
        <label className="text-xs text-gray-500 block mb-1">Task Type</label>
        <select
          value={taskType}
          onChange={(e) => setTaskType(e.target.value)}
          className="w-full bg-[#1a1a24] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="skill_call">Skill Call</option>
          <option value="tool_invoke">Tool Invoke</option>
          <option value="pipeline_run">Pipeline Run</option>
          <option value="agent_delegate">Agent Delegate</option>
        </select>
      </div>

      <div>
        <label className="text-xs text-gray-500 block mb-1">Priority</label>
        <select
          value={priority}
          onChange={(e) => setPriority(Number(e.target.value))}
          className="w-full bg-[#1a1a24] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-indigo-500"
        >
          <option value={0}>Low</option>
          <option value={1}>Normal</option>
          <option value={2}>High</option>
          <option value={3}>Critical</option>
        </select>
      </div>

      <div>
        <label className="text-xs text-gray-500 block mb-1">Payload (JSON)</label>
        <textarea
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          rows={6}
          className="w-full bg-[#1a1a24] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-gray-300 font-mono focus:outline-none focus:border-indigo-500 resize-none"
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-medium py-2 rounded-lg"
      >
        {submitting ? "Submitting..." : "Submit Task"}
      </button>

      {result && (
        <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3">
          <p className="text-xs text-green-400">Task submitted successfully</p>
          <p className="text-xs text-gray-400 font-mono mt-1">ID: {result.task_id}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
}
