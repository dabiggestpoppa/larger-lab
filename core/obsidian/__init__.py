"""
O2C Obsidian Vault — Cognitive Filesystem Foundation (Phase 00)

Components:
    vault_writer.py  — Write structured markdown to vault (Phase 0A)
    compressor.py    — Compress execution traces (Phase 0B)
    linker.py        — Auto-link knowledge graph (Phase 0C)
    taxonomy.py      — Enforce vault structure (Phase 0H)
    note_standard.py — Validate note format (Phase 0I)
"""

from core.obsidian.vault_writer import VaultWriter, write_note, get_note, list_notes, get_writer

__all__ = [
    "VaultWriter",
    "write_note",
    "get_note",
    "list_notes",
    "get_writer",
]
