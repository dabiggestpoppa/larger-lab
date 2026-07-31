"use client";

import { useEffect, useState } from "react";

interface FsNode {
  id: string;
  name: string;
  path: string;
  type: string;
  size?: number;
}

interface FsEdge {
  source: string;
  target: string;
}

interface FsTopology {
  nodes: FsNode[];
  edges: FsEdge[];
}

export default function FilesystemTopology() {
  const [topology, setTopology] = useState<FsTopology | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    const fetchFilesystem = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/substrate/filesystem");
        if (res.ok) {
          const data = await res.json();
          setTopology({
            nodes: data.nodes || [],
            edges: data.edges || [],
          });
        }
      } catch (e) {
        console.error("Failed to fetch filesystem:", e);
      } finally {
        setLoading(false);
      }
    };

    fetchFilesystem();
  }, []);

  const nodes = topology?.nodes || [];
  const filteredNodes = filter
    ? nodes.filter((n) => n.name.toLowerCase().includes(filter.toLowerCase()) || n.path.toLowerCase().includes(filter.toLowerCase()))
    : nodes;

  // Build parent-child map from edges
  const childrenMap = new Map<string, FsNode[]>();
  const childIds = new Set<string>();
  for (const edge of topology?.edges || []) {
    const children = childrenMap.get(edge.source) || [];
    const child = nodes.find((n) => n.id === edge.target);
    if (child) {
      children.push(child);
      childrenMap.set(edge.source, children);
      childIds.add(child.id);
    }
  }
  // Root nodes = nodes that are not children of anything
  const rootNodes = nodes.filter((n) => !childIds.has(n.id));

  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());

  const togglePath = (path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const renderNode = (node: FsNode, depth: number = 0) => {
    const children = childrenMap.get(node.id) || [];
    const isExpanded = expandedPaths.has(node.id);
    const hasChildren = children.length > 0;

    return (
      <div key={node.id} className="select-none">
        <div
          className="flex items-center gap-1 py-0.5 cursor-pointer hover:text-cyan-400 text-xs"
          style={{ paddingLeft: `${depth * 16}px` }}
          onClick={() => hasChildren && togglePath(node.id)}
        >
          {hasChildren ? (
            <span className="text-[10px] text-gray-500 w-3">{isExpanded ? "▾" : "▸"}</span>
          ) : (
            <span className="w-3" />
          )}
          <span className={node.type === "directory" ? "text-blue-400" : "text-gray-400"}>
            {node.type === "directory" ? "📁" : "📄"} {node.name}
          </span>
        </div>
        {isExpanded && hasChildren && (
          <div>{children.map((child) => renderNode(child, depth + 1))}</div>
        )}
      </div>
    );
  };

  const displayNodes = filter ? filteredNodes : rootNodes;

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Filesystem Topology</h2>

      <input
        type="text"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter files..."
        className="w-full bg-gray-900/50 border border-gray-800 rounded px-2 py-1 font-mono text-xs text-gray-300"
      />

      <div className="max-h-96 overflow-y-auto font-mono">
        {displayNodes.length > 0 ? (
          displayNodes.map((node) => renderNode(node))
        ) : (
          <div className="text-gray-500 text-xs">
            {loading ? "Scanning..." : filter ? "No matches" : "No files found"}
          </div>
        )}
      </div>

      <div className="text-[10px] text-gray-600">
        {nodes.length} nodes · {topology?.edges?.length || 0} edges
      </div>
    </div>
  );
}
