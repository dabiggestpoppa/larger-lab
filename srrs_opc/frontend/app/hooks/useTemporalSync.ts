/**
 * Phase 3 — Temporal Sync Hook
 * React hook for frame-locked updates across topology, entropy, and repair views.
 */
import { useEffect, useCallback } from "react";
import { useTimelineStore } from "../stores/timelineStore";
import { useEntropyStore } from "../stores/entropyStore";
import { useTopologyStore } from "../stores/topologyStore";

export function useTemporalSync() {
  const { frames, currentFrame } = useTimelineStore();
  const { updateFromFrame } = useEntropyStore();
  const { setNodes, setEdges } = useTopologyStore();

  const syncFrame = useCallback(
    (frameIndex: number) => {
      const frame = frames[frameIndex];
      if (!frame) return;

      // Sync topology
      if (frame.topologySnapshot) {
        setNodes(frame.topologySnapshot.nodes);
        setEdges(frame.topologySnapshot.edges);
      }

      // Sync entropy
      if (frame.observerStates) {
        updateFromFrame(frame.observerStates);
      }
    },
    [frames, setNodes, setEdges, updateFromFrame]
  );

  // Auto-sync when frame changes
  useEffect(() => {
    syncFrame(currentFrame);
  }, [currentFrame, syncFrame]);

  return { syncFrame };
}
