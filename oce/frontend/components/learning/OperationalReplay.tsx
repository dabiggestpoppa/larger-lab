"""
O-4-F1: OperationalReplay
==========================
Orchestration history replay panel.
*/

"use client";

import { useLearningStore } from "@/stores/learningStore";

export default function OperationalReplay() {
  const traces = useLearningStore((s) => s.traces);
  const isReplaying = useLearningStore((s) => s.isReplaying);
  const replayIndex = useLearningStore((s) => s.replayIndex);
  const setReplaying = useLearningStore((s) => s.setReplaying);
  const setReplayIndex = useLearningStore((s) => s.setReplayIndex);

  const handleReplay = () => {
    if (traces.length === 0) return;
    setReplaying(true);
    setReplayIndex(0);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      if (i >= traces.length) {
        clearInterval(interval);
        setReplaying(false);
        setReplayIndex(0);
      } else {
        setReplayIndex(i);
      }
    }, 500);
  };

  const typeColors: Record<string, string> = {
    task: "bg-blue-900/50 text-blue-300",
    routing: "bg-purple-900/50 text-purple-300",
    failure: "bg-red-900/50 text-red-300",
    entropy: "bg-yellow-900/50 text-yellow-300",
    spawn: "bg-green-900/50 text-green-300",
    topology: "bg-cyan-900/50 text-cyan-300",
    repair: "bg-orange-900/50 text-orange-300",
    consensus: "bg-indigo-900/50 text-indigo-300",
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-200">Operational Replay</h3>
        <button
          onClick={handleReplay}
          disabled={isReplaying || traces.length === 0}
          className="text-xs px-3 py-1 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded transition-colors"
        >
          {isReplaying ? "Replaying..." : "Replay"}
        </button>
      </div>

      {isReplaying && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Step {replayIndex + 1}/{traces.length}</span>
            <span>{traces[replayIndex]?.type}</span>
          </div>
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${((replayIndex + 1) / traces.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {traces.length === 0 ? (
        <p className="text-xs text-gray-600 italic">No traces recorded yet.</p>
      ) : (
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {traces.map((trace, i) => (
            <div
              key={trace.id}
              className={`flex items-center gap-2 text-xs rounded px-2 py-1.5 transition-colors ${
                isReplaying && i === replayIndex
                  ? "bg-blue-900/30 border border-blue-700"
                  : "bg-gray-800/50"
              }`}
            >
              <span className="text-gray-600 font-mono shrink-0 w-6">
                {i + 1}
              </span>
              <span
                className={`shrink-0 px-1.5 py-0.5 rounded text-xs ${
                  typeColors[trace.type] || "bg-gray-700 text-gray-300"
                }`}
              >
                {trace.type}
              </span>
              <span className="text-gray-400 truncate">
                {JSON.stringify(trace.data).substring(0, 80)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
