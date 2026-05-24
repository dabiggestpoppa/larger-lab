/**
 * Phase 3 — Frame Interpolator
 * Smooth interpolation between temporal frames.
 */
import { RuntimeFrame, ObserverState, EdgeState } from "./types";

export class FrameInterpolator {
  /**
   * Interpolate between two frames at a given progress (0-1).
   */
  interpolate(from: RuntimeFrame, to: RuntimeFrame, progress: number): RuntimeFrame {
    const t = Math.max(0, Math.min(1, progress));
    return {
      frameId: `interp_${from.frameId}_${to.frameId}`,
      timestamp: from.timestamp + (to.timestamp - from.timestamp) * t,
      topologySnapshot: {
        nodes: this.interpolateNodes(from.topologySnapshot.nodes, to.topologySnapshot.nodes, t),
        edges: this.interpolateEdges(from.topologySnapshot.edges, to.topologySnapshot.edges, t),
      },
      entropySnapshot: {
        local: this.lerp(from.entropySnapshot.local, to.entropySnapshot.local, t),
        cluster: this.lerp(from.entropySnapshot.cluster, to.entropySnapshot.cluster, t),
        global: this.lerp(from.entropySnapshot.global, to.entropySnapshot.global, t),
      },
      repairSnapshot: t < 0.5 ? from.repairSnapshot : to.repairSnapshot,
      events: t < 0.5 ? from.events : to.events,
      observerStates: t < 0.5 ? from.observerStates : to.observerStates,
    };
  }

  private interpolateNodes(from: ObserverState[], to: ObserverState[], t: number): ObserverState[] {
    const toMap = new Map(to.map((n) => [n.id, n]));
    return from.map((node) => {
      const target = toMap.get(node.id);
      if (!target) return node;
      return {
        ...node,
        x: this.lerp(node.x, target.x, t),
        y: this.lerp(node.y, target.y, t),
        entropy: this.lerp(node.entropy, target.entropy, t),
        status: t < 0.5 ? node.status : target.status,
        zone: t < 0.5 ? node.zone : target.zone,
      };
    });
  }

  private interpolateEdges(from: EdgeState[], to: EdgeState[], t: number): EdgeState[] {
    const toMap = new Map(to.map((e) => [`${e.source}->${e.target}`, e]));
    return from.map((edge) => {
      const key = `${edge.source}->${edge.target}`;
      const target = toMap.get(key);
      if (!target) return edge;
      return {
        ...edge,
        weight: this.lerp(edge.weight, target.weight, t),
        active: t < 0.5 ? edge.active : target.active,
      };
    });
  }

  private lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }
}
