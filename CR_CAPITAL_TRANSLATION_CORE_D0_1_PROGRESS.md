# CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1 — Progress

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1-CONTRACT-AND-IDEMPOTENCY-TRUTH-REPAIR
**Status:** PASS · **Base:** `18bd63aa` (D0) · **Science:** UNCHANGED

## Repairs (all verified THROUGH the repaired core)
1. **risk_unit_bps argument used in math** — `target_notional` computes
   `E x (f/100) x pos_t x 1e4 / risk_unit_bps` with the explicit argument;
   `ONE_R_NOTIONAL_FACTOR` is a frozen diagnostic constant only.
   `translate()` enforces the frozen science risk unit (24.49489742783178)
   → RiskUnitMismatchError for any other value / unsupported science version.
2. **translation_id account/snapshot-bound** — canonical schema-versioned
   sorted-key JSON serialization (no `|`.join ambiguity) binding event,
   decision, policy/config, account_id, portfolio_group_id, role,
   account_snapshot_id (deterministic SNP- hash of account_id + equity +
   currency + observed_at + profile hash), translation + science versions.
3. **PORTFOLIO_MASTER gate** — canonical A+B book requires role
   PORTFOLIO_MASTER + non-empty portfolio_group_id; EXCLUSIVE_STRATEGY_MASTER /
   FOLLOWER / MIRROR / unknown → blocked (PortfolioAuthorityMismatchError /
   InvalidAccountRoleError).
4. **CapitalDecision consistency** — REJECT → admitted_f == 0; ACCEPT →
   admitted_f > 0 + frozen family-f contract (A 0.70/0.70, B 0.30/0.30 —
   catches 100x unit errors); model heat finite, ≥ −1e-9 (fp-noise bound for
   the −2.2e-16 ledger noise), ACCEPT model_heat_after ≤ 1.00; NaN/+inf/−inf
   on all 7 numeric contract fields → InvalidNumericInputError.
5. **causal known_time** = max(event.entry, decision.timestamp,
   snapshot.observed_at) on timezone-aware timestamps (naive → UTC,
   documented; ledger ts already `+00:00` aware). No wall clock.
6. Typed errors (InvalidFamilyError, InvalidDirectionError,
   InvalidAccountRoleError, PortfolioAuthorityMismatchError,
   CapitalDecisionConsistencyError, RiskUnitMismatchError,
   InvalidNumericInputError, InvalidTimestampError) + full output audit chain
   (decision_id, requested_f, model heats, config/profile/portfolio hashes,
   account_snapshot_id).

## 890-event nonregression (through the REPAIRED core)
- 890 events · A 432 / B 458 · 826 ACCEPT_FULL (A 371 / B 455) · 64 REJECT
- gross parity max err **9.35e-15** · research net max err **9.39e-15**
- notional distribution UNCHANGED vs sealed canonical stats (pooled
  1.9842 / 7.6105 / 16.0364 / 32.7663; A 3.3513 / 11.4407 / 32.7663;
  B 1.2850 / 4.1231 / 22.2754)
- rejected → NO_EXPOSURE zero exposure (all 64); 890 unique translation_ids
- H1 / family / model heat never recomputed (source-level + decision truth)

## Cross-workstream (read-only, diagnostic)
- execution-runtime-foundation HEAD: `4f318a8f` (QL-EXEC-R2-MT5-BROKER-
  SESSION-EXTRACTION) — advanced past the R1.1 freeze; EconomicTarget /
  BoundAccountSnapshot contracts remain compatible; not imported.
- tb-forward-engine: `d1200598` (TB-R6.1B) — PROVEN_ENGINEERING_REFERENCE,
  untouched.

## Tests
- `tests/test_capital_translation_core_d0_1.py`: 49 tests (32 required
  adversarial checks + parity/nonregression/purity)
- `tests/test_capital_translation_core_d0.py`: 32 (updated for
  snapshot-bound id semantics; the family-f contract caught a latent
  B-event helper bug in the old tests — exactly what it is for)
- Full combined suites (D0, D0.1, R1, R1.1, R1.1B): **144/144**
- Determinism: byte-identical re-run

## Artifacts
`research/capital_routing/risk/block4_capital_translation_core_d0_1/`
(16 required + EVENT_TRANSLATIONS.csv) — start with
`CR_BLOCK4_D0_1_DEFECT_AUDIT.md`, `CR_BLOCK4_D0_1_DECISION.json`.

## Decision
d0_1_pass=true · d1_plan_ready=true · d1_plan_authorized=false ·
production_authorized=false · broker_execution_performed=false ·
broker_fields_added=false · human_review_required=true.
**Next (NOT started):** CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN
