"""
O-4-F3: RoutingLearningMap
===========================
Routing improvement visualization over time.
*/

"use client";

import { useLearningStore } from "@/stores/learningStore";

export default function RoutingLearningMap() {
  const improvements = useLearningStore((s) => s.routingImprovements);

  if (improvements.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Routing Learning</h3>
        <p className="text-xs text-gray-600 italic">No routing improvements recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Routing Improvements ({improvements.length})
      </h3>
      <div className="space-y-2">
        {improvements.map((imp, i) => (
          <div key={i} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="text-xs bg-purple-900/50 text-purple-300 px-1.5 py-0.5 rounded">
                  {imp.domain}
                </span>
                <span className="text-xs text-gray-500">{imp.previousModel}</span>
                <span className="text-xs text-gray-600">→</span>
                <span className="text-xs text-green-400">{imp.currentModel}</span>
              </div>
              <span
                className={`text-xs font-mono ${
                  imp.improvementScore > 0 ? "text-green-400" : "text-red-400"
                }`}
              >
                {imp.improvementScore > 0 ? "+" : ""}
                {(imp.improvementScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
