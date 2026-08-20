# CTBT T3 — Transfer-Candidate Seal & Forward-Shadow Preregistration

**Checkpoint:** `SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION`
**Base:** `d08502793fd0ca96eb65e78d12ed85eea6389073` (T2, FOCUSED_TRANSFER_FAMILY)
**Status:** **PASS_TRANSFER_FAMILY_SEALED_FORWARD_PREREGISTERED**

## 1. What this checkpoint is

Candidate **seal** + **forward-evidence contract** + **runtime-mapping
specification** for the two historically confirmed transfer candidates. It
performs **no** historical optimization, changes no parameters, opens no new
candidate baskets, places no orders, and authorizes no capital.

## 2. Sealed candidates

| Version ID | Strategy hash | T1.1 (dev) | 2025 confirmation | Transport |
|---|---|---|---|---|
| `CTBT-EUR-GBP-USD-v1` | `aad0a8e64c696495…` | N=435, EV +15.74, PF 5.42, WR 78.2%, ratio 2.88 | N=146, EV +17.75, PF 5.52, WR 77.4%, ratio 3.20 | TRANSPORT_CONFIRMED |
| `CTBT-GBP-NZD-USD-v1` | `5538d63a8acb2988…` | N=210, EV +22.84, PF 8.02, WR 84.3%, ratio 3.56 | N=81, EV +11.87, PF 5.82, WR 74.1%, ratio 2.33 | TRANSPORT_DECAYED_BUT_POSITIVE |

Full specs and hashes: `CTBT_T3_STRATEGY_HASHES.json` (sha256 over the
canonical, deterministically serialized strategy specification — the
immutable contract a runtime must reproduce exactly).

## 3. Frozen contract (both candidates)

M5 · rolling z 200 completed bars, population std ddof=0, current bar
excluded, closed-bar causal · strict |z| > 3.0 entry · W2 exact-neutral
(MODEL GEOMETRY only) · E1 signed overshoot ±0.25 · |z| > 6 structural
invalidation · canonical London 03:00–12:00 EST · 120 min minimum runway ·
canonical noon hard exit · concurrency 1 · canonical deterministic re-entry.
Cost: `HISTORICAL_MODELED_COST_CONTRACT` (frozen T1.1 conservative method) —
explicitly **not** claimed equal to realized forward execution cost.

Basis orientations and leg-side (buy/sell) mappings are frozen explicitly
(`CTBT_T3_BASIS_ORIENTATION.json`, `CTBT_T3_LEG_SIDE_MAPPING.json`) — no
dynamic orientation inference at runtime.

## 4. Forward-shadow program

- **Start:** strictly after the T3 commit timestamp; no historical event may
  be relabeled as forward evidence.
- **Horizon:** event-count driven — 15 early diagnostic, 30 minimum useful,
  50 preferred. 15 is diagnostic only, never validation.
- **Evidence states:** INSUFFICIENT_EVENTS / MECHANISM_ALIGNED /
  MECHANISM_WEAKENED / MECHANISM_BROKEN / COST_MARGIN_HEALTHY /
  COST_MARGIN_TIGHT / COST_MARGIN_BROKEN — labels only, no trading
  authorization.
- **Completeness:** independent signal-completeness auditor
  (`CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md`) reconstructs eligible signals
  independently from raw M5 data with the frozen engine (MATCHED_SHADOW /
  VALID_RUNTIME_BLOCK / MISSED_SIGNAL / RUNTIME_ONLY_SIGNAL /
  DATA_DIVERGENCE / NO_SIGNAL); 100% recognition target, misses are
  individual failures.
- **Costs:** per-signal provider cost snapshot (bid/ask/mid/spread per leg,
  modeled vs observed quote-crossing basket cost, observed/model multiple).
  Providers (MT5 vs TradeLocker) remain separate in diagnostics.
- **Comparison:** forward results compared separately against development and
  2025-confirmation fingerprints — never pooled.

## 5. Runtime architecture

`FrozenTransferCandidate → StrategyAdapter → provider-neutral market data →
shadow signal/event ledger`, reusing the existing execution abstractions
(`triangular_execution_contract.py`, `mt5/execution_layer.py`,
`mt5/production_runtime.py`, `config/spread_commission_config.py`). **No
order path, no account mutation, no capital routing, no sizing.** Registry
status: `HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE` (not LIVE, not
PRODUCTION, not CAPITAL_ELIGIBLE).

## 6. Family & independence

Family `CANONICAL_TB_TRANSFER_FAMILY`: AUD_GBP_NZD (CANONICAL_REFERENCE),
EUR_GBP_USD (CONFIRMED_TRANSFER), GBP_NZD_USD (CONFIRMED_TRANSFER_DECAYED).
No PnL pooling, no portfolio/correlation/capital work yet, no portfolio
optimization. Candidates promote independently — EUR_GBP_USD may pass forward
while GBP_NZD_USD fails. Canonical AUD_GBP_NZD is untouched and takes
priority. GBP_NZD_USD monitoring is weighted against its 2025 confirmation
(not development) given its recorded transport decay.

## 7. Promotion & failure

Demo consideration requires per candidate: ≥30 natural forward events,
positive net EV, PF > 1.20, no mechanism break, positive cost margin,
acceptable completeness, intact causality, acceptable runtime/data parity
(preferred ≥50). These are minimum *consideration* gates — not automatic
authorization. Failure: FORWARD_MECHANISM_FAILED with no automatic retuning;
a failed v1 is sealed. Early scientific stop (<30 events) only for
catastrophic evidence (causality failure, runtime mismatch, mechanism
inversion, cost impossibility, data invalidity).

## 8. Decision

`production_authorized = false` · `human_review_required = true` ·
`runtime_shadow_ready = false` · `demo_execution_authorized = false` ·
`capital_routing_authorized = false`. Next checkpoint (if authorized):
`SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION` — engineering
integration only, no demo/live execution, no strategy-science changes.
