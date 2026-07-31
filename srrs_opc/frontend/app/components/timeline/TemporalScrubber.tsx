/**
 * Phase 3 — Temporal Scrubber
 * Draggable timeline scrubber with event markers.
 */
"use client";

import { useRef, useCallback } from "react";
import { useTimelineStore } from "../../stores/timelineStore";

export default function TemporalScrubber() {
  const { frames, currentFrame, setCurrentFrame } = useTimelineStore();
  const trackRef = useRef<HTMLDivElement>(null);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!trackRef.current || frames.length === 0) return;
      const rect = trackRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, x / rect.width));
      const frame = Math.round(pct * (frames.length - 1));
      setCurrentFrame(frame);
    },
    [frames.length, setCurrentFrame]
  );

  const progress = frames.length > 0 ? (currentFrame / (frames.length - 1)) * 100 : 0;

  // Get event positions for markers
  const eventMarkers = frames
    .map((f, i) => ({ frame: i, hasEvent: f.events.length > 0 }))
    .filter((m) => m.hasEvent);

  return (
    <div className="w-full px-4 py-2 bg-gray-900/60 border-t border-gray-700">
      {/* Track */}
      <div
        ref={trackRef}
        onClick={handleClick}
        className="relative h-8 bg-gray-800 rounded cursor-pointer overflow-hidden"
      >
        {/* Progress fill */}
        <div
          className="absolute top-0 left-0 h-full bg-cyan-600/30 transition-all duration-100"
          style={{ width: `${progress}%` }}
        />

        {/* Event markers */}
        {eventMarkers.map((m) => (
          <div
            key={m.frame}
            className="absolute top-0 h-full w-0.5 bg-amber-400/60"
            style={{ left: `${(m.frame / (frames.length - 1)) * 100}%` }}
          />
        ))}

        {/* Playhead */}
        <div
          className="absolute top-0 h-full w-0.5 bg-cyan-400 transition-all duration-100"
          style={{ left: `${progress}%` }}
        >
          <div className="absolute -top-1 -left-1.5 w-3 h-3 bg-cyan-400 rounded-full" />
        </div>
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>{frames[0]?.timestamp ? new Date(frames[0].timestamp).toLocaleTimeString() : "00:00"}</span>
        <span className="text-cyan-400">
          {frames[currentFrame]?.timestamp
            ? new Date(frames[currentFrame].timestamp).toLocaleTimeString()
            : "—"}
        </span>
        <span>
          {frames[frames.length - 1]?.timestamp
            ? new Date(frames[frames.length - 1].timestamp).toLocaleTimeString()
            : "00:00"}
        </span>
      </div>
    </div>
  );
}
