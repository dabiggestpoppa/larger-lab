"use client";

import { useEffect, useState } from "react";
import { usePersistenceStore } from "../../stores/persistenceStore";

export default function LongHorizonTimeline() {
  const { continuitySummary, fetchContinuity } = usePersistenceStore();
  const [memories, setMemories] = useState<Array<{ category: string; importance: number; timestamp: string }>>([]);

  useEffect(() => {
    fetchContinuity();
    // Simulate memory entries for display
    setMemories([
      { category: "workflow", importance: 0.9, timestamp: new Date().toISOString() },
      { category: "orchestration", importance: 0.7, timestamp: new Date(Date.now() - 86400000).toISOString() },
      { category: "repair", importance: 0.5, timestamp: new Date(Date.now() - 172800000).toISOString() },
      { category: "topology", importance: 0.8, timestamp: new Date(Date.now() - 259200000).toISOString() },
    ]);
  }, [fetchContinuity]);

  const categoryColors: Record<string, string> = {
    workflow: "bg-blue-500",
    orchestration: "bg-purple-500",
    repair: "bg-cyan-500",
    topology: "bg-green-500",
    adaptation: "bg-yellow-500",
  };

  return (
    <div className="bg-gray-900/50 rounded p-3 border border-gray-800">
      <div className="text-xs text-gray-500 font-mono mb-3">Long-Horizon Timeline</div>

      {continuitySummary && (
        <div className="mb-3 text-xs font-mono">
          <span className="text-gray-500">Score: </span>
          <span className={continuitySummary.continuity_score > 0.7 ? "text-green-400" : "text-yellow-400"}>
            {continuitySummary.continuity_score.toFixed(2)}
          </span>
          <span className="text-gray-600 ml-2">({continuitySummary.total_records} records)</span>
        </div>
      )}

      <div className="space-y-1">
        {memories.map((mem, i) => (
          <div key={i} className="flex items-center gap-2 text-xs font-mono">
            <div className={`w-1.5 h-1.5 rounded-full ${categoryColors[mem.category] || "bg-gray-500"}`} />
            <span className="text-gray-400 w-20">{mem.category}</span>
            <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full ${categoryColors[mem.category] || "bg-gray-500"}`}
                style={{ width: `${mem.importance * 100}%` }}
              />
            </div>
            <span className="text-gray-600 w-16 text-right">
              {Math.round((Date.now() - new Date(mem.timestamp).getTime()) / 86400000)}d ago
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
