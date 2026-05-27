"""
O-1-F4: ArtifactViewer
=======================
Artifacts/results panel.
"""

"use client";

import { useState } from "react";

interface Artifact {
  id: string;
  type: "code" | "file" | "result" | "report";
  name: string;
  content: string;
  timestamp: string;
}

export default function ArtifactViewer() {
  const [artifacts] = useState<Artifact[]>([]);

  if (artifacts.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">
          Artifacts
        </h3>
        <p className="text-xs text-gray-600 italic">
          No artifacts yet. Task results will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-200 mb-3">
        Artifacts ({artifacts.length})
      </h3>
      <div className="space-y-2">
        {artifacts.map((artifact) => (
          <div
            key={artifact.id}
            className="bg-gray-800/50 rounded px-3 py-2"
          >
            <div className="flex justify-between items-center">
              <span className="text-xs font-medium text-gray-300">
                {artifact.name}
              </span>
              <span className="text-xs text-gray-500">
                {artifact.type}
              </span>
            </div>
            <pre className="text-xs text-gray-400 mt-1 overflow-x-auto">
              {artifact.content.substring(0, 200)}
              {artifact.content.length > 200 ? "..." : ""}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
