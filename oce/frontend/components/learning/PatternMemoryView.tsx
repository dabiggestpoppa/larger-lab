"""
O-4-F7: PatternMemoryView
==========================
Stable orchestration patterns display.
*/

"use client";

import { useLearningStore } from "@/stores/learningStore";

export default function PatternMemoryView() {
  const patterns = useLearningStore((s) => s.workflowPatterns);

  if (patterns.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Pattern Memory</h3>
        <p className="text-xs text-gray-600 italic">No stable patterns stored yet.</p>
      </div>
    );
  }

  const sorted = [...patterns].sort((a, b) => b.frequency - a.frequency);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Stable Patterns ({patterns.length})
      </h3>
      <div className="space-y-2">
        {sorted.map((pattern) => (
          <div key={pattern.id} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center mb-1">
              <div className="flex items-center gap-2">
                <span className="text-xs bg-blue-900/50 text-blue-300 px-1.5 py-0.5 rounded">
                  {pattern.domain}
                </span>
                <span className="text-xs text-gray-500">seen {pattern.frequency}×</span>
              </div>
              <span
                className={`text-xs font-mono ${
                  pattern.successRate >= 0.8
                    ? "text-green-400"
                    : pattern.successRate >= 0.5
                    ? "text-yellow-400"
                    : "text-red-400"
                }`}
              >
                {(pattern.successRate * 100).toFixed(0)}% success
              </span>
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
