
"use client";

import { useState } from "react";

interface ContextPackage {
  objective?: { task_type: string; description: string; success_criteria?: string[] };
  constraints?: { max_turns: number; timeout_seconds: number; allowed_tools: string[]; max_file_writes: number; max_terminal_commands: number };
  environment?: Record<string, unknown>;
  coordination?: { active_agent_count: number; my_role: string; coordination_channel: string };
  history?: Array<{ task_type: string; status: string; key_findings?: string[] }>;
}

export default function ContextInjectionView() {
  const [context] = useState<ContextPackage | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>("objective");

  if (!context) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-600">
        Select a spawned agent to view injected context
      </div>
    );
  }

  const sections = [
    { key: "objective", label: "Objective", data: context.objective },
    { key: "constraints", label: "Constraints", data: context.constraints },
    { key: "environment", label: "Environment", data: context.environment },
    { key: "coordination", label: "Coordination", data: context.coordination },
    { key: "history", label: "History", data: context.history },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Context Injection</h3>
        <span className="text-[10px] text-gray-500">Compressed field state for spawned agent</span>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-gray-700/30">
        {sections.map((section) => (
          <div key={section.key}>
            <button
              onClick={() => setExpandedSection(expandedSection === section.key ? null : section.key)}
              className="w-full flex items-center justify-between px-4 py-2 hover:bg-gray-800/30"
            >
              <span className="text-xs text-gray-300">{section.label}</span>
              <span className="text-[10px] text-gray-600">
                {expandedSection === section.key ? "▼" : "▶"}
              </span>
            </button>
            {expandedSection === section.key && section.data && (
              <div className="px-4 pb-3">
                <pre className="text-[10px] text-gray-400 whitespace-pre-wrap font-mono bg-gray-900/50 rounded p-2 max-h-40 overflow-y-auto">
                  {JSON.stringify(section.data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
