# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1 -- Protocol

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1-CONTRACT-AND-IDEMPOTENCY-TRUTH-REPAIR
**Base:** 18bd63aa36f9174aa3fb340f50c631e05edc5580 (D0 core) · **Branch:** capital-routing
**Parent:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0 (18bd63aa)
**Type:** implementation-contract / idempotency truth repair of the PURE core
(no broker/runtime code, no science change)

## Mission
Repair four implementation truth defects + causal timestamp semantics:

1. **risk_unit_bps argument ignored** -> arithmetic now uses the explicit
   argument (N = E x (f/100) x pos_t x 1e4 / risk_unit_bps); translate()
   enforces the frozen science risk unit 24.49489742783178 (RiskUnitMismatchError).
   `ONE_R_NOTIONAL_FACTOR` remains a frozen diagnostic reference constant only.
2. **translation_id not account-bound** -> canonical schema-versioned
   sorted-key JSON serialization binding event, decision, policy/config,
   account_id, portfolio_group_id, role, account_snapshot_id, translation +
   science versions. Same complete inputs -> same id; different account /
   profile / frozen equity snapshot -> different id.
3. **PORTFOLIO_MASTER invariant** -> canonical A+B book requires role
   PORTFOLIO_MASTER + non-empty portfolio_group_id; EXCLUSIVE_STRATEGY_MASTER /
   FOLLOWER / MIRROR blocked (PortfolioAuthorityMismatchError).
4. **CapitalDecision consistency** -> contradictory immutable inputs rejected,
   never silently repaired: REJECT -> admitted_f == 0; ACCEPT -> admitted_f
   > 0 and frozen family-f contract (A 0.70/0.70, B 0.30/0.30); model heat
   finite, >= 0 (fp tolerance), ACCEPT model_heat_after <= 1.0.
   NaN / +/-inf on all numeric contract fields fail closed.
5. **causal known_time** = max(event.entry, decision.timestamp,
   snapshot.observed_at) on timezone-aware timestamps (naive -> UTC per
   sealed ledger semantics; no wall clock).

## Frozen science (untouched)
890 events (A 432 / B 458); A1_70_30 + H1-1.00-REJ: 826 ACCEPT_FULL
(A 371 / B 455) / 64 REJECT_HEAT_CAP; requested_f A 0.70 / B 0.30; f_total
1.00%; 1R = 24.49489742783178 bps = NORMALIZED EXPECTED-MOVE UNIT, NOT a hard
stop / max loss / broker stop. Gross + research-modeled net parity and the
canonical notional distribution must be unchanged (verified through the
repaired core over all 890 events).

## Boundary
No AccountRegistry implementation, no broker, no MT5/TradeLocker, no runtime
supervision, no orders/fills, no margin/buying power. The core validates the
SUPPLIED AccountBindingReference / BoundAccountSnapshot only; the
execution-runtime-foundation workstream remains authoritative for account
control-plane mechanics.

## Pass gate
risk-unit argument used · frozen R enforced · NaN/inf fail closed ·
translation_id account+snapshot bound with canonical serialization ·
PORTFOLIO_MASTER required · contradictory decisions rejected · family-f
contract enforced · causal known_time · 890-event economics identical ·
no broker/runtime functionality · all tests pass.
