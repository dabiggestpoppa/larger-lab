/* Synchronization-based clustering for SRRA-OPH topology */

import { ObserverNode } from "../../stores/topologyStore";

export interface Cluster {
  id: string;
  nodes: string[];
  stabilityScore: number;
  entropyScore: number;
  syncDensity: number;
  centerX: number;
  centerY: number;
}

/**
 * Cluster observers by sync score proximity.
 * Observers with high sync scores that are connected form clusters.
 */
export function computeClusters(
  nodes: ObserverNode[],
  edges: { source: string; target: string; strength: number }[]
): Cluster[] {
  const clusters: Cluster[] = [];
  const visited = new Set<string>();

  // Build adjacency map for sync edges
  const adjacency: Record<string, string[]> = {};
  edges.forEach((e) => {
    if (!adjacency[e.source]) adjacency[e.source] = [];
    if (!adjacency[e.target]) adjacency[e.target] = [];
    adjacency[e.source].push(e.target);
    adjacency[e.target].push(e.source);
  });

  // Find clusters via BFS on high-sync nodes
  nodes.forEach((node) => {
    if (visited.has(node.id) || node.syncScore < 0.5) return;

    const cluster: string[] = [];
    const queue = [node.id];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);

      const currentNode = nodes.find((n) => n.id === current);
      if (!currentNode || currentNode.syncScore < 0.3) continue;

      cluster.push(current);

      const neighbors = adjacency[current] || [];
      neighbors.forEach((neighbor) => {
        const neighborNode = nodes.find((n) => n.id === neighbor);
        if (neighborNode && !visited.has(neighbor) && neighborNode.syncScore > 0.3) {
          queue.push(neighbor);
        }
      });
    }

    if (cluster.length >= 2) {
      const clusterNodes = cluster.map((id) => nodes.find((n) => n.id === id)!).filter(Boolean);
      const avgEntropy = clusterNodes.reduce((sum, n) => sum + n.entropy, 0) / clusterNodes.length;
      const avgSync = clusterNodes.reduce((sum, n) => sum + n.syncScore, 0) / clusterNodes.length;
      const centerX = clusterNodes.reduce((sum, n) => sum + n.x, 0) / clusterNodes.length;
      const centerY = clusterNodes.reduce((sum, n) => sum + n.y, 0) / clusterNodes.length;

      clusters.push({
        id: `cluster-${clusters.length + 1}`,
        nodes: cluster,
        stabilityScore: avgSync * (1 - avgEntropy),
        entropyScore: avgEntropy,
        syncDensity: avgSync,
        centerX,
        centerY,
      });
    }
  });

  return clusters;
}
