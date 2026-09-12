# G5R — DOMAIN EVIDENCE / DOCTRINE / SENSOR / TRANSFER INTEGRITY HARDENING — RESULT

**STATUS:** `PASS_G5R_DOMAIN_EVIDENCE_INTEGRITY`

| Field | Value |
|---|---|
| Starting SHA | `56c0605d5924b703603612327c89dfa15367914e` (verified == reported HEAD; delta 463495c3..56c0605d, 10 commits, 0 behind) |
| Artifacts head | `181b2589` (STRESS-G5RX, last code/artifact commit; G5RR archive commit follows) |
| Test total | **766 / 766** (684 preserved + 82 G5R) |
| Shared policy | `G5_DOMAIN_EPISTEMIC_POLICY` V1 (+2 governed availability rules), zero scenario-id predicates |
| Model calls / mutations | 0 / cloud=0 production=0 capital=0 authority=NONE cost=$0 |
| G6 | **NOT begun.** S20–S24 NOT implemented. |

## Core law — enforced, not asserted

Every fixture-declared truth path found by external review was closed in code:

| Law | Mechanism |
|---|---|
| CLAIMED INDEPENDENCE != VERIFIED INDEPENDENCE | `derive_independence()` resolves `independence_evidence_refs` through the governed EvidenceRegistry; the `evidence_lineages` integer is display-only |
| CLAIMED REPRODUCTION QUALITY != REPRODUCTION QUALITY | `derive_reproduction_quality()` compares the frozen ReproductionProtocol against the claim's applicability contract; `known_deviations=[]` cannot launder a structured mismatch |
| CLAIMED CONTRADICTION != MEASURED CONTRADICTION | `compare_measured_result()` derives SUPPORTS / INCONCLUSIVE / CONTRADICTS from the observed interval vs the doctrine band; fixture strings have no vote |
| AVAILABLE != ADEQUATE | `assess_sensor_adequacy()` / `DataAvailabilityRecord.adequate_history()` check the full requirement vector + provenance; governed policy rules keep AVAILABLE-but-inadequate sensors DATA_BLOCKED |
| PROTOCOL_FROZEN=true != RESOLVED FROZEN PROTOCOL | `resolve_frozen_target_protocol()` requires a registered protocol whose target_domain matches and whose fingerprint is valid |
| RATIFIED=true != GOVERNED RATIFICATION | `govern_amendment_ratification()` binds actor + AuthorityState level + prior proposal; OPERATOR-only; the manual file is never rewritten |

## G5R items → status

- **G5R-01 S15 evidence-path independence** — DONE. `evidence_lineages=99` with 0 registered refs → UNRESOLVED (CASE A). Zero refs = zero verified observations (never one). Two refs on one lineage = one lineage. Two verified distinct lineages → CONFIRMED. Unknown lineages never count favorably. No effective-sample-size scalar produced.
- **G5R-02 evidence-bound clusters** — DONE. `cluster_verified_observation_paths()` dedupes to unique verified paths; similarity grouping never upgrades independence.
- **G5R-03 disposition-gated mechanism admission** — DONE. `decide_mechanism_admission()`: UNRESOLVED_PATTERN / DATA_BLOCKED / POLICY_HOLD → PROPOSED_MECHANISM (no frozen protocol emitted); ONTOLOGY_EXPLORATION_CANDIDATE → ADMITTED_MECHANISM_FOR_EXPERIMENT. Fixture presence of the card file is not admission.
- **G5R-04 source binding** — DONE. The stored digest is now the true 64-hex SHA-256 of the manual file (the old fixture value was 32 hex while labeled SHA-256); the runner recomputes from the actual file and fails closed (`wrong_manual_digest_rejected`, `stale_manual_digest_rejected` → STALE_DIGEST). Source file bytes verified unchanged.
- **G5R-05 exact claim atoms** — DONE. The composite cross-section sentence was removed; the Target Metric table (`Win Rate (Filtered) 85% – 90%; Daily Goal 1.0% – 1.5%; Max Daily Drawdown < 0.50%; Prop Firm Circuit Breaker 0.40%`) is one bounded atom; pre-session conditions / tier sizing / P90 thresholds are separately bound applicability atoms with per-fragment digests.
- **G5R-06 derived reproduction quality** — DONE. ReproductionProtocol (all governed fields, frozen before result) + derived quality; wrong session/tier/PIT/fingerprint each → FLAWED → REPRODUCTION_REJECTED (CASE B without any declared deviation); post-result protocol change changes the fingerprint and invalidates comparison.
- **G5R-07 measured contradiction** — DONE. ObservedResult(metric, estimate, interval, n) + generic comparator (CASE C: string spoof yields zero contradictions; in-band → SUPPORTS; materially outside → CONTRADICTS; overlap → INCONCLUSIVE).
- **G5R-08 separation** — PRESERVED. DoctrineClaim / ReproductionProtocol / ObservedResult / ReproductionQualityAssessment / DoctrineComparison / DoctrineContradictionRecord remain separate objects; no overwrite in either direction.
- **G5R-09 governed ratification** — DONE. Proposal ≠ amendment; ratification binds actor + AuthorityState level + proposal id + basis + scope + claim id; OPERATOR only; worker rejected; manual bytes unchanged (CASE D).
- **G5R-10 provider+metric semantics key** — DONE. `(provider, metric)` indexing; missing contract → SEMANTIC_CONTRACT_MISSING / DATA_INSUFFICIENT / SOURCE_DIAGNOSTIC_REQUIRED (fail closed, emitted as diagnostics, never silently skipped or compared).
- **G5R-11 adapter version validation** — DONE. Observation adapter must equal the registered contract version unless an explicit compatible-version list admits it; blank fails (CASE E detected before normalization).
- **G5R-12 missing normalized value** — DONE. `normalized_value: Optional`; absent → NORMALIZATION_MISSING / DATA_INSUFFICIENT; never coerced to 0.0 (CASE F).
- **G5R-13 time/quality/contract semantics** — DONE. Window, timestamp semantics, quality contract, canonical instrument and pairwise contract-type all enforced (spot vs perp mismatch localized).
- **G5R-14 NO_DISAGREEMENT terminal fix** — DONE. Equal clean values terminate NO_DISAGREEMENT / NO_DISAGREEMENT — never GENUINE_SOURCE_DISAGREEMENT.
- **G5R-15 tolerance contract** — DONE. `DisagreementToleranceContract` (absolute/relative/bps) wired into the diagnosis; tiny rounding differences are not material, real disagreements preserved. Provisional; values not constitutionalized.
- **G5R-16 full-vector adequacy** — DONE. Observable, status, verified, provenance, resolution, structured history (HistorySpan — no naive string equality), instrument coverage, time semantics, quality minimum. Wrong resolution/instrument/time/history each → not adequate → DATA_BLOCKED (CASE G/H).
- **G5R-17 provenance** — DONE. `AUTHORITATIVE_SYNTHETIC_SENSOR_FIXTURE` / `CRYPTO_SENSOR_FABRIC_CERTIFICATION` required; UNKNOWN provenance → not adequate.
- **G5R-18 evidenced sensor arrival** — DONE. `SensorCapabilityChangeRecord` (observable, old/new state, source, evidence refs, certification, effective epoch, history coverage). The legacy boolean can flip status only — never verification/certification — and is reported NON_AUTHORITATIVE. A registered certified change can reopen. Arrival never retroactively validates history.
- **G5R-19 SearchDemand semantics** — DONE. `required_instruments` separated from `acceptable_source_classes`; BTC_USDT_PERP is never stored as a provider (legacy display field retained, marked LEGACY).
- **G5R-20 transfer-map axes** — DONE. `validate_transfer_map()` checks all 13 axes; blank mandatory axis ≠ STRUCTURALLY_SOUND; declared broken assumptions invalidate soundness (CASE J → ANALOGY_ONLY).
- **G5R-21 real frozen target protocol** — DONE. Ref must resolve; target domain must match (wrong-domain protocol rejected); fingerprint must validate; boolean alone cannot authorize (CASE I).
- **G5R-22 governed target data** — DONE. S19 target data runs the same SensorRequirement/DataAvailability/adequacy vector as S18; `target_data_available=True` is recorded as NON_AUTHORITATIVE_TEST_CONVENIENCE and cannot flip DATA_BLOCKED.
- **G5R-23 source evidence refs** — DONE. Unknown refs fail closed (phantom ref → not resolved → never DOMAIN_VALIDATION_REQUIRED); registered crypto evidence preserved as CRYPTO; `source_validation_as_target_validation=false` enforced.
- **G5R-24 S14 promotion vocabulary** — DONE. VALIDATION_PASS / REJECTED (B7ValidationResult) ≠ PROMOTION_CANDIDATE / REJECTED / HOLD (ResearchPromotionDecision) ≠ execution authority (NONE). Receipt carries no contradictory labels (`"PROMOTED"` absent; old dual use documented in the test).
- **G5R-25 B7 gate contract** — DONE. Versioned `B7GateContract` v1.0 sourced to OCE-B7-PLAN-001: PIT_INTEGRITY + EXECUTION_REALISM + OOS_WALK_FORWARD BLOCKING (B7.C1.S5, B7.C2.S4, B7.C3.S2/S3/S5); COST_SENSITIVITY + FAMILY_MULTIPLICITY ADVISORY (B7.C3.S4/S5); MECHANISM_PLAUSIBILITY CONDITIONAL (B7.C2.S1); REPRODUCIBILITY + SENSITIVITY_STRESS NOT_EXECUTED (surfaced, never silently passed). Materiality is contract-read, not hardcoded; no hidden materiality remains.

## Adversarial cases A–J

All ten blocked — see `G5R_EVIDENCE_RECEIPT.json` → `adversarial_cases`.

## Preserved G5 successes (§27)

PnL ≠ validation; priority separate from evidence quality; huge fake alpha still rejected on observable PIT/execution artifacts; UNRESOLVED_PATTERN legal; MechanismCard ≠ strategy; doctrine and reproduction preserved separately; manual canonical until governed amendment; provider-native observations preserved; no provider averaging; DATA_BLOCKED valid; SearchDemand ≠ validation; crypto→FX analogy ≠ target truth; source evidence ≠ target validation; expectation and hidden truth sealed (0 accesses in every run). All prior 684 tests remain green; the 5 upgraded assertions are documented old/why/replacement in their docstrings — most notably the S14 clean-control `PROMOTED` vs `VALIDATION_REQUIRED` inconsistency (G5R-24), now `PROMOTION_CANDIDATE` + `execution_authority=NONE` + `VALIDATION_REQUIRED`.

## New ambiguities (documented, non-blocking)

- **AMB-G5R-01** — the canonical CEREBUS v4 PDF is not in the repository; the S16 source binding is to the repo text extract (digest above). If a canonical PDF later materially conflicts, S16 must be re-blocked (see `G5R_CEREBUS_SOURCE_FIDELITY_AUDIT.md`).
- **AMB-G5R-02** — G5R-21 verifies ref resolution / target domain / fingerprint; claim↔hypothesis linkage is asserted in tests via `claim_ref` but not yet a hard field-level comparison inside `resolve_frozen_target_protocol`.

Carried unchanged: CON-02, CON-03, AMB-03, AMB-08, AMB-11, AMB-12 (provisional), AMB-13, operator-permanence revocation ambiguity.

**RECOMMENDED NEXT ACTION:** `AUTHORIZE_G6`. G6 not begun; S20–S24 not implemented; CEREBUS manual and crypto source branches untouched.
