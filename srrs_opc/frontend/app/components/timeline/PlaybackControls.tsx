/**
 * Phase 3 — Playback Controls
 * Play/pause/stop/reverse/step/speed controls for temporal playback.
 */
"use client";

import { useEffect, useRef, useCallback } from "react";
import { useTimelineStore } from "../../stores/timelineStore";

export default function PlaybackControls() {
  const { playback, setPlayback, setCurrentFrame, frames, currentFrame } = useTimelineStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPlayback = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    const baseInterval = 200; // ms per frame at 1x
    intervalRef.current = setInterval(() => {
      const store = useTimelineStore.getState();
      const { playback: p, frames: f, currentFrame: cf } = store;
      if (!p.isPlaying) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }
      let next = p.isReversed ? cf - 1 : cf + 1;
      if (next >= f.length) {
        if (p.loop) next = 0;
        else { setPlayback({ isPlaying: false }); return; }
      }
      if (next < 0) {
        if (p.loop) next = f.length - 1;
        else { setPlayback({ isPlaying: false }); return; }
      }
      setCurrentFrame(next);
    }, baseInterval / playback.speed);
  }, [playback.speed, playback.isReversed, playback.loop, setCurrentFrame, setPlayback]);

  useEffect(() => {
    if (playback.isPlaying) {
      startPlayback();
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playback.isPlaying, startPlayback]);

  const stepForward = () => {
    if (currentFrame < frames.length - 1) setCurrentFrame(currentFrame + 1);
  };

  const stepBackward = () => {
    if (currentFrame > 0) setCurrentFrame(currentFrame - 1);
  };

  return (
    <div className="flex items-center gap-2 bg-gray-900/80 rounded-lg px-4 py-2 border border-gray-700">
      {/* Step backward */}
      <button onClick={stepBackward} disabled={currentFrame === 0}
        className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 text-gray-300">
        <span className="text-sm">⏮</span>
      </button>

      {/* Play/Pause */}
      <button onClick={() => setPlayback({ isPlaying: !playback.isPlaying })}
        className="p-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white">
        <span className="text-sm">{playback.isPlaying ? "⏸" : "▶"}</span>
      </button>

      {/* Stop */}
      <button onClick={() => { setPlayback({ isPlaying: false }); setCurrentFrame(0); }}
        className="p-1.5 rounded hover:bg-gray-700 text-gray-300">
        <span className="text-sm">⏹</span>
      </button>

      {/* Step forward */}
      <button onClick={stepForward} disabled={currentFrame >= frames.length - 1}
        className="p-1.5 rounded hover:bg-gray-700 disabled:opacity-30 text-gray-300">
        <span className="text-sm">⏭</span>
      </button>

      {/* Reverse */}
      <button onClick={() => setPlayback({ isReversed: !playback.isReversed })}
        className={`p-1.5 rounded hover:bg-gray-700 ${playback.isReversed ? "bg-amber-600 text-white" : "text-gray-300"}`}>
        <span className="text-sm">⏪</span>
      </button>

      {/* Speed */}
      <select value={playback.speed} onChange={(e) => setPlayback({ speed: parseFloat(e.target.value) })}
        className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-600">
        <option value={0.25}>0.25x</option>
        <option value={0.5}>0.5x</option>
        <option value={1}>1x</option>
        <option value={2}>2x</option>
        <option value={5}>5x</option>
        <option value={10}>10x</option>
      </select>

      {/* Loop */}
      <button onClick={() => setPlayback({ loop: !playback.loop })}
        className={`p-1.5 rounded hover:bg-gray-700 ${playback.loop ? "bg-green-600 text-white" : "text-gray-300"}`}>
        <span className="text-sm">🔁</span>
      </button>

      {/* Frame counter */}
      <span className="text-xs text-gray-400 ml-2">
        {currentFrame + 1} / {frames.length}
      </span>
    </div>
  );
}
