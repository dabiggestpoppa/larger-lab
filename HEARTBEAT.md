# HEARTBEAT.md — Periodic Checks & Self-Healing

## 🦉 OWL Self-Healing Startup Check
- **What:** Run `python tools/self_heal.py --full` to scan gateway logs, classify errors, log to DB, create bug annotations, and auto-fix known issues
- **When:** First heartbeat after gateway restart, or every 4th heartbeat (whichever comes first)
- **Why:** Detect errors that occurred while OWL was offline, track recurring issues, auto-resolve known patterns
- **Action:** 
  1. Run `python tools/self_heal.py --full`
  2. If new errors found, review bug files in `bugs/open/`
  3. If critical errors found, notify MAD via Telegram
  4. Update `progress/rl-progress.md` with findings
- **DB Location:** `db/owl_health.db`
- **Bug Files:** `bugs/open/` and `bugs/resolved/`

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

## 🧠 Creative Think Activation
- **What:** When MAD's message is abstract, philosophical, or requires cross-domain synthesis, activate Creative Think skill
- **When:** On demand — triggered by nature of the request, not by schedule
- **Why:** Abstract problems need structured lateral reasoning, not linear decomposition
- **Skill:** `skills/creative-think/SKILL.md`
- **Framework:** LATTICE (Layer, Analogy, Tension, Transform, Integrate, Challenge, Express)

## 🔧 Self-Surgery Safety Rules
- **What:** OWL can edit its own workspace files (SOUL.md, MEMORY.md, skills, tools, etc.) using the self-surgery module
- **Rules:**
  1. ALWAYS read file completely before editing
  2. ALWAYS create backup before editing (auto-handled by `tools/self_surgery.py`)
  3. ALWAYS validate after editing (syntax check for .py, structure check for .md)
  4. NEVER edit openclaw.json directly — use `gateway` tool
  5. NEVER edit files in node_modules/, .git/, or .surgery-backups/
  6. ALLOG log what was changed and why to `db/owl_health.db`
- **Backups:** `.surgery-backups/` directory
- **Restore:** `python tools/self_surgery.py restore <backup_name>`

## Related

- [Heartbeat config](/gateway/config-agents)
- [Self-Healing Engine](tools/self_heal.py)
- [Self-Surgery Module](tools/self_surgery.py)
- [Creative Think Skill](skills/creative-think/SKILL.md)
- [Error Database Schema](db/schema.py)
