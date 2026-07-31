"use client";

import { useEffect, useState } from "react";
import { useResearchStore } from "@/stores/researchStore";

export default function DoctrineLibraryPage() {
  const { doctrine, doctrineLoading, doctrineError, doctrineDomain, setDoctrineDomain, fetchDoctrine } = useResearchStore();
  const [selectedNote, setSelectedNote] = useState<string | null>(null);

  useEffect(() => {
    fetchDoctrine();
  }, [fetchDoctrine]);

  const domains = [...new Set(doctrine.map((d) => d.domain || d.path.split("/")[0]))];

  return (
    <div className="p-6 space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-lg font-bold text-[var(--text-primary)]">Doctrine Library</h1>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Auto-extracted operational doctrine from research patterns
        </p>
      </div>

      {/* Domain filter */}
      <div className="flex gap-2">
        <button
          onClick={() => { setDoctrineDomain(""); fetchDoctrine(); }}
          className={`text-[10px] px-2 py-1 rounded border ${
            !doctrineDomain
              ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
              : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)]"
          }`}
        >
          All
        </button>
        {domains.map((d) => (
          <button
            key={d}
            onClick={() => { setDoctrineDomain(d); fetchDoctrine(d); }}
            className={`text-[10px] px-2 py-1 rounded border ${
              doctrineDomain === d
                ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)]"
            }`}
          >
            {d}
          </button>
        ))}
      </div>

      {doctrineLoading && <div className="text-xs text-[var(--text-muted)]">Loading...</div>}
      {doctrineError && <div className="text-xs text-[var(--accent-danger)]">{doctrineError}</div>}

      <div className="flex-1 flex gap-4 min-h-0">
        {/* Note list */}
        <div className="w-1/3 space-y-2 overflow-y-auto">
          {doctrine.length === 0 && !doctrineLoading && (
            <div className="text-xs text-[var(--text-muted)] text-center py-8">
              No doctrine notes yet. Doctrine is auto-extracted when ≥3 papers share a pattern.
            </div>
          )}
          {doctrine.map((note) => (
            <button
              key={note.path}
              onClick={() => setSelectedNote(note.path)}
              className={`w-full text-left p-3 rounded border ${
                selectedNote === note.path
                  ? "bg-[var(--bg-tertiary)] border-[var(--accent-primary)]"
                  : "bg-[var(--bg-secondary)] border-[var(--border-default)] hover:border-[var(--text-muted)]"
              }`}
            >
              <div className="text-xs font-semibold text-[var(--text-primary)]">{note.title}</div>
              <div className="text-[10px] text-[var(--text-muted)] mt-1 truncate">{note.path}</div>
            </button>
          ))}
        </div>

        {/* Note preview */}
        <div className="flex-1 card p-4 overflow-y-auto">
          {selectedNote ? (
            <>
              {(() => {
                const note = doctrine.find((d) => d.path === selectedNote);
                if (!note) return null;
                return (
                  <div>
                    <h2 className="text-sm font-bold text-[var(--text-primary)] mb-2">{note.title}</h2>
                    <div className="text-[10px] text-[var(--text-muted)] mb-4 font-mono">{note.path}</div>
                    <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
                      {note.preview}
                    </div>
                  </div>
                );
              })()}
            </>
          ) : (
            <div className="text-xs text-[var(--text-muted)] text-center py-12">
              Select a doctrine note to view
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
