# SENSOR-B5-I04 — OPERATOR RATIFICATION

> **Verdict: `B5-I04 = OPERATOR_ACCEPTED` (complete frozen I04 checkpoint:
> contract terms + linear/inverse conversion primitives).** Ratified 2026-10-09
> by the operator via the SENSOR-B5-I04R1 directive. This artifact records the
> verification performed on the exact ratification tree (HEAD
> `3da805b1c0b1c93b72df6307d157b5c74a133aa1`). Ratification changed **zero**
> production/test/implementation files; tracked outputs are this file, the
> I05 readiness assessment, and the ledger ratification entry (§166). No
> program-level gate was promoted; I05 implementation authority is NOT granted
> by this ratification.

---

## 1. Custody and ancestry (verified at ratification time)

```text
REPOSITORY  = dabiggestpoppa/larger-lab (origin)
BRANCH      = agent/crypto-sensor-fabric-build (sole authorized write target)
START HEAD  = 3da805b1c0b1c93b72df6307d157b5c74a133aa1 (= required, = remote)
TRACKED TREE= clean (only 3 pre-existing untracked scratch items: .bu_tmp/,
              an I06 spike note, an I03 redteam sidecar — never staged)
PLAN HEAD   = agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f
              (= ledger "Base planning commit"; untouched by this workstream)

Required chain (single parents, 0 merges, all reachable):
  72984adbcc29580bb7942b119f59d3372ebccd8e  I03J I03 ratification / I04 readiness
  4f18a589c12bae41b4dd29860823fd8570507c7b  I04A terms snapshot + PIT projection
  3da805b1c0b1c93b72df6307d157b5c74a133aa1  I04B linear/inverse conversion engine
```

`git log --format="%H %P"` shows exactly these single-parent links; no
rebase/reset/merge/amend/force in the chain. Caveat carried from I03J: Git
proves committed ancestry and reachable evidence, not the absence of any
pre-push local rewrite; the ledger custody records remain the process record.

**Blob identity of frozen authority.** All seven Bloc 5 plan documents are
blob-identical between `agent/crypto-sensor-fabric-plan` and the implementation
branch (measured `git ls-tree` hash-by-hash: `6015790…`, `e35eab5…`,
`f1a0ef1…`, `5382248…`, `3633311…`, `d075bab…`, `d317b39…` — zero diffs).

## 2. Implementation chain inventory (read, not assumed)

**I04A** — `terms/__init__.py`, `terms/snapshot.py` (17-field immutable
`ContractTermsSnapshot`), `terms/projection.py`
(`project_contract_terms(registry, resolution, event_time, knowledge_cutoff)`
half-open valid-time + Option-1 knowledge-time laws, fail-closed typed refusal).
Evidence: schema authority matrix (32 rows), PIT terms matrix (12/12),
adversarial matrix (8/8), scope audit (10/10), implementation evidence.
28 tests (T04A-01..20 + A1..A8).

**I04B** — `terms/conversion.py` (526 lines): `ReferencePriceEvidence`,
`ConversionResult` (structural NULL⇔flag laws), `linear_base_exposure`,
`quote_notional`, `contracts_to_quote_notional`, `inverse_quote_face`,
`inverse_base_from_quote`. Evidence: 7 artifacts (dimensional authority 5,
linear 7, inverse 17, blocked 11, adversarial 10, scope audit 8/8, unit
validation 35 = 58 measured rows, 0 failed), implementation evidence.
54 tests (LIN/INV/OP/ADV/INT/SCHEMA families).

**Noninterference (measured `git diff 4f18a589..HEAD`):**
`identity/` diff = **0 files** (I03 untouched); `terms/snapshot.py` +
`terms/projection.py` **byte-identical** to I04A; `terms/__init__.py` diff is
docstring-only with `__all__` unchanged (`ContractTermsSnapshot`,
`project_contract_terms`); tests changed = only the new I04B suite; no I01
enum touched; no `normalization/time/` (I05), no `normalization/common/`
(I08), no T1 lineage engine (I16) exists — absence verified by `git ls-tree`
of `normalization/` (`__init__`, `enums`, `identity`, `models`, `terms` only).

## 3. Contract coverage — R1..R15 exact set (frozen clauses from
`BLOC_05_I04_READINESS_ASSESSMENT.md` §8.2, cross-read against bloc_05/01–07)

| ID | FROZEN CLAUSE | IMPLEMENTATION + TEST + EVIDENCE | OBSERVED | STATUS |
|---|---|---|---|---|
| R1 | terms source = PIT-valid ContractInstance (03 §6) | projection step 2 valid-time + knowledge-time; `test_t04a_06..12`, `test_int_01`; PIT terms matrix | projection refuses at every boundary; resolves only in-window | COVERED |
| R2 | linear formula parameterized (03 §7) | `linear_base_exposure`/`quote_notional`; `test_lin_01..07`; LIN rows | oracle 19/19, no `1c=1base` assumption (`test_t04a` A1 trap) | COVERED |
| R3 | inverse formula + recorded price block (03 §8) | `inverse_quote_face`/`inverse_base_from_quote`; `test_inv_01..16`; INV rows | face/price dims enforced (INV-13 refuses BTC face) | COVERED |
| R4 | blocked = NULL + flag (03 §8, G5) | `ConversionResult._result_laws` structural validator; blocked matrix 11 rows | NULL⇔`UNIT_CONVERSION_BLOCKED` enforced at model level | COVERED |
| R5 | no silent price-type substitution (03 §8) | `required_price_type` check in `_validated_price`; `test_inv_14`, `test_adv_b`, CXT-06a | PROVIDER_INDEX where TRADE required → BLOCKED (re-observed) | COVERED |
| R6 | unverified terms cannot verify T1 (F3, 01 §9) | projection step 3 `payoff_type=UNKNOWN → None`; `test_t04a_15`, `test_a5` | no snapshot, identity status untouched (T1 emission gate = I18, later) | COVERED (I04 boundary) |
| R7 | no future terms leakage (G1, C2) | `_valid_at`/`_known_at` half-open; `test_t04a_06..12`, `test_int_02`, `test_op_naive_knowledge_cutoff` | boundary pinned ±1µs against real fixture | COVERED |
| R8 | native values preserved (G3, 03 §22 inv.1) | `native_quantity` on every result; INV-15; native-preservation probe | non-finite input → BLOCKED, declared native `None`, input unmoved (re-observed) | COVERED |
| R9 | stablecoin untouched (F7, 03 §22 inv.3) | absence proof: no `common/` conversion module; scope audit `no_i08_common_conversion`; `test_adv_e` | stablecoin substitution BLOCKED; no USD peg path exists | COVERED |
| R10 | lineage + methodology on derived values (G5, 03 §17) | `conversion_inputs`, `source_evidence_refs`, `methodology_version` required by validator | `test_schema_04` proves success without them fails | COVERED |
| R11 | determinism (G8) | `test_lin_07`, `test_inv_16`, `test_adv_j`; producer double-run | generators byte-identical (§6) | COVERED |
| R12 | fail-closed everywhere (G9) | `_validated_price` + `_block` + family isolation; ADV-A..G | every refusal → NULL + flag, no fallback price | COVERED |
| R13 | no identity mutation (01 §15/F28) | identity diff empty; int tests assert inputs unmoved | `git diff 72984adb..HEAD -- identity/` = 0 files | COVERED |
| R14 | N0 schema laws (06 §3) | `test_schema_01..06` (impossible combinations fail validation) | NULL-without-flag, value-with-blocking-flag, unknown fields all refused | COVERED |
| R15 | terms-version succession without overwrite (01 §7) | version read from record only (`test_t04a_05`, `test_a3`); `test_adv_i` | never promoted/synthesized; mismatch → BLOCKED | COVERED |

**UNCOVERED_CONTRACT_SET = ∅. UNAUTHORIZED_EXTRA_SET = ∅** (scope audits
I04A 10/10, I04B 8/8; top-level normalization surface still exactly the 24
ratified B5-I01 symbols; package root exports exactly the 2 ratified I04A
symbols — firewall `test_t04a_16` green).

## 4. Dual-clock and price-context audit (§05) — six counterexamples executed
against the committed implementation this session (read-only probe,
`.bu_tmp/b5_i04r1_cxt_probe.py`, exit 0; reuses committed fixtures)

| CASE | FROZEN EXPECTATION | OBSERVED | ENFORCING LAYER | STATUS |
|---|---|---|---|---|
| CXT-01 terms eligible + price available by cutoff | convert | VALUE `75000 USDT`, instance stamped | projection + `_validated_price` | PASS |
| CXT-02 price observed after event, before later cutoff | PIT-safe vs the **supplied knowledge clock** (bloc_05/02 S4); no frozen clause binds price observation to instrument event time | cutoff=LATE → VALUE; cutoff=event-context → **BLOCKED** (caller's cutoff choice is decisive) | conversion vs caller cutoff; event-time selection = **caller / I05 / later normalizer** | PASS (ownership recorded, §5) |
| CXT-03 `market_available_at` (2023-10-15) > cutoff (2023-10-01) | BLOCK | BLOCKED `UNIT_CONVERSION_BLOCKED` | `_validated_price` availability check | PASS |
| CXT-04 terms knowledge interval expired before conversion cutoff | refuse | projection returns `None`; conversion with `terms=None` → BLOCKED | projection `_known_at` (I04A) | PASS |
| CXT-05 caller supplies foreign-context snapshot | no re-binding; mismatch must be detectable | VALUE with the snapshot's **own** `contract_instance_id` stamped; no laundering | caller precondition + result lineage (identity binding = I03 + projection, upstream) | PASS (upstream precondition recorded, §5) |
| CXT-06 price type substituted / non-finite price | BLOCK | type mismatch → BLOCKED; NaN → refused at model construction (`ValidationError`) | `required_price_type` + `_require_price_domain` | PASS |

**§05.3 ownership decision.** Event/valuation-context selection (which
knowledge cutoff a conversion is asked under, which snapshot belongs to which
row) is **not** an I04-owned obligation: no frozen I04 clause (03 §7/§8, G5,
F5) requires the pure primitives to take or enforce an instrument event time;
03 §8 requires only that the four reference-price fields be *recorded* (done)
and that PIT-safety hold (enforced against the supplied cutoff). The frozen
plan clearly names the later owner: **I05 = "time semantics registry +
interval conventions"** (bloc_05/06 §19, bloc_05/07 §10), with row-level call
context carried by the I10+ sensor normalizers. Upstream precondition recorded
for I05: conversion callers must supply the knowledge cutoff that matches the
intended query/valuation context; I04 primitives remain pure and
caller-clock-bound as designed. **I04 is not incomplete on this axis**, and no
authority gap requires `REQUIRES_OPERATOR_DECISION`. Production guards were
neither strengthened nor relaxed during this audit.

## 5. Economic validity ratification (§06)

- **Linear:** token-equal count unit, multiplier from PIT snapshot only,
  exact Decimal, output = recorded `quantity_unit`/`price_unit`,
  `methodology_version = B5_I04B_CONVERSION_V1`,
  `contract_multiplier_ref=instance#version` lineage, deduplicated
  evidence refs, native preserved. Independent Decimal oracle (no production
  import) recomputed all expectations: **19/19 ORACLE_ALL_MATCH** (0.003,
  75.000, 0.4, 3.303/0.0005, 4.000004).
- **Inverse:** quote-face denomination (face must equal `terms.price_unit`),
  INVERSE classification with consistent `inverse_flag`, nonzero/finite/positive
  price, one of the five frozen types with `required_price_type` enforcement,
  explicit source, UTC observation, availability ≤ cutoff, dimension pair
  equal to `(price_unit, quantity_unit)`, versioned lineage. No universal
  inverse formula; QUANTO refused entirely (refusal path proven).
- **Blocked:** `normalized_value = NULL` + `UNIT_CONVERSION_BLOCKED` at the
  authorized result surface, structurally enforced (NULL without flag, blocked
  result claiming consumed inputs/price, value carrying blocking flag — all
  fail model validation). No zero substitution, no fabricated lineage/source,
  no native mutation, no fallback price.
- **Price-evidence qualification (recorded explicitly):** the engine validates
  the *supplied* reference-price evidence. It is **not** a live market-data
  provenance verifier. Fixture validation is not proof of external provider
  availability; later integration stages must preserve this distinction.
- The 34 first-generation expectation edits: **34
  NUMERICALLY_EQUIVALENT_FORMAT_CHANGE, 0 semantic, 0 incorrect-oracle, 0
  unresolved** (classification table in the I04B implementation evidence §3).

## 6. Evidence integrity and reproducibility (freshly measured this session)

- **Committed hashes match recorded hashes** for all 11 matrices: I04A
  `014f5aac…`, `79de338f…`, `19741acc…`, `07ca4a69…` (= I04A evidence §6);
  I04B `029280ca…`, `b675d95c…`, `7aa3fc21…`, `cde6e4ce…`, `0e6516a7…`,
  `26cba7eb…`, `8945a679…` (= ledger §165 quotes).
- **I04B producer** (`scripts/b5_i04b_conversion.py`): run twice on the clean
  sealed tree this session → exit 0, **7/7 byte-identical** to committed
  bytes; `git status` unchanged after regeneration.
- **I04A producer** (`scripts/b5_i04_terms.py`): run twice at the **I04A
  tree** (`4f18a589`, temporary detached worktree, removed after) → exit 0,
  `ALL PASS: True True True True`, zero tracked diff — the four I04A artifacts
  reproduce byte-identically from tracked source at their checkpoint tree.
  **Disclosure (classified, not a defect):** at the current HEAD the I04A
  producer's *scope audit* legitimately records
  `no_linear_inverse_conversion_engine = FAIL` because its I04A-era non-scope
  predicate ("no conversion implementation") now observes I04B's
  operator-authorized `terms/conversion.py`; the three other I04A artifacts
  still reproduce byte-identically at HEAD. This is checkpoint-time scope
  truth (the same class as I03 limitation L4: sealed historical artifacts are
  not overwritten by later-tree regeneration), not an integrity failure; the
  sealed artifact was left untouched.
- **Governance binding:** tracked `.py` inventory measured from the
  repository root = **1045**; `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`
  reports **1045** — equal; this ratification adds **no** `.py` files, so no
  republish is authorized or performed (directive §10).
- **Protected evidence:** binding audit + protected digest tests re-run this
  session → **9 passed**; `test_i11r2_evidence.py` → **10 passed**; current
  `git status` shows **zero** modified Bloc 4 / I01 / I02 / I03 / I04A / I04B
  evidence artifacts.

## 7. Fresh verification record (§09; cwd = `quant-lab`)

| check | command | exit | result |
|---|---|---|---|
| I04B focused | `pytest tests/.../test_b5_i04b_conversion.py -q` | 0 | 54 passed |
| I04A focused | `pytest tests/.../test_b5_i04_terms.py -q` | 0 | 28 passed |
| I03 focused | `pytest tests/.../test_b5_i03_{resolver,public_api,scope_audit}.py -q` | 0 | 84 passed |
| Normalization | `pytest tests/crypto_sensor_fabric/normalization -q` | 0 | 579 passed |
| Binding + digests | `pytest tests/.../test_i11r2_binding_audit.py tests/.../test_i08_evidence.py -q` | 0 | 9 passed |
| I11R2 evidence | `pytest tests/.../test_i11r2_evidence.py -q` | 0 | 10 passed |
| CXT probe | `python ../.bu_tmp/b5_i04r1_cxt_probe.py` | 0 | 6/6 counterexamples as specified |
| Determinism | both producers ×2 | 0,0 | I04B 7/7 at HEAD; I04A 4/4 at I04A tree (§6) |

**Full suite NOT rerun in this checkpoint** (governance-only, no executable
surface changed — directive §09). The historical
`python -m pytest tests -q` → **3977 passed / 14 skipped / 0 failed**
(1362.28 s, exit 0) was measured on the byte-identical tree: this worktree's
tracked files are unchanged from `3da805b1c` (git status clean before this
ratification's edits), i.e. the same bytes the full suite exercised. Recorded
accurately as a carried measurement, not a fresh one.

## 8. Accepted limitations (carried forward, not converted into closures)

- **L1 — caller-clock PIT:** conversion primitives enforce availability and
  observation against the caller-supplied knowledge cutoff and take no
  event-time parameter; event/valuation-context selection is I05/normalizer
  owned (§4, CXT-02). Frozen contract boundary, not a defect.
- **L2 — price provenance:** engine validates supplied evidence only; not an
  external market-data provenance verifier (§5).
- **L3 — I04A scope-audit regeneration:** checkpoint-time predicate vs
  later trees (§6 disclosure); sealed artifact authoritative for its tree.
- **L4 — inherited static baselines:** repo-wide ruff (5834) / mypy (15)
  predate I04B; 0 findings in I04 files; mypy scoped to `terms/` reports 0.
- **L5 — full-suite carryover:** §7 measurement basis, disclosed as historical.

## 9. Governance promotion (established vocabulary only; before → after)

```text
PASS_SENSOR_B5_I04A_TERMS_FOUNDATION
    PROPOSED (I04A evidence §head)         → OPERATOR_ACCEPTED
B5-I04A                                    (unchanged) OPERATOR_ACCEPTED
B5-I04B
    IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW → OPERATOR_ACCEPTED
B5-I04
    (not yet recorded)                     → OPERATOR_ACCEPTED
B5-I04_COMPLETE
    FALSE                                  → TRUE
BLOC_05_IMPLEMENTATION_STATUS
    I03_OPERATOR_ACCEPTED                  → I04_OPERATOR_ACCEPTED
        (parallel to I02_OPERATOR_ACCEPTED §158, I03_OPERATOR_ACCEPTED §163)
I05_READINESS                              → MEASURED_AND_REPORTED
        (parallel to I04_READINESS §163; see BLOC_05_I05_READINESS_ASSESSMENT.md)
I05_IMPLEMENTATION_AUTHORIZATION           (unchanged) FALSE
B5-I04C+                                   (unchanged) UNAUTHORIZED — no I04C
        exists or is required; R1–R15 coverage is complete, so no I04C work
        package was invented
B5-I03 = OPERATOR_ACCEPTED                 (unchanged)
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
    (all unchanged) NOT_YET_EARNED         — program gates are not earned by
        subgate ratification
next_checkpoint_authorized                 (unchanged) FALSE — I05 requires
        a separate implementation directive; this ratification grants none
BLOC_05 = INCOMPLETE                       (unchanged — I05..I23 remain)
BLOC_06 = UNAUTHORIZED                     (unchanged)
RESEARCH = FROZEN                          (unchanged)
```

No status value was invented to mirror this report: `B5-I04 = OPERATOR_ACCEPTED`
and `B5-I04_COMPLETE = TRUE` are the exact keys the operator's directive §15
specifies for complete coverage; `PASS_SENSOR_B5_I04A_TERMS_FOUNDATION` is the
verdict name already recorded in the committed I04A evidence. No
`PASS_SENSOR_B5_I04_*_SEALED` name was coined because none exists in the
frozen record.

## 10. Acceptance ruling (§07.3 conditions, individually)

```text
ALL_MANDATORY_I04_CONTRACTS = COVERED        (R1..R15, section 3: ∅ uncovered)
UNRESOLVED_I04_BLOCKERS     = ZERO           (dual-clock ownership resolved to
                                              a clearly named later owner, §4)
UNAUTHORIZED_SCOPE          = ZERO           (scope audits 10/10 + 8/8,
                                              identity diff empty, exports fixed)
EVIDENCE_INTEGRITY          = PASS           (hashes match, producers
                                              reproduce, §6)
HISTORICAL_NONINTERFERENCE  = PASS           (protected digests 9 passed,
                                              zero protected-artifact diffs, §6)
```

**→ Complete I04 acceptance is earned.** This ratification covers the I04
technical checkpoint and its evidence chain only. It does not promote any
program-level gate, does not authorize I05 or BLOC_06, and does not change
RESEARCH = FROZEN. `BLOC_05_I05_READINESS_ASSESSMENT.md` is a read-only
reconstruction of the next frozen checkpoint; producing it grants no
implementation authority.

**HARD STOP after push and report.**
