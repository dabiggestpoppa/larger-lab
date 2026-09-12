# BLOC 03 — SENSOR-B3-I08R1 DERIBIT COMPLETION-SEAL EVIDENCE

Status: **SENSOR-B3-I08R1 COMPLETE** — proposed verdict
`PASS_SENSOR_B3_I08R1_DERIBIT_SEALED` (NOT `PASS_BLOC_03`).

## 1. Lineage

| Item | Value |
|---|---|
| Starting SHA | `0ace0ef709b74dcc90463fd6e8ee063cf2878f9c` (branch `agent/crypto-sensor-fabric-build`) |
| I08R1A | `3b6f8c39` — parsers coverage seam + adapter completion block (quality exclusivity, funding demotion, liquidation source coverage) |
| I08R1B | `d44831c7` — quality-matrix / liquidation-trap / funding adversarial tests |
| I08R1C | (this commit) — seal evidence, README, I08 doc correction, ledger |
| Review verdict | HOLD_PASS_SENSOR_B3_I08_DERIBIT_ADAPTER_OFFLINE_PENDING_I08R1_COMPLETION_SEAL |

## 2. Review defects (all three CONFIRMED + FIXED)

- **Defect A — COMPLETE + PARTIAL contradiction.**  The I08 adapter appended
  `PARTIAL_INTERVAL` whenever any semantic row was in-window BEFORE computing
  `is_complete`, so a terminal, fully in-window batch could report
  `is_complete=TRUE` while also carrying `PARTIAL_INTERVAL`.
- **Defect B — funding terminal proof.**  Funding used
  `terminal = len(rows) < DERIBIT_PAGE_LIMIT (1000)` — the characterization
  probe's short-page heuristic.  No committed artifact proves
  `get_funding_rate_history` returns ALL window records whenever
  `len(result) < count`.
- **Defect C — liquidation coverage from the filtered projection.**  The
  liquidation sensor's completion was computed from the projected
  forced-liquidation rows only, so a source page leaking outside the requested
  window (ordinary row outside + liquidation row inside) could be certified
  complete.

## 3. Final quality classification algorithm (I08R1A)

Decision order: completion FIRST, quality flags SECOND.

Coverage truth comes from `ParsedDeribit.coverage_timestamps` — the
schema-validated epoch-ms timestamps of the FULL source page, never from the
projected semantic rows:

- TRADE: coverage == semantic rows.
- LIQUIDATION: coverage == EVERY validated trade row (ordinary + forced
  liquidation); semantic rows == forced-liquidation events only.
- FUNDING: coverage == funding rows (no projection).

Completion:

- BOOK_SNAPSHOT (CURRENT_ONLY): `is_complete=True` per snapshot unit.
- FUNDING: **never** `is_complete=True` (completion_proof = LIMITED; the
  short-page-under-cap rule is a characterization heuristic, not a proven
  provider contract).
- TRADE/LIQUIDATION: `is_complete=True` ONLY when semantic rows non-empty AND
  at least one coverage row is in-window AND ALL coverage rows are inside the
  requested `[start_time, end_time)` window AND `has_more == false`
  (provider-native terminal flag for the current request window).

Quality flags (assigned AFTER the completion decision):

- COMPLETE → NO `PARTIAL_INTERVAL`, NO `GAP_DETECTED`.
- non-empty, not complete, any coverage row in-window → `PARTIAL_INTERVAL`.
- non-empty, not complete, no coverage row in-window → `GAP_DETECTED`.
- empty → `EMPTY_VALID` only (never GAP from an empty response).

`PARTIAL` and `GAP` are mutually exclusive; COMPLETE can never be PARTIAL.

## 4. COMPLETE vs PARTIAL exclusivity — result

Test-proven (`TestQualityFlagMatrix`): a fully in-window `has_more=false`
trade page and a fully in-window terminal liquidation page both report
`is_complete=True` with NO PARTIAL/GAP flags.  A `has_more=true` page reports
PARTIAL only; a no-row-in-window page reports GAP only.

## 5. Funding terminal evidence disposition

**NOT PROVED → FAIL CLOSED.**  Committed evidence reviewed:

- `probe._pagination_state` (characterization): funding done =
  `not rows or len(rows) < page_limit` — a characterization heuristic, which
  per the review instruction is NOT proof of the provider contract.
- `live_probe_contracts.yaml` funding: "window bounded; funding 1h/8h series"
  — describes the windowed request shape, not exhaustive-below-count
  semantics.
- `09_SCHEMA_FINGERPRINTS.jsonl`: five funding era fingerprints, each a
  complete 7-day hourly series (167–168 rows << 1000) — consistent with the
  heuristic in the sampled windows but not a proof of the general contract for
  arbitrary windows.
- `10_CAPABILITY_CLAIMS.jsonl` funding: E4_MULTI_ERA_VERIFIED,
  `history_boundary_confidence: UNKNOWN`.

No dedicated artifact establishes "short page + fully in-window →
terminal/exhaustive" for arbitrary requested windows.  Per the operator's
explicit instruction ("Do NOT assume this merely because the characterization
probe used that heuristic"), funding completion is demoted: **`is_complete`
is always FALSE**, `completion_proof = LIMITED`.  Funding readiness stays
ADAPTER_READY (resume = LIMITED, completion proof = LIMITED).  No capability
was removed — only false certainty.

## 6. Liquidation source coverage vs semantic projection

`ParsedDeribit` gained `coverage_timestamps` (schema-validated source-row
timestamps).  The adapter computes `has_in_window` / `all_in_window` from the
SOURCE page; semantic output remains ONLY forced-liquidation events.  Ordinary
trades never leak into the liquidation view; the raw payload is unchanged and
fully preserved.

## 7. Liquidation filter trap — adversarial result

Fixture `LIQ_TRAP`: source = ordinary trade at T1 − 1 day (OUTSIDE window) +
forced liquidation at T1 (INSIDE window), `has_more=false`.

- LIQUIDATION semantic output: the forced-liquidation row only (row_count 1).
- `is_complete = FALSE` — source-page coverage leaks outside the requested
  window; the filtered projection cannot manufacture completeness.
- Flags: `PARTIAL_INTERVAL` present, `GAP_DETECTED` absent.
- `next_resume_token = None`.

## 8. Trade completion result

Fully in-window + `has_more=false` trade page → `is_complete=True`, clean
flags.  `has_more=true` → PARTIAL, not complete.  No-row-in-window → GAP.
Unchanged from I08 except the flag-exclusivity fix.

## 9. Funding completion result

Never complete: under-cap all-in-window page → PARTIAL + `is_complete=False`;
1000-row count-cap page → not complete; outside-window page → GAP + not
complete.  Completion proof recorded LIMITED.

## 10. Tests / validation

- Deribit provider tests: **178 passed / 0 failed** (+10 over I08's 168).
- Full crypto_sensor_fabric suite: **1252 passed / 0 failed** (parent 1242).
- Deribit PRODUCTION_CANDIDATE conformance: **0 failed** (inside Deribit run).
- Kraken + Gate + OKX regression: 379 passed (green, frozen, unchanged).
- ruff: clean (full repo).  mypy: clean on all changed Deribit modules
  (remaining errors are pre-existing rest.py + Bloc 2 probe.py ClassVar).
- Network calls: **0** (FAKE TRANSPORT ONLY).

## 11. Scope unchanged

- Exactly four Deribit promoted sensors (BOOK_SNAPSHOT CURRENT_ONLY, FUNDING
  SECONDARY, LIQUIDATION + TRADE MECHANISM_MICROSCOPE).
- BTC-PERPETUAL production scope only; ETH/SOL probe-only.
- Endpoints, JSON-RPC error model, raw preservation, schema field contracts,
  epoch-ms INT timestamps (bool rejected), liquidation microscope doctrine,
  verified history bounds, methodology pins, PIT status — all unchanged.
- Historical resume stays LIMITED; no resume token invented.
- No I09 work; no Bloc 4 code; no other provider changes.

## 12. Readiness

| Provider / Sensor | Status | Notes |
|---|---|---|
| DERIBIT / BOOK_SNAPSHOT | ADAPTER_READY | CURRENT_ONLY |
| DERIBIT / FUNDING | ADAPTER_READY | SECONDARY; resume + completion_proof LIMITED |
| DERIBIT / LIQUIDATION | ADAPTER_READY | MECHANISM_MICROSCOPE; resume LIMITED; completion from source coverage |
| DERIBIT / TRADE | ADAPTER_READY | MECHANISM_MICROSCOPE; resume LIMITED |

network_validation: NOT_RUN.
