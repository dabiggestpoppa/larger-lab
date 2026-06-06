# 🔴 PM2 — Sub-Progress Log

> **Agent:** PM2 (Polymorph 2)
> **Role:** Monitor / Test — Watching CC's build progress, verifying plan alignment
> **Reports to:** CC (Claude Code) + OWL (OC2)
> **Last Updated:** 2026-06-03 12:00 UTC

---

## PowerShell/Windows Execution Gotchas

### Encoding Issues
- **Problem:** Windows PowerShell defaults to `cp1252` encoding, breaking emoji and Unicode
- **Fix:** Always set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Symptom:** 🔄✅⚠️ characters appear as `?` or cause silent failures

### Process Invocation
- **Problem:** `Start-Process "openclaw"` opens .ps1 in VS Code instead of executing
- **Fix:** Use `Start-Process -File "path\to\script.ps1"` or `Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "script.py"`
- **For background processes:** Always use `-WindowStyle Hidden` to avoid terminal timeout

### Terminal Management
- **Problem:** Stale terminals accumulate (76+ hours old), causing port conflicts
- **Fix:** Kill old terminals before starting: `Get-Process powershell | Where-Object {$_.StartTime -lt (Get-Date).AddHours(-1)} | Stop-Process`
- **Best practice:** Use `gateway_watchdog.py` for 24/7 monitoring instead of async terminals

### Working Directory
- **Problem:** Scripts with relative paths fail when terminal CWD differs
- **Fix:** Use full paths: `python "C:\Users\wifik\Desktop\projects\larger-lab\scripts\script.py"`
- **Or:** `Set-Location "C:\Users\wifik\Desktop\projects\larger-lab"` before running

### PID Locking (for Python scripts)
- Always implement PID file locks to prevent duplicate instances
- Check `_PID_FILE` before starting critical services (telegram_gateway, etc.)
- Use `taskkill /F /PID <pid>` to kill stale processes

---

## Status: 🟡 MONITORING — Watching CC Build Progress

### Current Assignment (2026-06-03)
- **Monitor CC** — watch his build progress, ensure he's following the plan
- **Do NOT build** unless something is wrong
- **Test** when everything is done
- **Report** to team-chat.md when CC updates

### Sync Infrastructure Status
| Script | Status | Notes |
|--------|--------|-------|
| `tools/progress-sync.py` | ✅ Present | 2-min interval, hash-based change detection |
| `tools/obsidian_vault_sync.py` | ✅ Present | Bidirectional vault sync, 60s interval |
| `tools/gateway_watchdog.py` | ✅ Present | Monitors OC2, Hermes, OCE-BE, OCE-FE, SRRA, Telegram |
| `tools/po_watchdog.py` | ✅ Present | Monitors observer state + chat log |
| `tools/pm2_autopilot.py` | ⚠️ Stopped | Was spamming git with empty commits — killed |
| `scripts/start_telegram_gateway.py` | ⚠️ Exists | Crashes on start (exit code 1) — needs investigation |
| Git sync | ⚠️ Dirty | 20+ "PM2 autopilot" spam commits on master |
| Vault sync | ✅ Running | Obsidian vault sync daemon active |

### Issues Found
1. **PM2 autopilot spam** — 20+ meaningless commits pushed to master. Needs cleanup or autopilot rewrite.
2. **Telegram gateway crash** — `start_telegram_gateway.py` exits with code 1. Likely missing deps or config.
3. **Progress sync daemon not running** — `progress-sync.py` daemon not active, needs restart.
4. **workspace-state.md stale** — Last updated 2026-05-28, doesn't reflect O-5/O-6 completion or ML work.

---

## Previous Work: CEREBUS ML ENGINE — PHASES 2-5 COMPLETE

### CEREBUS ML Build (2026-06-02)
All 5 phases built. 40/40 tests passing.
- Phase 1 (CC): Data pipeline, firewall, Asian Range, K-Means, features, labels
- Phase 2 (PM2): XGBoost regime classifier, entry scorer, SHAP, calibration
- Phase 3 (PM2): Optuna Bayesian optimizer, search spaces, robustness check
- Phase 4 (PM2): Friction filters, parity validator
- Phase 5 (PM2): Guardrail interceptor, PSI drift, shadow mode, Grafana dashboards

### Completed Work (Phase 11 Experimental Track) — ALL COMPLETE
- T11.1 Topology Baseline: PASS (737 nodes, 9 edges, 0 cycles)
- T11.1 Entropy Trace: PASS (6 chaos events, 83% recovery)
- T11.2 Continuity Persistence: PASS (36 checkpoints, 5/5 conditions)
- T11.3 Observer Consensus: PASS (4/4 types, 80-100% rates)
- T11.3 Adversarial Drift: PASS (5/5 tests)
- Observability Stress: PASS (5/5 stress tests, 5/5 validation)
- Tufte Renderers: PASS (4/4 connected to live data)
- Observability Layer (11.2-3B): All 7 stages complete

### SRRA-OPH Frontend Phases 3-5 — COMPLETE (2026-05-24)
- **Phase 3:** ✅ Temporal Playback Engine (timeline core, playback controls, frame interpolation)
- **Phase 4:** ✅ Entropy Field Dynamics (entropy visualization, field maps, perturbation injector)
- **Phase 5:** ✅ Repair + Self-Stabilization visualization (repair cascade, continuity monitor)
- **API Server:** ✅ FastAPI backend at `srrs_opc/frontend/api_server.py` (port 8001)
- All integrated into CC2's topology page structure
- Both frontends running (:3001 SRRA-OPH, :3000 OCE)

### Key Files Built
- `experiments/codegraph/topology_snapshot.py` — AST topology extractor
- `experiments/phase11/test1/entropy_trace.py` — Entropy propagation tracker
- `experiments/phase11/test2/continuity_persistence.py` — Persistence monitor
- `experiments/phase11/test3/consensus_tests.py` — Consensus tests
- `experiments/phase11/test3/adversarial_drift.py` — Adversarial drift tests
- `core/observability/` — Full observability layer (registry, events, temporal, attractors)
- `tools/visualization/exporters/` — 6 export formats
- `tools/visualization/tufte/` — 4 Tufte renderers

### Lessons Learned (from BUILD-NOTES + TEAM-NOTES)
1. ONE system, not many — integrate into OCE, don't build standalone
2. Runtime topology > static structure — use disk for cross-process data
3. Singletons don't persist across processes — use JSON/parquet
4. Continuity > features — validate before building new
5. Test before you update — verify code works before updating progress
6. Don't over-engineer — simplest thing that works
7. UTF-8 encoding required on Windows

### Next Steps
1. ✅ Monitor CC's build progress
2. ✅ Verify sync scripts are up to date
3. ⏳ Test when CC finishes building
4. ⏳ Report to team-chat.md

---

## Completed Work (Historical)

### CEREBUS ML Build (2026-06-02) — COMPLETE
- All 5 phases built. 40/40 tests passing.
- Phase 2: XGBoost regime classifier, entry scorer, SHAP, calibration
- Phase 3: Optuna Bayesian optimizer, search spaces, robustness check
- Phase 4: Friction filters, parity validator
- Phase 5: Guardrail interceptor, PSI drift, shadow mode, Grafana dashboards
