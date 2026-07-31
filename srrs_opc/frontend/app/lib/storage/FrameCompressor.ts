/**
 * Phase 3 — Frame Compressor
 * Delta compression for temporal frame storage.
 */
import { RuntimeFrame } from "../timeline/types";

export class FrameCompressor {
  /**
   * Compress a frame relative to a baseline using delta encoding.
   */
  compress(frame: RuntimeFrame, baseline: RuntimeFrame): CompressedFrame {
    const deltaNodes = frame.topologySnapshot.nodes.filter(
      (n) => {
        const base = baseline.topologySnapshot.nodes.find((bn) => bn.id === n.id);
        return !base || base.x !== n.x || base.y !== n.y || base.entropy !== n.entropy || base.status !== n.status;
      }
    );

    const deltaEdges = frame.topologySnapshot.edges.filter(
      (e) => {
        const base = baseline.topologySnapshot.edges.find(
          (be) => be.source === e.source && be.target === e.target
        );
        return !base || base.weight !== e.weight || base.active !== e.active;
      }
    );

    return {
      frameId: frame.frameId,
      timestamp: frame.timestamp,
      baselineFrameId: baseline.frameId,
      deltaNodes,
      deltaEdges,
      entropySnapshot: frame.entropySnapshot,
      events: frame.events,
      isKeyframe: false,
    };
  }

  /**
   * Create a keyframe (full snapshot) every N frames.
   */
  createKeyframe(frame: RuntimeFrame): CompressedFrame {
    return {
      frameId: frame.frameId,
      timestamp: frame.timestamp,
      baselineFrameId: frame.frameId,
      deltaNodes: frame.topologySnapshot.nodes,
      deltaEdges: frame.topologySnapshot.edges,
      entropySnapshot: frame.entropySnapshot,
      events: frame.events,
      isKeyframe: true,
    };
  }

  /**
   * Decompress a frame by applying delta to baseline.
   */
  decompress(compressed: CompressedFrame, baseline: RuntimeFrame): RuntimeFrame {
    if (compressed.isKeyframe) {
      return {
        frameId: compressed.frameId,
        timestamp: compressed.timestamp,
        topologySnapshot: {
          nodes: compressed.deltaNodes,
          edges: compressed.deltaEdges,
        },
        entropySnapshot: compressed.entropySnapshot,
        repairSnapshot: { active: [], completed: [] },
        events: compressed.events,
        observerStates: baseline.observerStates,
      };
    }

    // Apply delta to baseline
    const nodeMap = new Map(baseline.topologySnapshot.nodes.map((n) => [n.id, n]));
    for (const dn of compressed.deltaNodes) {
      nodeMap.set(dn.id, dn);
    }

    const edgeMap = new Map(
      baseline.topologySnapshot.edges.map((e) => [`${e.source}->${e.target}`, e])
    );
    for (const de of compressed.deltaEdges) {
      edgeMap.set(`${de.source}->${de.target}`, de);
    }

    return {
      frameId: compressed.frameId,
      timestamp: compressed.timestamp,
      topologySnapshot: {
        nodes: Array.from(nodeMap.values()),
        edges: Array.from(edgeMap.values()),
      },
      entropySnapshot: compressed.entropySnapshot,
      repairSnapshot: { active: [], completed: [] },
      events: compressed.events,
      observerStates: baseline.observerStates,
    };
  }
}

export type CompressedFrame = {
  frameId: string;
  timestamp: number;
  baselineFrameId: string;
  deltaNodes: any[];
  deltaEdges: any[];
  entropySnapshot: { local: number; cluster: number; global: number };
  events: any[];
  isKeyframe: boolean;
};
