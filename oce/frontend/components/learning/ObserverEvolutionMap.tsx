import { useLearningStore } from "@/stores/learningStore";

export default function ObserverEvolutionMap() {
  const specializations = useLearningStore((s) => s.observerSpecializations);

  const entries = Object.entries(specializations);

  if (entries.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Observer Evolution</h3>
        <p className="text-xs text-gray-600 italic">No observer specialization data yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Observer Specializations ({entries.length})
      </h3>
      <div className="space-y-2">
        {entries.map(([observerId, score]) => (
          <div key={observerId} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-medium text-gray-300">{observerId}</span>
              <span
                className={`text-xs font-mono ${
                  score >= 0.7 ? "text-green-400" : score >= 0.4 ? "text-yellow-400" : "text-red-400"
                }`}
              >
                {(score * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${score * 100}%`,
                  backgroundColor:
                    score >= 0.7 ? "#22c55e" : score >= 0.4 ? "#eab308" : "#ef4444",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
