"""
O-4-F4: FailureAnalysisPanel
=============================
Failure analysis display.
*/

"use client";

import { useLearningStore } from "@/stores/learningStore";

export default function FailureAnalysisPanel() {
  const failures = useLearningStore((s) => s.failures);
  const resolveFailure = useLearningStore((s) => s.resolveFailure);

  const typeColors: Record<string, string> = {
    routing: "bg-purple-900/50 text-purple-300",
    entropy: "bg-yellow-900/50 text-yellow-300",
    topology: "bg-cyan-900/50 text-cyan-300",
    repair: "bg-orange-900/50 text-orange-300",
    context: "bg-red-900/50 text-red-300",
  };

  if (failures.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Failure Analysis</h3>
        <p className="text-xs text-gray-600 italic">No failures recorded. System healthy.</p>
      </div>
    );
  }

  const unresolved = failures.filter((f) => !f.resolved);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold text-gray-200">
          Failures ({unresolved.length} unresolved)
        </h3>
        <span className="text-xs text-gray-500">{failures.length} total</span>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {failures.map((failure) => (
          <div
            key={failure.id}
            className={`flex items-center justify-between bg-gray-800/50 rounded px-3 py-2 ${
              failure.resolved ? "opacity-50" : ""
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`text-xs px-1.5 py-0.5 rounded ${
                  typeColors[failure.type] || "bg-gray-700 text-gray-300"
                }`}
              >
                {failure.type}
              </span>
              <span className="text-xs text-gray-400">{failure.description}</span>
            </div>
            {!failure.resolved && (
              <button
                onClick={() => resolveFailure(failure.id)}
                className="text-xs text-green-400 hover:text-green-300 shrink-0"
              >
                Resolve
              </button>
            )}
            {failure.resolved && (
              <span className="text-xs text-green-600 shrink-0">✓</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
