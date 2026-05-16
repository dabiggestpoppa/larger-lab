# HEARTBEAT.md — Periodic Checks

## Progress → Memory Auto-Sync Check
- **What:** Run `python tools/progress-sync.py` to check if progress files have accumulated 7+ updates since last sync
- **When:** Every heartbeat (or at least once per work session)
- **Why:** Ensures repo memory always matches current progress state
- **Action:** If sync is triggered, the script auto-updates `/memories/repo/workspace-state.md`

## Related

- [Heartbeat config](/gateway/config-agents)
