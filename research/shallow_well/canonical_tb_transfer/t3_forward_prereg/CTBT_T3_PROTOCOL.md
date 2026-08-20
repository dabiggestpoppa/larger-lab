# CTBT T3 — Transfer-Candidate Seal & Forward-Shadow Preregistration Protocol

**Checkpoint:** `SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION`
**Authoritative base:** `d08502793fd0ca96eb65e78d12ed85eea6389073` (T2)
**Parent status:** `FOCUSED_TRANSFER_FAMILY`

---

## 1. Mission

Seal the two historically confirmed Canonical TB transfer candidates and
preregister their future **forward-shadow** evidence program.

This checkpoint **must NOT**:

- run new historical optimization
- change parameters
- open new candidate baskets
- change costs to improve results
- place demo orders
- place live orders
- authorize production

This checkpoint **is**: CANDIDATE SEAL + FORWARD-EVIDENCE CONTRACT +
RUNTIME-MAPPING SPECIFICATION.

## 2. Frozen confirmed family

1. `EUR_GBP_USD` → version `CTBT-EUR-GBP-USD-v1`
2. `GBP_NZD_USD` → version `CTBT-GBP-NZD-USD-v1`

No other candidate enters T3.

## 3. Historical research is closed

`historical_optimization_complete = true`,
`additional_historical_testing_authorized = false`. No z grids, exit grids,
session/weight/cost tuning, day/volatility/direction filters, or new
triangles. 2020–2025 is **consumed research evidence** for these exact
strategy versions.

## 4. Frozen strategy contract (both candidates)

| Element | Frozen value |
|---|---|
| Timeframe | M5 |
| Rolling z | 200 completed bars, population std ddof=0, current bar excluded, closed-bar causal |
| Entry PRIMARY | strict \|z\| > 3.0 |
| Weight | W2 exact-neutral (MODEL GEOMETRY only) |
| Exit | E1 signed overshoot ±0.25 |
| Structural invalidation | \|z\| > 6 |
| Session | canonical London 03:00–12:00 EST, fixed contract |
| Minimum runway | 120 minutes |
| Hard exit | canonical noon |
| Concurrency | 1 active basket per strategy instance |
| Re-entry | canonical deterministic lifecycle |

No runtime implementation may modify these. Any change creates a NEW
strategy version.

## 5. Basis & leg-side freezing

- `EUR_GBP_USD`: `b = ln(EURGBP) − ln(EURUSD) + ln(GBPUSD)`; identity
  `EURGBP × GBPUSD == EURUSD`.
- `GBP_NZD_USD`: `b = ln(GBPNZD) − ln(GBPUSD) + ln(NZDUSD)`; identity
  `GBPNZD × NZDUSD == GBPUSD`.
- z > +3 → SHORT basket (short A, long B, short C); z < −3 → LONG basket
  (long A, short B, long C).
- Stored explicitly; runtime must not infer orientation dynamically.

## 6. Cost truth

- Historical confirmation used the frozen T1.1 conservative methodology →
  `HISTORICAL_MODELED_COST_CONTRACT`. It is **not** equal to realized
  forward execution cost.
- Forward shadow collects actual provider-side cost evidence per eligible
  signal: provider, account environment, symbol mapping, decision timestamp,
  per-leg bid/ask/mid/spread, basket modeled cost, basket observed
  quote-crossing cost, observed/model multiple.
- If later demo fills exist, slippage and commissions are measured
  separately. T3 itself places no orders.

## 7. Forward-shadow purpose (six questions)

1. Does the signal continue to occur naturally?
2. Does the frozen mechanism remain positive prospectively?
3. Are real provider costs compatible with historical economics?
4. Does runtime reproduce research signals completely?
5. Does event frequency remain within plausible historical variation?
6. Does GBP_NZD_USD continue to show greater decay than EUR_GBP_USD?

## 8. No forward retuning

Once sealed, future results must not change z, exit, session, weights, stop,
cost gate, or trade selection. Any change = new version.

## 9. Forward start

Forward evidence begins strictly after the T3 commit timestamp. No
historical event may be relabeled as forward evidence.
`forward_start_timestamp` = first causally complete M5 bar after T3 sealing.

## 10. Event-count stopping

| Horizon | Events |
|---|---|
| Early diagnostic | 15 |
| Minimum useful | 30 |
| Preferred | 50 |

15 is diagnostic only — not validation. Calendar time is reported but not
decisive. Review points: monthly engineering audit, quarterly scientific
context review. No parameter changes at reviews.

## 11. Forward metrics

signals, completed events, events/week, gross EV, net modeled EV, net
observed-cost EV, WR, median EV, PF, payoff ratio, max DD, p5, worst event,
losing streak, MAE, MFE, hold distribution, z6 rate, hard-exit rate,
signal-time cost distribution, provider cost multiple distribution.
Forward results compared separately against development and 2025-confirmation
fingerprints — never pooled.

## 12. Expectancy states

`INSUFFICIENT_EVENTS`, `MECHANISM_ALIGNED`, `MECHANISM_WEAKENED`,
`MECHANISM_BROKEN`, `COST_MARGIN_HEALTHY`, `COST_MARGIN_TIGHT`,
`COST_MARGIN_BROKEN`. Evidence labels only — they do not authorize trading.

## 13. Reference bands

- EUR_GBP_USD: dev EV ≈ 15.74, conf EV ≈ 17.75, PF ≈ 5.52, WR ≈ 77.4%,
  cost ratio ≈ 3.20. Reference distributions, not quotas.
- GBP_NZD_USD: dev EV ≈ 22.84, conf EV ≈ 11.87, PF ≈ 5.82, WR ≈ 74.1%,
  cost ratio ≈ 2.33. Already showed material transport decay — monitor
  primarily vs the 2025 confirmation; do not auto-kill for EV below
  development.

## 14. Completeness & independent replay

Independent signal-completeness auditor patterned after the canonical TB
weekly audit (see `CTBT_T3_SIGNAL_COMPLETENESS_SPEC.md`). Reconstruct
eligible signals independently from raw completed M5 data with the frozen
candidate engine — never merely reread runtime signal logs. Recognition
target 100%; misses are individual failures. Classifications: MATCHED_SHADOW,
VALID_RUNTIME_BLOCK, MISSED_SIGNAL, RUNTIME_ONLY_SIGNAL, DATA_DIVERGENCE,
NO_SIGNAL. Data parity: store bar timestamps, OHLC, spread, provider
provenance, symbol mapping, missing bars — distinguish strategy failure from
data/provider divergence.

## 15. Provider scope

Primary: existing MT5 provider-neutral runtime path. TradeLocker may
participate once its read-only provider layer is available. Providers stay
separate in cost diagnostics; never pool MT5 and TradeLocker observations
blindly.

## 16. Runtime architecture

Use existing Execution Runtime abstractions; no parallel broker stack inside
Shallow Well. Flow: `FrozenTransferCandidate → StrategyAdapter →
provider-neutral market data → shadow signal/event ledger`. No order path in
T3. T3 does not invoke CapitalPolicyAdapter, CapitalTranslationAdapter,
EconomicTarget sizing, or broker order routing. Shadow quantities normalized
for economics only. Registry status:
`HISTORICALLY_CONFIRMED_FORWARD_SHADOW_CANDIDATE` — not LIVE, not
PRODUCTION, not CAPITAL_ELIGIBLE.

## 17. Canonical TB noninterference

AUD_GBP_NZD remains a separate strategy version, evidence program, runtime
slot, and completeness audit. T3 may share infrastructure but must not share
evidence ledgers. No candidate may delay or alter canonical TB Forward.

## 18. Family relationship

Family = `CANONICAL_TB_TRANSFER_FAMILY`; members: AUD_GBP_NZD
(CANONICAL_REFERENCE), EUR_GBP_USD (CONFIRMED_TRANSFER), GBP_NZD_USD
(CONFIRMED_TRANSFER_DECAYED). Do not combine PnL. Portfolio/correlation/
capital work is later. No portfolio optimization (no combined PnL,
allocation ratios, Kelly, risk parity, correlation weighting, portfolio PF).

## 19. Promotion contract

Before demo execution may even be considered, per candidate: ≥30 natural
forward events, positive forward net EV, PF > 1.20, no mechanism break,
positive cost margin, acceptable signal completeness, intact causality,
acceptable runtime/data parity; preferred ≥50. Minimum *consideration* gates,
not automatic authorization. Candidates promote independently.

## 20. Failure logic

`FORWARD_MECHANISM_FAILED` when sufficient events show persistent negative
EV, clear mechanism-sign reversal, or transaction costs systematically
dominating gross edge. No automatic historical retuning; a failed v1 is
sealed. Early scientific stop (<30 events) only for catastrophic evidence:
causality failure, strategy/runtime mismatch, gross mechanism inversion,
severe cost impossibility, data invalidity. Do not stop for an ordinary
losing streak.

## 21. Artifacts & decision

25 artifacts under `research/shallow_well/canonical_tb_transfer/
t3_forward_prereg/` per master prompt. Expected status:
`PASS_TRANSFER_FAMILY_SEALED_FORWARD_PREREGISTERED`. Next checkpoint (if
authorized): `SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION` —
engineering integration only; it does NOT authorize demo/live execution or
strategy-science changes.

**NO ORDERS. NO CAPITAL. NO LIVE.**
