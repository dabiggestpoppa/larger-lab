"""
O-1-F2: ExecutionFeed
======================
Live execution visibility in chat.
"""

"use client";

import { useObserverStore } from "@/stores/observerStore";

export default function ExecutionFeed() {
  const events = useObserverStore((s) => s.events);

  if (events.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">
          Execution Feed
        </h3>
        <p className="text-xs text-gray-600 italic">
          No events yet. Start a task to see execution events.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Execution Feed
      </h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {events.slice(-20).reverse().map((event, i) => (
          <div
            key={i}
            className="flex items-start gap-2 text-xs bg-gray-800/50 rounded px-2 py-1.5"
          >
            <span className="text-gray-600 font-mono shrink-0">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
            <span
              className={`shrink-0 px-1.5 py-0.5 rounded text-xs ${
                event.eventType.includes("failed") || event.eventType.includes("error")
                  ? "bg-red-900/50 text-red-300"
                  : event.eventType.includes("spike") || event.eventType.includes("degraded")
                  ? "bg-yellow-900/50 text-yellow-300"
                  : "bg-blue-900/50 text-blue-300"
              }`}
            >
              {event.eventType}
            </span>
            <span className="text-gray-400 truncate">{event.source}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
