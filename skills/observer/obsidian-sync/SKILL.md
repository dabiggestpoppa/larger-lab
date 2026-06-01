---
name: o2c-obsidian-sync
description: Sync O2C-VAULT markdown files to Obsidian vault. Write, search, and manage vault notes with CAUSE/FIX/RESULT/LINKS standard.
---

# O2C Obsidian Sync

Sync the O2C-VAULT (filesystem cognition layer) with Obsidian.

## Vault Paths

- **Source**: `memory/obsidian-vault/` (in project root)
- **Obsidian target**: Auto-detected from `OBSIDIAN_VAULT_PATH` env var, or `~/Documents/Obsidian Vault/`, or `~/memory/obsidian-vault/`
- If no Obsidian vault exists, writes stay in `memory/obsidian-vault/` (Obsidian will pick them up when vault is opened)

## Write a Note

Use `core.obsidian.live_sync.write_and_sync()`:

```python
from core.obsidian.live_sync import write_and_sync

content = """# Note Title

CAUSE:
[What caused this]

FIX:
[What fixed it]

RESULT:
[Outcome]

LINKS:
[[Related Note]]
"""

write_and_sync("doctrine/My_Note.md", content)
```

## Sync All Files

```python
from core.obsidian.live_sync import sync_to_obsidian
written, skipped = sync_to_obsidian()
print(f"Synced: {written} written, {skipped} skipped")
```

## Search Notes

Use `core.obsidian.vault_writer.VaultWriter`:

```python
from core.obsidian.vault_writer import VaultWriter
writer = VaultWriter()
notes = writer.list_notes(category="doctrine", search="keyword")
```

## Note Standard

Every note MUST follow CAUSE/FIX/RESULT/LINKS format. Use `core.obsidian.note_standard.NoteValidator` to validate.

## Taxonomy

Vault directories: `agents/`, `doctrine/`, `failures/`, `execution/`, `memory/`, `ontology/`, `graphs/`, `journals/`, `skills/`, `heuristics/`, `routing/`, `architecture/`

Use `core.obsidian.taxonomy.Taxonomy` to enforce structure.
