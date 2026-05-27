"""
O-4-F2: WorkflowEvolution
==========================
Workflow pattern evolution display.
*/

"use client";

import { useLearningStore } from "@/stores/learningStore";

export default function WorkflowEvolution() {
  const patterns = useLearningStore((s) => s.workflowPatterns);

  if (patterns.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Workflow Evolution</h3>
        <p className="text-xs text-gray-600 italic">No workflow patterns extracted yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Workflow Patterns ({patterns.length})
      </h3>
      <div className="space-y-2">
        {patterns.map((pattern) => (
          <div key={pattern.id} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-medium text-gray-300">{pattern.domain}</span>
              <div className="flex gap-2">
                <span className="text-xs text-gray-500">×{pattern.frequency}</span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    pattern.successRate >= 0.8
                      ? "bg-green-900/50 text-green-300"
                      : pattern.successRate >= 0.5
                      ? "bg-yellow-900/50 text-yellow-300"
                      : "bg-red-900/50 text-red-300"
                  }`}
                >
                  {(pattern.successRate * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="flex gap-1 flex-wrap">
              {pattern.sequence.map((step, i) => (
                <span key={i} className="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">
                  {step}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
