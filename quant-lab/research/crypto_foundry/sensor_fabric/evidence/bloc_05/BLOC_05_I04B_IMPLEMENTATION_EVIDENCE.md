# SENSOR-B5-I04B — IMPLEMENTATION EVIDENCE

> Checkpoint verdict: **I04B_IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW**
> (recorded, never self-ratified). This document measures the I04B linear /
> inverse conversion subsystem on the exact implementation tree; governance
> values are recorded in ledger section 165. The operator's acceptance of
> I04A as an implementation foundation (I04B directive Book 0.1) is recorded
> in that same section. No resolver change, no new enum, no price source, no
> program-gate promotion occurred.

---

## 0. Scope

Authorized in (I04B verification directive): verification of the existing
I04B implementation, repair of demonstrated defects only, evidence audit,
test-scope reconciliation, I11R2 governance binding, custody.

Explicitly NOT owned: new features, I04C, program gates, research changes.
Verified mechanically (scope audit 8/8 PASS).

## 1. Reality lock (§01)

| assertion | measured |
|---|---|
| repository | `dabiggestpoppa/larger-lab` (origin) |
| branch | `agent/crypto-sensor-fabric-build` |
| start HEAD | `4f18a589c12bae41b4dd29860823fd8570507c7b` (= required) |
| tracked worktree at start | only the I04B implementation + test-side Bloc 4 dirt |
| competing pytest processes | **two** concurrent `python -m pytest tests -q` runs were found; the duplicate was terminated (§2) |
| implementation committed | no — uncommitted at directive receipt |

## 2. Full-suite provenance reconciliation (§02)

```text
HISTORICAL_COMMAND      : python -m pytest tests -q   (cwd = quant-lab)
HISTORICAL_WORKING_DIR  : .worktrees/sensor-b4-i11/quant-lab
HISTORICAL_COLLECTION   : tests/ (the supported project suite; no pytest
                          config file exists, so the argument defines scope)
HISTORICAL_PASSED       : 3923 (I04A V7, /tmp/i04a_full.log, FULL_EXIT=0)
HISTORICAL_SKIPPED      : 14
HISTORICAL_LINEAGE      : 3895 (I03I) -> 3923 (I04A, +28) -> now

CURRENT_COMMAND         : python -m pytest tests -q   (same cwd, same args)
CURRENT_COLLECTED       : 3991 (3977 passed + 14 skipped)
CURRENT_PASSED          : 3977
CURRENT_SKIPPED         : 14
CURRENT_FAILED          : 0
CURRENT_ERRORS          : 0
CURRENT_EXIT_CODE       : 0   (1362.28 s; /tmp/i04b_full_clean.log)
ARITHMETIC              : 3923 historical + 54 new I04B tests = 3977 exactly
```

**Discovery-failure classification (§02.2).** The earlier broad-collection
`SystemExit` came from
`research/crypto_foundry/alt_rotation/mech_8/tests/test_alt_mech_8.py`, a
pre-existing executable research script that matches `test_*.py` outside the
supported suite. It is **EXTERNAL_COLLECTION_HAZARD**: the file exists
unmodified at the I04A parent (no I04B diff reaches `research/`), it is not
collected by the historical command, and no I04B import surface is involved.
It was neither modified nor ignored; bare `pytest` (no arguments) was never
the historical invocation. **PROJECT_REGRESSION: none.**
**UNRESOLVED_SCOPE_DISCREPANCY: none** — `tests/` is the canonical supported
suite, evidenced by the exact +54 arithmetic and the I03I/I04A log lineage
both produced by that command.

**Two-run interference defect (repaired).** The first completed full run
 raced a duplicate run launched in the same window and reported 2 failures:
 `test_t04a_16` (stale `terms/__init__` module cache predating the 20:08:19
 firewall repair by the same session) and `test_evidence_directory_untouched`
 (the duplicate process rewriting Bloc 4 JSONs between this test's before/
 after hashing). Both pass in isolation on the final tree (`2 passed`), and
 the uncontested rerun passed 3977/14/0. Neither failure was reproducible
 outside the interference.

## 3. Numeric oracle audit (§03.1–§03.2)

An independent oracle (`.bu_tmp` scratch, not committed, imports **no**
production conversion code) recomputes every arithmetic expectation from the
frozen formulas in exact Decimal:

```text
base_lin   = 3 x 0.001            = 0.003      (bloc_05/03 S7)
notional   = 0.003 x 25000        = 75.000     (S7 x S8)
inv_base   = 10000 / 25000        = 0.4        (Book 2.3)
frac       = 1.101 x 3 / 0.5 x 0.001 = 3.303 / 0.0005
inv03      = 10000.01 / 2500      = 4.000004
```

Result: **ORACLE_ALL_MATCH — 19/19 checks**: every hand-written
`expected_result` and every measured `observed_result` in the linear,
inverse and dimensional-authority matrices contains the independently
derived value.

**Classification of the 34 first-generation expectation edits** (the exact
pre-edit `FAILURES=34` dump was recovered from the session transcript;
each pair is listed with its original and final text):

| class | count | cases |
|---|---|---|
| `NUMERICALLY_EQUIVALENT_FORMAT_CHANGE` | 4 | LIN-03 (`75`→`75.000`), LIN-04 (`0`→`0.000`), LIN-06 (`75`→`75.000`), INV-03-family serializer scale (Decimal str keeps trailing zeros; oracle confirms 75.000 == 75, 0.000 == 0) |
| `NUMERICALLY_EQUIVALENT_FORMAT_CHANGE` (observable-detail expansion, same semantics) | 3 | LIN-05, INV-04, ADV-D (expected prose → the exact observed serialization of the same value/flag/quote-settlement facts) |
| `NUMERICALLY_EQUIVALENT_FORMAT_CHANGE` (blocked-row serialization: `\|native=X` suffix added to observed format, expectation now carries it) | 24 | INV-05..14, LIN-R01..R09, OP-N1, OP-N2, ADV-B, ADV-C, ADV-E — NULL + `UNIT_CONVERSION_BLOCKED` unchanged in both members |
| `NUMERICALLY_EQUIVALENT_FORMAT_CHANGE` (probe rephrasing, same boolean fact) | 3 | ADV-A, ADV-F, ADV-G (expected now states the exact observed enumeration of the same all-blocked / all-True facts) |
| `SEMANTIC_EXPECTATION_CHANGE` | 0 | — |
| `INCORRECT_ORACLE` | 0 | — |
| `UNRESOLVED` | 0 | — |

No edit changed a unit, price input, payoff type, flag set, lineage,
methodology, or numeric economic value: the frozen formulas, the flag
vocabulary (`UNIT_CONVERSION_BLOCKED` only) and the methodology token are
identical before and after. Native preservation for the 24 blocked rows was
**additionally re-proven by an independent probe** (blocked results carry
`native_quantity` = the caller's input; non-finite input → declared absent,
never a number): `NATIVE_PRESERVATION_ON_BLOCK: PASS`.

## 4. Matrix execution provenance (§03.3)

Every artifact is produced by the tracked generator
`research/crypto_foundry/sensor_fabric/scripts/b5_i04b_conversion.py`,
which **imports the production implementation and executes each operation
here**; `expected_result` is the hand-written member, `observed_result` is
measured from the returned `ConversionResult`, and `disposition` is their
string equality (non-PASS makes the producer exit non-zero, so no failing
fixture can be emitted as a passing artifact):

| artifact | rows | failed | tracked generator | SHA256 |
|---|---|---|---|---|
| BLOC_05_I04B_DIMENSIONAL_AUTHORITY_MATRIX.json | 5 | 0 | b5_i04b_conversion.py | `029280ca1a51d13f6fbc646047f9385e5d73971fa7c334b0d071a5e087bb640c` |
| BLOC_05_I04B_LINEAR_MATRIX.json | 7 | 0 | b5_i04b_conversion.py | `b675d95c7785d7cbdfd2a9d3b59388bc7a340ed1913a4f3b1b9af72c71bb6f29` |
| BLOC_05_I04B_INVERSE_MATRIX.json | 17 | 0 | b5_i04b_conversion.py | `7aa3fc21da6b7519b29193f775a1fa5fb211b51a9a7c3fcada00725b90c015f1` |
| BLOC_05_I04B_BLOCKED_CONVERSION_MATRIX.json | 11 | 0 | b5_i04b_conversion.py | `cde6e4ceffa8a5c22ae71b98d1e1a8c8a3a179d286aea33488df12ae0cec62a6` |
| BLOC_05_I04B_ADVERSARIAL_MATRIX.json | 10 | 0 | b5_i04b_conversion.py | `0e6516a7e81c2163f2d3c245cb87f21d86daaad7d6eb737418568afd2c580a71` |
| BLOC_05_I04B_SCOPE_AUDIT.json | 8 | 0 | b5_i04b_conversion.py | `26cba7ebb4e942c9ce4c95773d81892b80a9d53ed123212dcc0ebd504276a095` |
| bloc_05_unit_validation.json | 35 | 0 | b5_i04b_conversion.py | `8945a679bb0875583ec0e442baa4e45edd6460ede000ae9fa6f6b2107a9572cb` |

Total: **58 measured rows, 0 failed** (envelope rows + scope checks as
summarized inside each artifact).

## 5. Determinism (§03.4)

Four consecutive generator executions (two before this directive's audit,
two after the scope-audit ledger-name repair) produced **byte-identical
output**: identical per-artifact SHA256 across all runs, identical run
logs. No `.bu_tmp` import (the producer bootstraps `sys.path` from `src/`
only), pinned `CREATED = "2026-10-08"` literal (no wall clock), no network,
no memory-address `repr()`, `sort_keys` + LF bytes written directly.
The ledger-filename predicate repair (section 7) changed no artifact hash.

## 6. Frozen contract audit (§04)

**Linear authority.** Every successful linear result has: token-equal
count denomination (`contracts_unit == multiplier_unit`), multiplier read
only from the PIT-eligible snapshot (never inferred from its number, never
assumed 1-contract-1-base), exact Decimal arithmetic (oracle §3), output
unit = recorded `quantity_unit`/`price_unit`, explicit
`methodology_version = B5_I04B_CONVERSION_V1`, lineage =
`contract_multiplier_ref=instance#version` (+ price ref when consumed),
`source_evidence_refs` passed through deduplicated, native quantity
preserved on the result.

**Inverse authority.** Each successful inverse result has: verified
quote-face denomination (face unit must equal `terms.price_unit` — INV-13
proves the BTC-denominated face is refused), INVERSE classification with
structurally consistent `inverse_flag` (INV-12), nonzero/finite/economically
positive price (INV-06/07), one of the five frozen types with
`required_price_type` enforcement (INV-14), explicit source (INV-08),
UTC-aware observation (INV-09), PIT availability (INV-10), dimension pair
equal to `(price_unit, quantity_unit)` (INV-11), versioned lineage.

**Reference-price availability (§04.3).** The accepted availability field
is `market_available_at` (bloc_05/02 S4 knowledge clock), a **required**
field of `ReferencePriceEvidence`; the engine refuses unavailability rather
than equating observation with availability. Six counterexamples, executed
against the real implementation (read-only probes):

| probe | configuration | observed | required |
|---|---|---|---|
| PRICE-PIT-01 | available after cutoff | BLOCKED | BLOCKED |
| PRICE-PIT-02 | available before cutoff (control) | VALUE (0.4) | VALUE |
| PRICE-PIT-03 | observation after cutoff | BLOCKED | BLOCKED |
| PRICE-PIT-04 | type substitution (PROVIDER_INDEX where TRADE_PRICE required) | BLOCKED | BLOCKED |
| PRICE-PIT-05 | `market_available_at` absent | BLOCKED (model refuses construction) | BLOCKED |
| PRICE-PIT-06 | blank source | BLOCKED (model refuses construction) | BLOCKED |

Event-time nuance disclosed: the conversion primitives enforce observation
and availability against the **caller-supplied `knowledge_cutoff`**; they do
not take an event-time parameter. A price observed after the event but
before a later cutoff converts **only when that later cutoff is what the
caller asks** (probe: `cutoff=LATE` → VALUE; `cutoff=EVENT` → BLOCKED).
Point-in-time queries are therefore only as sound as the cutoff the caller
supplies — this is the frozen contract's clock boundary (bloc_05/02 S4), not
an implementation shortcut; no silent fallback price and no
observation≡availability conflation exists anywhere in the module.

**Blocked contract.** `normalized_value = None` + `UNIT_CONVERSION_BLOCKED`
is enforced *structurally* (the `ConversionResult` validator rejects a NULL
without the flag, a NULL claiming consumed inputs or a consumed price, and a
value carrying any blocking flag). No zero substitution, no fabricated
lineage (ADV-H), no invented source (INV-08), no mutation (INV-15), no
fallback price (INV-14, §3.4 of the directive).

## 7. Public API noninterference (§05)

| boundary | measured |
|---|---|
| `terms/snapshot.py` vs HEAD | **byte-identical** |
| `terms/projection.py` vs HEAD | **byte-identical** |
| `terms/__init__.py` export section vs HEAD | **identical** (docstring-only diff; `__all__` still exactly `ContractTermsSnapshot`, `project_contract_terms`) |
| I04A tests vs HEAD | **zero modifications** (`git diff --name-only -- tests/` empty for tracked files) |
| I03 `identity/` vs HEAD | **empty diff** (0 lines) |
| new I01 enums | none (no tracked enum file modified) |
| I05/I08/I16 leakage | none (scope audit: `i08_common_conversion_absent`, `conversion_owned_under_terms`, top-level surface = 24 symbols) |
| firewall test `test_t04a_16` | passes (conversion reachable only as `terms.conversion` submodule; no conversion name at package root) |

**Defect found and repaired in-session:** the first I04B wiring exposed
conversion names through `terms/__init__.py`, which the I04A firewall
correctly rejected. The repair moved access to
`crypto_sensor_fabric.normalization.terms.conversion`; the package-root diff
is now docstring-only. The I11R2 binding audit additionally flagged the
generator for *naming the governance ledger* (a predicate non-reader
modules must not mention): the ledger path was removed from the producer's
scope-check allowlist and an ordering law documented in its docstring
(generation precedes the ledger append; hashes are quoted into it).
**No allowlist entry was added** — that would be a governance decision.

## 8. Regression battery (§07) — all freshly measured

| suite | command (cwd = quant-lab) | exit | result |
|---|---|---|---|
| I04B focused | `python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i04b_conversion.py -q` | 0 | **54 passed** |
| I04A focused | `python -m pytest tests/crypto_sensor_fabric/normalization/test_b5_i04_terms.py -q` | 0 | **28 passed** |
| I03 focused | `python -m pytest tests/.../test_b5_i03_{resolver,public_api,scope_audit}.py -q` | 0 | **84 passed** (exact historical match) |
| Normalization | `python -m pytest tests/crypto_sensor_fabric/normalization -q` | 0 | **579 passed** (525 I04A baseline + 54) |
| Full project | `python -m pytest tests -q` | 0 | **3977 passed, 14 skipped, 0 failed** (1362.28 s) |
| I11R2 binding + protected digests | `python -m pytest tests/.../test_i11r2_binding_audit.py tests/.../test_i08_evidence.py -q` | 0 | **9 passed** (after Bloc 4 restoration) |
| Secret scan | `python -m pytest tests/.../test_i15_hardening.py -k repository_secret_scan -q` | 0 | **1 passed** |
| Evidence generators ×2 | `python research/.../scripts/b5_i04b_conversion.py` (twice) | 0, 0 | **7/7 byte-identical** |
| Ruff (changed scope) | `python -m ruff check` on the four I04B files | 0 | **All checks passed** |
| Ruff (repo-wide) | `python -m ruff check .` | 0 reported as findings-dump | 5834 pre-existing findings, **none** in I04B files (inherited baseline; I04A-era runs used the changed-scope convention) |
| Mypy (I04B scope) | `python -m mypy src/crypto_sensor_fabric/normalization/terms/` | 1 | **0 errors in `terms/`**; the 10 reported are the inherited provider/probe baseline (verified identical to the I04A-era log) |
| Mypy (repo) | `python -m mypy src` | 1 | 15 errors, all in untouched provider/probe/planner files (inherited; 0 in I04B files) |
| Compileall | `python -m compileall -q src tests research/.../scripts` | 0 | **OK** |

Limitations: historical full-suite runs used the same command but are not
re-runnable at the parent commit inside this worktree without disturbing
the tree; lineage is instead established by exact arithmetic (+54 = the new
file's test count) and preserved prior logs.

## 9. Historical noninterference (§08)

The full suite regenerated 11 Bloc 4 evidence JSONs (CRLF line endings via
`Path.write_text` text mode + current-tree `files_scanned`/timing/memory
re-measurements — Windows test-environment artifacts, the documented L4
behavior). Classified by `git diff --ignore-cr-at-eol`: 7 files EOL-only, 4
files additionally carry re-measured machine counters (observed moves
include `files_scanned` 122→136 and 279→311, plus timing/memory fields and
one `refusal` discriminator observed under concurrent load). **No historical
semantics changed**; all 11 restored to HEAD bytes (`git checkout -- evidence/bloc_04/`),
protected digest + binding tests re-run green (9 passed). The I11R2 audit
count republish (section 10) is handled separately as the authorized
mechanical exception — it is *not* part of this restoration.

## 10. I11R2 governance binding (§06)

- Measured tracked-Python inventory at staging: `git ls-files '*.py'` (from
  the repository root, the same call the audit makes) = **1042 before**
  staging; I04B adds exactly **3** tracked `.py` files
  (`terms/conversion.py`, `test_b5_i04b_conversion.py`,
  `scripts/b5_i04b_conversion.py`) → **1045 after staging**.
- Republish via the established `UPDATE_I11R2_EVIDENCE=1` path, staged with
  the same commit that creates the count (the I03J/I04A lesson). Only
  `python_files_scanned` moves; all substantive audit rows, the allowlist,
  the predicates and the frozen I07R1I pin are re-verified unchanged, and
  the binding + digest tests pass after republish.
- Before/after values: **1042 → 1045** (recorded in ledger section 165).

## 11. RED-first capture

`tests/.../test_b5_i04b_conversion.py` was authored before any conversion
module existed; the pre-implementation run failed at collection with
`ImportError: cannot import name 'ConversionResult' from
'crypto_sensor_fabric.normalization.terms'` (pytest exit 2, recorded in the
session log). No existing code was touched to produce the RED. Post-
implementation: 54/54.

## 12. Acceptance gates (§09)

See the final report's gate matrix G01–G22; each PASS there cites the
section of this document (or the measured command table in section 8) that
produced it.

## 13. R1–R15 exact-set coverage (I04 disposition after I04B)

| id | obligation | state | where |
|---|---|---|---|
| R1 | terms source = PIT-valid ContractInstance | COVERED | I04A schema matrix (prior) |
| R2 | linear formula parameterized (03 §7) | COVERED | LIN-01..07; authority rows L1–L3 |
| R3 | inverse formula + price block (03 §8) | COVERED | INV-01..04, INV-15/16; authority I1–I2 |
| R4 | blocked = NULL + flag | COVERED | blocked matrix 11 rows + INV-05..14; structural validator |
| R5 | no silent price-type substitution | COVERED | INV-14, ADV-B, PRICE-PIT-04 |
| R6 | unverified terms cannot verify | COVERED | I04A status-map tests (prior) |
| R7 | no future leakage | COVERED | INV-10, PRICE-PIT-01/03 (availability vs cutoff) |
| R8 | native values preserved | COVERED | INV-15, scope audit, native-preservation probe |
| R9 | stablecoin untouched | COVERED | absence proof: no common-conversion directory (scope audit) |
| R10 | lineage + methodology on derived values | COVERED | conversion_inputs/source_evidence_refs/methodology on every success row; validator-enforced |
| R11 | determinism | COVERED | LIN-07, INV-16, ADV-J + 4× byte-identical generation |
| R12 | fail-closed everywhere | COVERED | blocked matrix, ADV-A..G, probes |
| R13 | no identity mutation | COVERED | identity diff empty (§7) |
| R14 | N0 schema laws | COVERED | model validators (NULL⇔flag, impossible combinations rejected) |
| R15 | terms-version succession | COVERED | ADV-I (version never promoted) + I04A succession tests |

No row is PARTIAL, BLOCKED, NOT_STARTED or OUT_OF_SCOPE for I04B scope;
full I04 checkpoint completion still requires operator acceptance of this
stage (I04B alone does not ratify I04).

## 14. Limitations

- PIT soundness depends on the caller-supplied knowledge cutoff (§6) — the
  frozen contract's own boundary; no implementation-side event-time
  parameter exists by design.
- QUANTO conversion is refused entirely (no formula is authorized); only
  the refusal path is proven.
- Repo-wide ruff/mypy carry large inherited baselines outside I04B scope;
  only the changed-scope results are I04B claims.
- The `market_available_at` precondition on caller-supplied prices is
  verified mechanically against the model, not against an external market
  data availability record (none exists at this checkpoint).

*Governance: `B5-I04B = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`;
`B5-I04_COMPLETE = FALSE`; all program gates `NOT_YET_EARNED`;
`next_checkpoint_authorized = FALSE`; B5-I04C+ = UNAUTHORIZED; BLOC_06 =
UNAUTHORIZED; RESEARCH = FROZEN. HARD STOP after push and report.*
