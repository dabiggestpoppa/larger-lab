"use client";

import PersistentFieldView from "../../components/persistence/PersistentFieldView";
import RuntimeHeartbeatPanel from "../../components/persistence/RuntimeHeartbeatPanel";
import DormantStateMonitor from "../../components/persistence/DormantStateMonitor";
import ObserverPersistenceView from "../../components/persistence/ObserverPersistenceView";
import DriftAnalysisPanel from "../../components/persistence/DriftAnalysisPanel";
import LongHorizonTimeline from "../../components/persistence/LongHorizonTimeline";
import AutonomousRepairView from "../../components/persistence/AutonomousRepairView";
import RecoveryContinuityPanel from "../../components/persistence/RecoveryContinuityPanel";

export default function PersistencePage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-gray-200">
      <div className="max-w-7xl mx-auto p-4">
        <div className="mb-4">
          <h1 className="text-xl font-mono text-gray-100">Persistent Field Mode</h1>
          <p className="text-xs text-gray-500 font-mono mt-1">
            Continuous operational continuity — O-7
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main panel */}
          <div className="lg:col-span-2">
            <PersistentFieldView />
          </div>

          {/* Side panels */}
          <div className="space-y-4">
            <RuntimeHeartbeatPanel />
            <DormantStateMonitor />
            <ObserverPersistenceView />
          </div>

          {/* Bottom row */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <DriftAnalysisPanel />
            <LongHorizonTimeline />
            <AutonomousRepairView />
            <RecoveryContinuityPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
