import { useLearningStore } from "@/stores/learningStore";

export default function AdaptationMonitor() {
  const events = useLearningStore((s) => s.adaptationEvents);

  if (events.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Adaptation Monitor</h3>
        <p className="text-xs text-gray-600 italic">No adaptation events yet. System stable.</p>
      </div>
    );
  }

  const typeColors: Record<string, string> = {
    routing: "bg-purple-900/50 text-purple-300",
    model: "bg-blue-900/50 text-blue-300",
    observer: "bg-green-900/50 text-green-300",
    topology: "bg-cyan-900/50 text-cyan-300",
    boundary: "bg-orange-900/50 text-orange-300",
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Adaptation Events ({events.length})
      </h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {events.map((event) => (
          <div key={event.id} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    typeColors[event.type] || "bg-gray-700 text-gray-300"
                  }`}
                >
                  {event.type}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <span
                className={`text-xs font-mono ${
                  event.impact > 0 ? "text-green-400" : event.impact < 0 ? "text-red-400" : "text-gray-400"
                }`}
              >
                {event.impact > 0 ? "+" : ""}
                {(event.impact * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
