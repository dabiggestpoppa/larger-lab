/**
 * Phase 3 — Timeline Store
 * Zustand store for temporal playback state.
 */
import { create } from "zustand";
import { RuntimeFrame, PlaybackState, TimelineEvent } from "../lib/timeline/types";

interface TimelineStore {
  frames: RuntimeFrame[];
  currentFrame: number;
  playback: PlaybackState;
  selectedEvent: TimelineEvent | null;
  isLoaded: boolean;

  // Actions
  setFrames: (frames: RuntimeFrame[]) => void;
  setCurrentFrame: (frame: number) => void;
  setPlayback: (update: Partial<PlaybackState>) => void;
  setSelectedEvent: (event: TimelineEvent | null) => void;
  loadFromAPI: () => Promise<void>;
}

export const useTimelineStore = create<TimelineStore>((set, get) => ({
  frames: [],
  currentFrame: 0,
  playback: {
    isPlaying: false,
    isReversed: false,
    speed: 1,
    currentFrame: 0,
    totalFrames: 0,
    loop: false,
  },
  selectedEvent: null,
  isLoaded: false,

  setFrames: (frames) =>
    set({
      frames,
      isLoaded: true,
      playback: { ...get().playback, totalFrames: frames.length },
    }),

  setCurrentFrame: (frame) =>
    set({
      currentFrame: frame,
      playback: { ...get().playback, currentFrame: frame },
    }),

  setPlayback: (update) =>
    set({ playback: { ...get().playback, ...update } }),

  setSelectedEvent: (event) => set({ selectedEvent: event }),

  loadFromAPI: async () => {
    try {
      const res = await fetch("/api/temporal/timeline");
      const data = await res.json();
      const frames: RuntimeFrame[] = data.frames.map((f: any, i: number) => ({
        frameId: f.frameId || `frame_${i}`,
        timestamp: f.timestamp || i * 1000,
        topologySnapshot: f.topologySnapshot || { nodes: [], edges: [] },
        entropySnapshot: f.entropySnapshot || { local: 0, cluster: 0, global: 0 },
        repairSnapshot: f.repairSnapshot || { active: [], completed: [] },
        events: f.events || [],
        observerStates: f.observerStates || {},
      }));
      set({
        frames,
        isLoaded: true,
        playback: { ...get().playback, totalFrames: frames.length },
      });
    } catch (err) {
      console.error("Failed to load timeline:", err);
    }
  },
}));
