"use client";

import { useEffect, useState, useCallback } from "react";

interface VaultNote {
  id: string;
  title: string;
  path: string;
  content: string;
  tags: string[];
  links: string[];
  modified: string;
  category: string;
}

interface VaultViewerProps {
  onNoteSelect?: (note: VaultNote) => void;
}

export default function VaultViewer({ onNoteSelect }: VaultViewerProps) {
  const [notes, setNotes] = useState<VaultNote[]>([]);
  const [selectedNote, setSelectedNote] = useState<VaultNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [category, setCategory] = useState("all");

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/vault/notes");
      if (!res.ok) {
        // API not yet available — show empty state
        setNotes([]);
        setError("Vault API not yet available. Waiting for Phase 0A (Vault Writer) completion.");
        return;
      }
      const data = await res.json();
      setNotes(data.notes || []);
    } catch {
      setNotes([]);
      setError("Vault API not yet available. Waiting for Phase 0A (Vault Writer) completion.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotes();
    // Poll every 30s for new notes
    const interval = setInterval(fetchNotes, 30000);
    return () => clearInterval(interval);
  }, [fetchNotes]);

  const filteredNotes = notes.filter((note) => {
    const matchesFilter =
      !filter ||
      note.title.toLowerCase().includes(filter.toLowerCase()) ||
      note.content.toLowerCase().includes(filter.toLowerCase()) ||
      note.tags.some((t) => t.toLowerCase().includes(filter.toLowerCase()));
    const matchesCategory =
      category === "all" || note.category === category;
    return matchesFilter && matchesCategory;
  });

  const categories = ["all", ...new Set(notes.map((n) => n.category))];

  const handleNoteClick = (note: VaultNote) => {
    setSelectedNote(note);
    onNoteSelect?.(note);
  };

  if (loading && notes.length === 0) {
    return (
      <div className="p-4 space-y-4">
        <h2 className="text-lg font-semibold text-gray-200">Vault</h2>
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-4 h-4 border-2 border-gray-600 border-t-cyan-400 rounded-full animate-spin" />
          <span className="text-sm">Loading vault...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
        <h2 className="text-xs font-mono font-bold text-[var(--text-primary)]">
          O2C VAULT
        </h2>
        <button
          onClick={fetchNotes}
          className="text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--accent-primary)] transition-colors"
        >
          REFRESH
        </button>
      </div>

      {/* Filters */}
      <div className="px-4 py-2 border-b border-[var(--border-subtle)] space-y-2">
        <input
          type="text"
          placeholder="Filter notes..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full px-2 py-1 text-xs font-mono bg-[var(--bg-tertiary)] border border-[var(--border-default)] rounded text-[var(--text-primary)] placeholder-gray-600 focus:outline-none focus:border-[var(--accent-primary)]"
        />
        <div className="flex gap-1 flex-wrap">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${
                category === cat
                  ? "bg-[var(--accent-primary)] text-white border-[var(--accent-primary)]"
                  : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border-default)] hover:text-[var(--text-primary)]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {error && notes.length === 0 ? (
          <div className="p-4 text-center">
            <div className="text-gray-500 text-sm mb-2">📂</div>
            <p className="text-xs text-gray-400">{error}</p>
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="p-4 text-center">
            <div className="text-gray-500 text-sm mb-2">📝</div>
            <p className="text-xs text-gray-400">
              {filter || category !== "all"
                ? "No notes match the current filter."
                : "No notes in vault yet. Phase 0A will populate this."}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border-subtle)]">
            {filteredNotes.map((note) => (
              <div
                key={note.id}
                onClick={() => handleNoteClick(note)}
                className={`px-4 py-2 cursor-pointer transition-colors ${
                  selectedNote?.id === note.id
                    ? "bg-[var(--accent-primary)]/10 border-l-2 border-[var(--accent-primary)]"
                    : "hover:bg-[var(--bg-tertiary)] border-l-2 border-transparent"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-[var(--text-primary)] truncate">
                    {note.title}
                  </span>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] ml-2 shrink-0">
                    {note.category}
                  </span>
                </div>
                {note.tags.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {note.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="px-1 py-0 text-[9px] font-mono bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded"
                      >
                        #{tag}
                      </span>
                    ))}
                    {note.tags.length > 3 && (
                      <span className="text-[9px] font-mono text-[var(--text-muted)]">
                        +{note.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
                {note.links.length > 0 && (
                  <div className="mt-1">
                    <span className="text-[9px] font-mono text-[var(--text-muted)]">
                      → {note.links.length} link{note.links.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Note Preview */}
      {selectedNote && (
        <div className="border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)] p-4 max-h-48 overflow-auto">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-mono font-bold text-[var(--text-primary)]">
              {selectedNote.title}
            </h3>
            <button
              onClick={() => setSelectedNote(null)}
              className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              ✕
            </button>
          </div>
          <pre className="text-[10px] font-mono text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
            {selectedNote.content.slice(500)}
            {selectedNote.content.length > 500 ? "\n..." : ""}
          </pre>
        </div>
      )}

      {/* Status Bar */}
      <div className="px-4 py-1 border-t border-[var(--border-subtle)] bg-[var(--bg-tertiary)]">
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {filteredNotes.length} note{filteredNotes.length !== 1 ? "s" : ""} 
          {category !== "all" ? ` in ${category}` : ""}
          {filter ? ` matching "${filter}"` : ""}
        </span>
      </div>
    </div>
  );
}
