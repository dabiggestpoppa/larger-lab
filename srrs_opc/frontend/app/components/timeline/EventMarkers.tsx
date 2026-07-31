/**
 * Phase 3 — Event Markers
 * Event type markers on the timeline scrubber.
 */
"use client";

import { useMemo } from "react";
import { TimelineEvent } from "../../lib/timeline/types";

interface Props {
  events: TimelineEvent[];
  totalFrames: number;
  onMarkerClick: (frameIndex: number) => void;
}

const EVENT_COLORS: Record<string, string> = {
  PERTURBATION: "bg-red-400",
  REPAIR_TRIGGER: "bg-amber-400",
  REPAIR_PROPAGATION: "bg-green-400",
  SYNC_COLLAPSE: "bg-purple-400",
  SYNC_RESTORE: "bg-cyan-400",
  ENTROPY_SPIKE: "bg-orange-400",
  ROUTING_SHIFT: "bg-blue-400",
  OBSERVER_FAILURE: "bg-red-600",
  ATTRACTOR_FORMATION: "bg-emerald-400",
};

export default function EventMarkers({ events, totalFrames, onMarkerClick }: Props) {
  const markers = useMemo(() => {
    return events.map((evt, i) => ({
      event: evt,
      position: totalFrames > 0 ? (i / totalFrames) * 100 : 0,
      color: EVENT_COLORS[evt.type] || "bg-gray-400",
    }));
  }, [events, totalFrames]);

  return (
    <div className="absolute top-0 left-0 right-0 h-1">
      {markers.map((m, i) => (
        <div
          key={i}
          className={`absolute top-0 w-1 h-full ${m.color} cursor-pointer hover:scale-x-150 transition-transform`}
          style={{ left: `${m.position}%` }}
          onClick={() => onMarkerClick(Math.round((m.position / 100) * totalFrames))}
          title={`${m.event.type} @ ${m.event.source}`}
        />
      ))}
    </div>
  );
}
