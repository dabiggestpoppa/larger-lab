/* Fixed docstring */

"use client";

import { useObserverStore } from "@/stores/observerStore";
import ObserverStatus from "./ObserverStatus";
import ContinuityPanel from "./ContinuityPanel";
import RuntimeSummary from "./RuntimeSummary";
import ObserverHealthPanel from "./ObserverHealthPanel";

export default function ObserverConsole() {
  const observer = useObserverStore((s) => s.observer);

  return (
    <div className="flex flex-col gap-4 p-4 bg-gray-950 border border-gray-800 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">
            Primary Observer
          </h2>
          <p className="text-xs text-gray-500">
            Continuity-aware orchestration interface
          </p>
        </div>
        <div className="text-xs font-mono text-gray-600">
          {observer.observerId}
        </div>
      </div>

      {/* Status bar */}
      <ObserverStatus />

      {/* Panels grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ContinuityPanel />
        <RuntimeSummary />
      </div>

      {/* Health metrics */}
      <ObserverHealthPanel />
    </div>
  );
}
