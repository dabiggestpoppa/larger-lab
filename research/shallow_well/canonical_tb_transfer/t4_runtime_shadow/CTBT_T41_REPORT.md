# CTBT T4.1 — Forward Collector Activation + Transfer Dashboard

**Checkpoint:** `SW-CTBT-T4.1-FORWARD-COLLECTOR-AND-TRANSFER-DASHBOARD-ACTIVATION`
**Base:** `0758608f509d4402bf82dc69e51f091e3609a355` (T4)
**Status:** **PASS_FORWARD_COLLECTOR_RUNNING_AND_DASHBOARD_LIVE**

---

## Part A — Persistent forward-shadow collector: RUNNING

`ctbt_runtime/run_shadow_loop.py --start` (PID 21940, PID-locked singleton,
read-only) is live against OxSecurities-Demo:

- Provider connected; both sealed strategies loaded by exact T3 hash
  (hash-drift refusal active).
- **Time-axis integrity fix (critical):** broker server time is UTC+3; the
  feed now measures the server offset at init and normalizes every bar to
  **real UTC**, matching the research axis (activation timestamp, first
  eligible bar, session mapping). Bars land on clean `:00`/`:05` marks.
- **Forward-evidence filter:** only events with `decision_bar_timestamp >=
  2026-08-20T13:05:00Z` (first eligible bar, strictly after activation) may
  enter a ledger — the pre-activation smoke event can never be relabeled.
- **Restart safety:** last-processed bar per triangle persisted to
  `state/processed_<tri>.json` and seeded from the ledger max on start — a
  restart never duplicates signals, resets counts, rewrites the activation
  timestamp, or truncates ledgers (3/3 collector tests pass).
- **Operator status heartbeat:** `CTBT_T4_OPERATOR_STATUS.json` updated each
  tick (collector pid, provider, last bar, heartbeat, event counts,
  recognition rate, order-prevention status) — the authoritative operational
  state the dashboard reads.
- Forward clock remains authoritative; completed forward events so far:
  **EUR_GBP_USD 0, GBP_NZD_USD 0** (correct — waiting for natural signals).

## Part B — Transfer Family dashboard: LIVE at http://127.0.0.1:8766

Cloned from the existing canonical TB dashboard (same stdlib server, dark
monospace theme, status cards/tables, 5s refresh) — **visual consistency, no
redesign**. One app, navigation:

1. **FAMILY OVERVIEW** — status-only summary of both candidates + system health
2. **EUR / GBP / USD** — full strategy page
3. **GBP / NZD / USD** — full strategy page
4. **CANONICAL TB** — link to the existing dashboard on 8765 (unchanged)

Each strategy page shows: version + hash, FORWARD SHADOW ACTIVE header with
Provider / READ ONLY / Execution DISABLED / Capital DISABLED, forward clock,
demo-canary progress (X/10 events + X/28 days, `NOT ELIGIBLE`, never shown as
validated/ready), 10/15/30/50 event horizons with progress bars, forward
performance (metrics withheld → **INSUFFICIENT EVENTS** until N ≥ 10),
historical reference cards (development + 2025 confirmation, labeled **NOT
pooled**), broker reality (modeled basket cost, observed signal-time crossing
when it exists, cost margin state), signal-completeness panel (six classes +
recognition rate with engineering warnings), and recent events table
(`0 EVENT / WAITING FOR NATURAL SIGNAL` when empty).

Evidence isolation: the dashboard reads only CTBT state — it never reads
canonical data, and canonical evidence is never pooled with forward evidence.

## Verification

24/24 checks pass (`CTBT_T4_VERIFICATION.json`): base SHA, seal/timestamps
unchanged, single-instance collector, provider connected, bars updating, both
hashes exact, separate ledgers, replay + cost capture active, order
prevention PASS, restart-safe markers, canonical dashboard unaffected (8765
still live), transfer dashboard loads, zero-event state correct, progress
displays correct, completeness accurate, no pooling, no fake metrics,
production/capital false.

## Final state

| Element | State |
|---|---|
| collector | RUNNING |
| forward shadow | ACTIVE |
| dashboard | TRANSFER FAMILY VIEW LIVE (127.0.0.1:8766) |
| canonical TB | UNCHANGED (127.0.0.1:8765) |
| historical lab | CLOSED |
| research mode | PROSPECTIVE ONLY |
| demo execution | NOT AUTHORIZED |
| production | NOT AUTHORIZED |

## Next steps

WAITING / FORWARD OBSERVATION. No daily commits because no signal occurred.
Next evidence hinge: a candidate reaching ≥10 clean natural forward events
**and** ≥28 days **and** all T4 demo-canary gates → then recommend
`SW-CTBT-T5-DEMO-EXECUTION-CANARY` (human authorization required). No
research checkpoints are created until then.
