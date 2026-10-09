# SENSOR-B5-I05 — READINESS ASSESSMENT (READ-ONLY)

> Reconstructed 2026-10-09 by the operator via the SENSOR-B5-I04R1 directive
> (Operation D), after complete I04 acceptance. **READ-ONLY:** no I05 code,
> no I05 tests, no placeholders in `src/`, no implementation authority
> granted. Frozen plan documents were read from the implementation branch and
> verified blob-identical to `agent/crypto-sensor-fabric-plan` @ `4bb677f9e…`.
> Verdict: **I05_READINESS = MEASURED_AND_REPORTED**;
> **I05_IMPLEMENTATION_AUTHORIZATION = FALSE** (a separate directive is
> required to start I05).

---

## 1. Frozen checkpoint identity

```text
CHECKPOINT_ID    : SENSOR-B5-I05
FROZEN_TITLE     : "time semantics registry + interval conventions"
                   (bloc_05/06 §19 staged commits; bloc_05/07 §10 — same words)
PURPOSE          : make every provider timestamp's meaning explicit and every
                   availability claim defensible, so that PIT queries, replay
                   and revision handling rest on declared semantics instead of
                   guessed ones (bloc_05/02 §1: "Why timestamp truth matters")
```

## 2. Governing clauses (frozen authority)

| clause | obligation for I05 |
|---|---|
| bloc_05/02 §2 | canonical timestamp vocabulary (`source_event_at`, `interval_start_at`, `interval_end_at`, `effective_at`, `published_at`, `market_available_at`, `ingested_at`, …) |
| bloc_05/02 §4 | two availability clocks preserved separately: `market_available_at` vs `ingested_at`; never silently substituted |
| bloc_05/02 §5 | `availability_basis` + `availability_confidence` on replay-relevant rows; `UNKNOWN` / unsupported `SYSTEM_ONLY_OBSERVED` blocked from strict replay |
| bloc_05/02 §6 | conservative availability derivation rules (no optimistic availability) |
| bloc_05/02 §7 | interval boundary convention declared per observation (`LEFT_CLOSED_RIGHT_OPEN` … `POINT_SAMPLE`); never guessed |
| bloc_05/02 §8–9 | UTC/timezone-aware canonical times; explicit precision; clock-skew handling |
| bloc_05/02 §10–12 | historical revisions, research revision modes (`AS_KNOWN_THEN` vs `LATEST_VERIFIED`), provider-correction leakage prevention |
| bloc_05/02 §13 | sensor-specific time semantics per family (trades anchor `source_event_at`; interval statistics need `market_available_at >= interval_end_at`; funding preserves `published_at`/`effective_at`; …) |
| bloc_05/02 §15 | replay eligibility rules + planned `replay_eligibility` field |
| bloc_05/02 §17 | **required modules** (§4 below) + `provider_time_semantics.yaml`, `revision_policies.yaml` |
| bloc_05/02 §18 | invariants 1–8 (no naive timestamps; no early interval availability; `ingested_at` never substitutes; no future-correction leakage into `AS_KNOWN_THEN`; precision preserved; archive reconstruction labeled; unknown semantics fail closed; time normalization never mutates T0 evidence) |
| bloc_05/06 §1 G2 | Timestamp truth gate (UTC; explicit interval semantics; no pre-close availability without evidence; availability≠ingestion; strict replay blocks unknown availability) |
| bloc_05/06 §13 | required timestamp/replay test scenarios (6 listed) |
| bloc_05/06 §17 | evidence artifact **`bloc_05_time_validation.json`** |
| bloc_05/07 F8 | timestamp truth is multi-dimensional; T0 preservation fields kept |
| bloc_05/01 §7 | (feeds I05) symbol reuse / terms-version succession events that create cutover timestamps |

## 3. Upstream dependencies and readiness

| dependency | state at I04 ratification |
|---|---|
| B5-I01 enums/base models/T1 envelope | OPERATOR_ACCEPTED |
| B5-I02 identity models + registries | OPERATOR_ACCEPTED |
| B5-I03 lifecycle/alias/PIT resolver | OPERATOR_ACCEPTED |
| B5-I04 terms snapshot + conversion primitives | OPERATOR_ACCEPTED (this ratification) |
| Frozen availability field | `market_available_at` already consumed as a **required** field of `ReferencePriceEvidence` (I04B); I05 owns its derivation/registry side |
| Ledger §163 two open items (D1 schema, D2 TERMS_UNVERIFIED) | both answered and implemented in I04A (D1/D2 recorded in ledger §164) |

No unresolved upstream blocker was identified for I05.

## 4. Required modules (frozen list) → current inventory

```text
normalization/time/
  models.py               ABSENT
  enums.py                ABSENT
  semantics_registry.py   ABSENT
  availability.py         ABSENT
  intervals.py            ABSENT
  revision_policy.py      ABSENT
  replay_gate.py          ABSENT
config:
  provider_time_semantics.yaml    ABSENT
  revision_policies.yaml          ABSENT
```

Verified by `git ls-tree HEAD quant-lab/src/crypto_sensor_fabric/normalization/`
— contains only `__init__.py`, `enums.py`, `models.py`, `identity/`, `terms/`.
**Unimplemented surface: 7/7 modules + 2/2 configs — I05 not started**, as
required (no I05 leakage from I04; scope audits confirm).

## 5. Input/output schema contract (reconstructed, not implemented)

- **Inputs:** provider observations carrying raw timestamp fields + declared
  provider semantics config; T0 evidence (never mutated — invariant 8);
  existing `IdentityRegistrySnapshot`/`ContractTermsSnapshot` PIT windows as
  consumers of interval decisions.
- **Outputs:** canonical UTC times with declared semantics;
  `availability_basis`/`availability_confidence`; interval boundary
  declarations; revision-mode labels (`AS_KNOWN_THEN` vs `LATEST_VERIFIED`);
  `replay_eligibility`; quality flags from bloc_05/02 §16.
- **Consumer contract already frozen in I04:** conversion primitives consume
  (cutoff, `market_available_at`, `reference_price_time`) — I05 must keep
  supplying clocks at least as strict; upstream precondition recorded in the
  I04 ratification §4 (L1).

## 6. Test layers and evidence artifacts required

```text
TEST LAYERS (bloc_05/06 §13 + §3 N0 for time models):
  - 5m interval timestamped at start cannot be available at start
  - archive row proven contemporaneously public → HISTORICAL_ARCHIVE_RECONSTRUCTION
  - late correction does not enter AS_KNOWN_THEN replay
  - latest retrospective mode may select it explicitly
  - unknown market availability blocks strict replay
  - system ingestion vs market availability never collapse
  - N0 laws: tz enforcement, unknown enum fails, versions required where derived

EVIDENCE (bloc_05/06 §17):
  bloc_05_time_validation.json     (plus shared acceptance summary later)
```

## 7. Acceptance predicates and forbidden behavior

- **Acceptance:** G2 all bullets green; invariants 1–8 hold; the six §13
  scenarios reproduce; evidence artifact deterministic from tracked source;
  no regression in I01–I04 suites (esp. the 84 I03 + 82 I04 focused tests).
- **Forbidden:** inventing availability timestamps; substituting `ingested_at`
  for `market_available_at`; guessing interval conventions; leaking future
  corrections into `AS_KNOWN_THEN`; mutating T0 evidence; promoting any
  program gate as a side effect.
- **Stop conditions:** any invariant that can only be satisfied by rewriting
  T0 evidence or an I01–I04 artifact → STOP and request operator decision.

## 8. Contract-to-interface inventory summary

```text
FROZEN_OBLIGATIONS (I05):  bloc_05/02 §2–§18 + §13/§15/§17 + G2 + F8
IMPLEMENTED_SURFACE       : 0 / 7 modules, 0 / 2 configs
DEPENDENCY_READINESS      : I01–I04 all OPERATOR_ACCEPTED; no open upstream item
EVIDENCE_STATUS           : bloc_05_time_validation.json ABSENT (correct —
                            nothing fabricated before implementation)
AUTHORIZATION             : FALSE — separate directive required
```
