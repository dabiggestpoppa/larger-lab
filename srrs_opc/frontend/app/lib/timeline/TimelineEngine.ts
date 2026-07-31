/**
 * Phase 3 — Timeline Engine
 * Master temporal controller for playback.
 */
import { RuntimeFrame, PlaybackState } from "./types";

export class TimelineEngine {
  private frames: RuntimeFrame[] = [];
  private state: PlaybackState = {
    isPlaying: false,
    isReversed: false,
    speed: 1,
    currentFrame: 0,
    totalFrames: 0,
    loop: false,
  };
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private listeners: Set<(state: PlaybackState) => void> = new Set();

  loadFrames(frames: RuntimeFrame[]) {
    this.frames = frames;
    this.state.totalFrames = frames.length;
    this.state.currentFrame = 0;
    this.notify();
  }

  getState(): PlaybackState {
    return { ...this.state };
  }

  getCurrentFrame(): RuntimeFrame | null {
    if (this.frames.length === 0) return null;
    return this.frames[this.state.currentFrame] || null;
  }

  getFrameAt(index: number): RuntimeFrame | null {
    if (index < 0 || index >= this.frames.length) return null;
    return this.frames[index];
  }

  play() {
    if (this.state.isPlaying) return;
    this.state.isPlaying = true;
    this.startTicking();
    this.notify();
  }

  pause() {
    this.state.isPlaying = false;
    this.stopTicking();
    this.notify();
  }

  stop() {
    this.state.isPlaying = false;
    this.state.currentFrame = 0;
    this.stopTicking();
    this.notify();
  }

  reverse() {
    this.state.isReversed = !this.state.isReversed;
    this.notify();
  }

  setSpeed(speed: number) {
    this.state.speed = Math.max(0.25, Math.min(10, speed));
    if (this.state.isPlaying) {
      this.stopTicking();
      this.startTicking();
    }
    this.notify();
  }

  stepForward() {
    if (this.state.currentFrame < this.frames.length - 1) {
      this.state.currentFrame++;
    } else if (this.state.loop) {
      this.state.currentFrame = 0;
    }
    this.notify();
  }

  stepBackward() {
    if (this.state.currentFrame > 0) {
      this.state.currentFrame--;
    } else if (this.state.loop) {
      this.state.currentFrame = this.frames.length - 1;
    }
    this.notify();
  }

  seekTo(frame: number) {
    this.state.currentFrame = Math.max(0, Math.min(this.frames.length - 1, frame));
    this.notify();
  }

  setLoop(loop: boolean) {
    this.state.loop = loop;
    this.notify();
  }

  subscribe(listener: (state: PlaybackState) => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private startTicking() {
    const baseInterval = 100; // ms per frame at 1x speed
    const interval = baseInterval / this.state.speed;
    this.intervalId = setInterval(() => {
      if (this.state.isReversed) {
        this.stepBackward();
      } else {
        this.stepForward();
      }
    }, interval);
  }

  private stopTicking() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private notify() {
    this.listeners.forEach((l) => l(this.getState()));
  }

  destroy() {
    this.stopTicking();
    this.listeners.clear();
  }
}
