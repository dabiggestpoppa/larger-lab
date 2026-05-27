/* Fixed docstring */

"use client";

import { useState } from "react";

interface ReplayEntry {
  id: string;
  timestamp: string;
  taskDomain: string;
  complexity: string;
  success: boolean;
  routingPath: string;
  durationMs: number;
}

export default function ReplaySummary() {
  const [replays] = useState<ReplayEntry[]>([]);

  if (replays.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">
          Replay Summary
        </h3>
        <p className="text-xs text-gray-600 italic">
          No replays yet. Completed tasks will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Replay Summary
      </h3>
      <div className="space-y-2">
        {replays.map((replay) => (
          <div
            key={replay.id}
            className="bg-gray-800/50 rounded px-3 py-2"
          >
            <div className="flex justify-between items-center">
              <span className="text-xs font-medium text-gray-300">
                {replay.taskDomain}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded ${
                  replay.success
                    ? "bg-green-900/50 text-green-300"
                    : "bg-red-900/50 text-red-300"
                }`}
              >
                {replay.success ? "Success" : "Failed"}
              </span>
            </div>
            <div className="flex gap-2 mt-1 text-xs text-gray-500">
              <span>{replay.complexity}</span>
              <span>•</span>
              <span>{replay.routingPath}</span>
              <span>•</span>
              <span>{replay.durationMs}ms</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
