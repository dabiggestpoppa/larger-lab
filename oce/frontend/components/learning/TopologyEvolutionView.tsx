import { useLearningStore } from "@/stores/learningStore";

export default function TopologyEvolutionView() {
  const clusters = useLearningStore((s) => s.topologyClusters);

  if (clusters.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Topology Evolution</h3>
        <p className="text-xs text-gray-600 italic">No topology clusters analyzed yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Topology Clusters ({clusters.length})
      </h3>
      <div className="space-y-2">
        {clusters.map((cluster) => (
          <div key={cluster.id} className="bg-gray-800/50 rounded px-3 py-2">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-medium text-gray-300">{cluster.id}</span>
              <div className="flex gap-3">
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">Stability:</span>
                  <span
                    className={`text-xs font-mono ${
                      cluster.stability >= 0.7
                        ? "text-green-400"
                        : cluster.stability >= 0.4
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {(cluster.stability * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">Entropy:</span>
                  <span
                    className={`text-xs font-mono ${
                      cluster.entropy <= 0.3
                        ? "text-green-400"
                        : cluster.entropy <= 0.6
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {(cluster.entropy * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
            {/* Stability bar */}
            <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${cluster.stability * 100}%`,
                  backgroundColor:
                    cluster.stability >= 0.7
                      ? "#22c55e"
                      : cluster.stability >= 0.4
                      ? "#eab308"
                      : "#ef4444",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
