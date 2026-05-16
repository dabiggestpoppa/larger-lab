# HEARTBEAT.md — Periodic Checks

## Progress → Memory Auto-Sync Check
- **What:** Run `python tools/progress-sync.py` to check if progress files have accumulated 7+ updates since last sync
- **When:** Every heartbeat (or at least once per work session)
- **Why:** Ensures repo memory always matches current progress state
- **Action:** If sync is triggered, the script auto-updates `/memories/repo/workspace-state.md`

## Polymorph (PM) — Standby Check
- **What:** Check `progress/polymorph-progress.md` for any tasks assigned by AS or CC
- **When:** Every heartbeat
- **Why:** PM is on standby — needs to pick up tasks as soon as they're assigned
- **Action:** If task found, execute and report back to assigner

## Related

- [Heartbeat config](/gateway/config-agents)
