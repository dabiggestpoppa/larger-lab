# SENSOR-B5-I03  -  LIFECYCLE/ALIAS/PIT IDENTITY RESOLVER IMPLEMENTATION EVIDENCE

Checkpoint verdict: `PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED` (proposed, PENDING_OPERATOR_REVIEW).
`I03_IDENTITY_RESOLVER_SUBGATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`; `IDENTITY_GATE = NOT_YET_EARNED` (program-level gate; later PIT/property/integration/golden stages still exist  -  no self-ratification).
All values below are measured on the literal final implementation tree (local HEAD `61148c02e73ce3e9ca5b2d5f09ddfc90ff288637`, reached via I03A `e06c26452` -> I03B `06dcc7eb9` -> I03C `5e9424835` -> I03D-impl `61148c02e`) by the mechanical generators in `.bu_tmp/` (`b5_i03_mats.py`, `b5_i03_redteam.py`, `b5_i03_scope.py`, `b5_i03_adv_wrap.py`) and by the pytest/static runs recorded in ledger §159.

## 0. Scope

Implemented exactly: the frozen lifecycle/alias/resolution vocabulary (`identity/enums.py`), versioned evidence-backed alias records (`identity/aliases.py`), minimal per-transition lifecycle evidence records (`identity/lifecycle.py`), the registry/snapshot extension consuming I02 identity truth (duplicate refusal, referential integrity, overlap refusal, succession law, YAML roundtrip  -  all re-measured green), and the pure point-in-time identity resolver (`identity/resolver.py`). Nothing else: no terms math, no universe/time/sensors/conversion machinery, no network, no filesystem, no wall clock (scope audit measured: all forbidden imports/behaviors absent; `identity __all__ = 17`, top-level normalization surface unchanged at 24).

## 1. Production surface (measured)

`normalization/identity/`: 7 files, 1547 source lines. I03-new: `enums.py` 97, `aliases.py` 75, `lifecycle.py` 69, `resolver.py` 615; I02 files extended in place: `models.py` (alias/lifecycle/resolution record models), `registry.py` (snapshot registration + validation of the new record kinds), `__init__.py` (surface only). Public identity symbols: **17** (AliasType, CanonicalAsset, ContractInstance, EconomicContract, IdentityRegistrySnapshot, IdentityResolution, IdentityResolutionStatus, InstrumentAlias, InstrumentLifecycle, LifecycleState, SemanticToken, Venue, VenueInstrument, parse_identity_registry_yaml, resolve_instrument, serialize_identity_registry_yaml, validate_registry_succession). Top-level normalization `__all__`: **24** (unchanged ratified I01 surface).

Resolver entry point: `resolve_instrument(snapshot, provider, venue, native_symbol, event_time, knowledge_cutoff, optional_provider_instrument_id=None) -> IdentityResolution`  -  the registry **snapshot leads** (documented deviation from the plan's argument order: resolution is a pure function over one explicit immutable snapshot; no ambient state, no global registry lookup).

## 2. Frozen vocabulary (measured, nothing invented)

* `LifecycleState` (7, exact order): PRE_LISTING, ACTIVE, SUSPENDED, DELISTING_ANNOUNCED, DELISTED, RELISTED_NEW_INSTANCE, UNKNOWN. Section 6's refusal to collapse pre-listing/post-delisting/unknown absence into one state is enforced in the resolver's verdict law, not by an enum trick. UNKNOWN is unverified lifecycle evidence and must NOT become ACTIVE by default (directive 34).
* `AliasType` (6, exact order): API_SYMBOL, ARCHIVE_SYMBOL, WEBSOCKET_SYMBOL, DISPLAY_SYMBOL, LEGACY_SYMBOL, PROVIDER_INTERNAL_ID. MANUAL/FUZZY/CANONICAL are deliberately absent (no frozen source defines them; section 10 fuzzy law).
* `IdentityResolutionStatus` (9, exact order): RESOLVED_EXACT, RESOLVED_ALIAS, RESOLVED_WITH_WARNING, AMBIGUOUS, NOT_YET_LISTED, DELISTED, UNKNOWN_SYMBOL, TERMS_UNVERIFIED, PIT_KNOWLEDGE_BLOCKED  -  plus `BLOCKING_IDENTITY_RESOLUTION_STATUSES = {AMBIGUOUS, UNKNOWN_SYMBOL, TERMS_UNVERIFIED, PIT_KNOWLEDGE_BLOCKED}` as the section-9 blockers that never yield canonical economic identity.
* Quality flags emitted by I03 paths: `IDENTITY_ALIAS_USED` (ordinary documented alias wins the pooled scan), `IDENTITY_MANUAL_OVERRIDE` (curated non-API carrier wins the pooled scan), `IDENTITY_LIFECYCLE_BOUNDARY` (knowledge-valid SUSPENDED/DELISTING_ANNOUNCED window over the event), `IDENTITY_PROVIDER_ID_MISSING` (tier-1 marker when no provider instrument ID was supplied). Sanctioned flags NOT emitted by any I03 path and NOT invented: IDENTITY_SYMBOL_REUSED, IDENTITY_RELISTED, IDENTITY_CURRENT_METADATA_BACKCAST_RISK (reuse/relisting/backcast behavior is carried by RELISTED_NEW_INSTANCE + the cutover verdict law without a dedicated flag in I03), IDENTITY_AMBIGUOUS (ambiguity is carried by the AMBIGUOUS status), IDENTITY_TERMS_UNVERIFIED (terms verification is B5-I04+), IDENTITY_STABLECOIN_DISTINCT (USD/USDT/USDC distinction is structural in I02 records: no mapping logic exists at all).

## 3. Resolver laws (measured)

* **Frozen five-tier matching order** (bloc_05/01 section 10): (1) provider instrument ID valid at event time, (2) exact native symbol + venue + lifecycle interval, (3) documented alias valid at event time, (4) curated evidence-backed manual mapping, (5) no result. **Tiers 3 and 4 are ONE pooled alias scan by design** (ambiguity dominates convenience, section 9): splitting curated carriers into a later sequential tier would let a convenience match silently outrank an ambiguity the pooled scan can see. Tier-4 semantics live in the winner's discrimination: `alias_type in _DOCUMENTED_SYMBOL_ALIAS_TYPES = {API_SYMBOL, WEBSOCKET_SYMBOL}` -> `IDENTITY_ALIAS_USED`; any other (curated ARCHIVE/DISPLAY/LEGACY/PROVIDER_INTERNAL_ID) carrier -> `IDENTITY_MANUAL_OVERRIDE`. Tier 4 is therefore structurally distinct from tier 3  -  never a dead duplicate.
* **Dual-clock PIT law on every candidate at every tier**: `valid_from <= event_time < valid_to` AND `known_from <= knowledge_cutoff` (and known_to where applicable). No result uses identity knowledge not yet known at the cutoff. Naive datetimes refused outright.
* **Ambiguity law**: several equally PIT-valid candidates inside one tier -> AMBIGUOUS; never first/latest/sorted/lexicographic. A curated carrier can never outrank an ambiguity the pooled scan sees (A1a/A2b).
* **Lifecycle-verdict law**: a queried symbol with instances known by the cutoff but no instance valid at event_time is NOT_YET_LISTED strictly before the earliest valid_from and DELISTED at/after the latest valid_to (instance cutover is the relisting law, not a silent latest-win  -  symbol-reuse/relisting separation A1c/A1d).
* **Lifecycle downgrade law**: a knowledge-valid SUSPENDED/DELISTING_ANNOUNCED window covering event_time downgrades the resolution to RESOLVED_WITH_WARNING + IDENTITY_LIFECYCLE_BOUNDARY. A downgraded **alias** match keeps its provenance (alias evidence refs, confidence, IDENTITY_ALIAS_USED) but carries **NO `matched_alias_id`**  -  that field is only ever set for RESOLVED_ALIAS (I03 validator law). Lifecycle rows of other states (DELISTED, UNKNOWN, ...) are inert evidence: they neither block nor warn; no behavior was invented for UNKNOWN windows (the frozen plan under-specifies them; recorded, not patched).
* **Fail-closed tier-5 sweep**: any late (post-cutoff) alias or instance evidence reachable for the query forces PIT_KNOWLEDGE_BLOCKED rather than UNKNOWN_SYMBOL; unresolved answers carry no fabricated identifiers (all id fields None, source refs empty unless a real identity was selected).
* **Provider-ID priority bounded by PIT** (directive 13): the ID anchors the instrument against contradicting text (A4a), a nonexistent ID is not a lifeline (A4b), and an ID whose instance is unknown at the cutoff yields PIT_KNOWLEDGE_BLOCKED  -  never a backward leak (A4c).
* **Exact-only law**: no fuzzy, no prefix, no substring, no case folding, no separator normalization, no BTC/XBT inference without a registered alias, no display/archive-symbol guessing (alias matrix), and no USD/USDT/USDC substitution (stablecoin firewall; no I08 conversion behavior exists in I03).
* **No I04 leakage** (mechanically audited, scope audit): no multiplier, inverse, quantity, notional, or unit conversion anywhere in the identity package; `canonical_asset_id` is supplied by the registry (the selected instance's economic contract underlying), never computed; `terms_version` mirrors `ContractInstance.contract_terms_version` verbatim.

## 4. A12 defect history (preserved, not hidden)

**PRE-REPAIR (real defect, found by the I03 red-team, case A12):** an alias-derived match landing inside a knowledge-valid SUSPENDED lifecycle window produced a result shape that violated the I03C resolver validator  -  the downgraded result still carried `matched_alias_id`, but that field is only lawful on RESOLVED_ALIAS  -  so `resolve_instrument` **crashed** on a legal input. The stale pre-fix red-team artifact (23/25, A3+A12 FAIL) was generated before `61148c02e` and has been discarded from the working area; the defect history is recorded here and in ledger §159 instead of being rewritten out of the I03 commits.

**POST-REPAIR (`61148c02e`, no amend/squash of earlier I03 history):** the lifecycle downgrade of an alias-derived match drops `matched_alias_id`, preserves provenance (source evidence refs, confidence, `IDENTITY_ALIAS_USED`), does not misrepresent alias resolution as active canonical identity, and no validator crash occurs. Two regression pins were added to the I03 suite: `test_alias_match_inside_suspended_window_downgrades_without_alias_id` and `test_alias_match_outside_warning_windows_keeps_matched_alias_id`. The validator law itself was not changed.

## 5. Tier-4 relabel and disclosed wording deviation

The vocabulary authority matrix phrased curated-manual outcomes as "RESOLVED_WITH_WARNING"; the implementation keeps a tier-4 winner at **RESOLVED_ALIAS with `matched_alias_id`** plus `IDENTITY_MANUAL_OVERRIDE`, because emitting `matched_alias_id` under any other status would violate the frozen validator law, and dropping the ID would destroy manual-mapping attribution. This wording deviation is disclosed here and in the vocabulary matrix's authority chain; no status name was invented.

## 6. Verification (measured, final tree)

B5-I03 tests: **69 passed** (test_b5_i03_resolver.py 47  -  including the two A12 regression pins  -  plus public-API and scope-audit suites). I01+I02 explicit regression suites: **413 passed**. Normalization package total: **482 passed**. Focused battery: **794 passed / 0 failed**. Full storage: **2019 passed / 13 skipped / 0 failed**. Full project: **3880 passed / 14 skipped / 0 failed** with 2 warnings  -  both the known inherited Windows manifest-concurrency teardown warning (`test_manifest_concurrency.py::TestPointerVisibility::test_readers_never_observe_partial_pointer`, reader-thread PermissionError on a temp pointer file), intermittent, recorded here per directive §25 and deliberately not repaired in I03. Zero deterministic failures.

Adversarial red-team: **25/25 PASS** (fresh run at the final tree; classes: same-tier ambiguity, alias overlap, half-open validity boundaries, provider-ID conflicts, venue mismatch, dangling references, lifecycle-state incompatibility incl. late knowledge, event-vs-knowledge disagreement, not-yet-known information, evidence naming, tier-ord conflict, permutation determinism (A12), duplicate registry records, referential integrity).

Evidence matrices, all regenerated after `61148c02e`, all rows measured with acceptance clause / probe / input condition / observed result / disposition / evidence reference (no prose-only rows): FUTURE_LEAKAGE 4/4 PASS, MATCH_ORDER 6/6 PASS, LIFECYCLE 9/9 PASS, ALIAS 6/6 PASS, ADVERSARIAL 25/25 PASS (mechanical wrapper over the red-team run; per-class acceptance-clause map disclosed in the artifact). Scope audit: `BLOC_05_I03_SCOPE_AUDIT.json`  -  identity files exactly the 7 authorized modules; forbidden modules absent.

Static: ruff changed scope all-pass (7 findings present mid-I03D were all fixed before sealing); mypy 0 identity findings (10 pre-existing providers/probes baseline unchanged); compileall OK; secret scan only the known lexical false positive `SemanticToken = ` (models.py:115).

## 7. I11R2 custody

Mechanical tracked-Python count regenerated: **1025 -> 1033** (`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`, exactly one line changed; no-update rerun byte-stable). Historical custody intact: Bloc 4, I17, B5-I01, B5-I02 evidence untouched; suite-generated informational dirt in eleven other bloc_04 JSONs restored before commit; the I06 spike file and `.bu_tmp/` remain untracked.

## 8. Evidence amendment (operator gap sweep, 2026-10-07, same day as sealing)

An operator-directed evidence sweep identified laws pinned by implementation omission rather than measurement. Three were closed in the B5-I03D scope (lifecycle-ROW state laws and warning-window boundary instants; the remaining sweep items are recorded for future operator decision and were NOT acted on):

* **RELISTED_NEW_INSTANCE lifecycle row is inert evidence** - a state row over a PIT-valid instance neither gates, warns, nor activates; the relisting cutover is carried by the NEW instance's own valid_from (S6 cutover law), never by the state row. Pinned by `test_relisted_new_instance_lifecycle_row_is_inert` and one new lifecycle-matrix row.
* **PRE_LISTING lifecycle row is inert evidence** - exactly the A7b law (DELISTED row over a live instance): a PRE_LISTING row about one instance never de-activates the instance's own PIT-valid interval. Pinned by `test_pre_listing_lifecycle_row_is_inert` and one new lifecycle-matrix row.
* **Warning windows are half-open [valid_from, valid_to)** - start-inclusive, end-exclusive; the downgrade fires exactly at the start instant, one microsecond before it the resolution is plain, and equally at/one microsecond before the end instant. Pinned for BOTH warning states (SUSPENDED, DELISTING_ANNOUNCED) x 4 boundary instants each by 2 boundary tests and 6 new lifecycle-matrix rows.

No production source change: the resolver already implemented these laws (S6/I03D33 warning enumeration); this amendment converts omission into measured evidence. Re-measured at the final tree: I03 tests **73 passed** (69 + 4 new pins); normalization package **486 passed**; I11R2 audit no-update byte-stable (4 passed, SHA `bebda72...` unchanged); full project **3884 passed / 14 skipped / 0 failed with 1 warning** (the known intermittent Windows manifest-concurrency reader-thread teardown race). Static: ruff all-pass, mypy 0 identity findings (10 pre-existing baseline), compileall OK, secret scan clean. Lifecycle matrix regenerated: **17 rows / 17 PASS, all 7 states enumerated** (was 9). Remaining known evidence gaps (recorded, not closed here): dual-clock `known_to` (superseded knowledge) coverage; provider-ID + wrong-venue tier-1 probe; stablecoin/negative-alias/flag matrix backfill; TERMS_UNVERIFIED reachability statement.

## 9. Knowledge-boundary closure amendment (B5-I03H, operator-directed, 2026-10-08)

Operator directive: Option 1 is authorized for records that possess
`known_to`: `known_from <= knowledge_cutoff < known_to`; an absent `known_to`
means an open-ended knowledge interval. This is a **prospective semantic
clarification**. It is not attributed to any earlier frozen contract, and no
previously sealed evidence was rewritten to accommodate it. `InstrumentAlias`
was **not altered**: its frozen eleven-field schema (section 8) carries no
`known_to` by frozen design, so alias knowledge intervals are open-ended by
construction and every historical alias test remains valid unchanged.

### 1. Production change (exactly one file)

`src/crypto_sensor_fabric/normalization/identity/resolver.py`:

- `_known_by(known_from, known_to, knowledge_cutoff)` now enforces the
  bounded knowledge interval on `ContractInstance` and `InstrumentLifecycle`
  eligible records (upper bound applied only when `known_to` is present).
- Call sites: `_pit_valid` (valid-time + knowledge gating),
  `_lifecycle_warning` (knowledge gating of applicable periods),
  `_tier_exact_symbol` (registry symbol scan); the alias scan passes `None`
  for the upper bound (frozen schema — open-ended by design).
- Blocking outcome for an expired knowledge record with no eligible
  candidate: the existing `PIT_KNOWLEDGE_BLOCKED` / `UNKNOWN` pair — no new
  status, flag, field, or enum member was fabricated, no supersession engine
  was built, and no replacement record is ever selected. Tier priorities,
  valid-time filtering, alias behavior, and fail-closed identity handling are
  unchanged.

### 2. Regression evidence (Phase 2 — knowledge clock verified independently)

Eleven new standing regressions in `tests/crypto_sensor_fabric/normalization/
test_b5_i03_resolver.py`, each probing the knowledge clock with the event
clock fixed inside the valid window (never substituted):

1. Before `known_from` → blocked (`PIT_KNOWLEDGE_BLOCKED`, no identity).
2. Exactly at `known_from` → resolves.
3. One microsecond before `known_to` → resolves.
4. Exactly at `known_to` → blocked (half-open upper bound).
5. After `known_to` → blocked.
6. Absent `known_to` with far-future cutoff → open-ended, resolves.
7. Historical event with later cutoff → resolves inside the window, blocks
   after `known_to` closes (event time unchanged).
8. Two revisions, nonoverlapping knowledge windows → gap cutoff blocked with
   no engine and no replacement; old-window probe answers with the OLD
   record; new-window probe answers with the NEW record (valid-time law).
9. Two eligible records stay `AMBIGUOUS` — eligibility never manufactures a
   winner; both live candidates observed.
10. Lifecycle warning with expired knowledge → warning inert; control at an
    eligible cutoff still warns.
11. G2: provider instrument ID on the wrong registered venue →
    `UNKNOWN_SYMBOL`, no identity payload; control on the right venue
    resolves (same venue probe asserted independently).

All 41 pre-existing resolver tests, the 73-test I03 block, and all valid-time /
lifecycle-boundary tests pass unchanged.

### 3. Evidence artifacts (Phase 3 — G1–G4 closure, minimum matrix growth)

- **G1 CLOSED** — new `BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json`: 14/14
  measured rows (KB1–KB10 + three lifecycle knowledge rows), generated by the
  extended `.bu_tmp/b5_i03_mats.py` (live resolver calls, no hand-authored
  verdicts).
- **G2 CLOSED** — `BLOC_05_I03_MATCH_ORDER_MATRIX.json` regenerated with the
  tier-1 venue-isolation row (wrong-venue probe measured live): 10/10 rows;
  standing regression above.
- **G3 CLOSED** — same matrix backfilled from existing verified behavior:
  exact-text negative probes (prefix / case-fold / separator →
  `NO_CANDIDATE`), the S12 stablecoin quote-asset firewall row (quote never
  substituted, canonical = underlying), and identity-flag coverage (four
  sanctioned-emitted flags observed live; the six sanctioned not-emitted
  flags absent from every probed path).
- **G4 CLOSED** — `BLOC_05_I03_SCOPE_AUDIT.json` regenerated with a mechanical
  AST pin: `TERMS_UNVERIFIED` is reserved (section 9 blocker set) and is
  never constructed through any I03 path (zero construction arguments across
  all seven identity modules). Terms verification machinery remains B5-I04+
  — not implemented here.
- FUTURE_LEAKAGE (4/4), LIFECYCLE (17/17) and ALIAS (6/6) matrices were
  re-measured from the changed tree and their outputs are byte-identical to
  the sealed artifacts (restored after regeneration); ADVERSARIAL red-team
  was re-measured unchanged (its fixtures carry no `known_to`); I02 matrices
  untouched; I11R2 audit not republished (byte-stable no-update).

### 4. Verification (measured, this tree)

I03 focused **84 passed** (73 + 11 new). Normalization package **497 passed**
(486 + 11). I11R2 binding/evidence **14 passed**, audit SHA
`bebda72beeaba50aa73b3c0032311282140f831ce0adcf2a813ce70a55cbfa8c`
byte-identical before/after, bloc_04 untouched. Deterministic generators all
re-run with all-pass summaries (vocabulary/future-leakage/match-order/
lifecycle/alias/knowledge-boundary/scope). Full project **3895 passed / 14 skipped / 0 failed (no warnings)** —
new failures: **none — 3895 = sealed baseline 3884 + 11 new; 14 skipped unchanged**; the known intermittent Windows
manifest-concurrency teardown race remains inherited TEST-ENVIRONMENT DEBT
(unrepaired by design). Statics: ruff changed scope all-pass; mypy 10
inherited / 0 identity; compileall OK; secret scan clean.

### 5. Remaining limitations (disclosed, not closed)

- Alias `known_to` semantics do not exist structurally (frozen schema,
  open-ended by construction) — documented, not a gap, and not a reason to
  alter `InstrumentAlias`.
- Overlapping knowledge windows across valid-time revisions follow the
  valid-time cutover law once both records are eligible; not separately
  probed.
- ADVERSARIAL red-team matrix not regenerated (fixtures carry no `known_to`;
  behavior path unchanged for alias rows).
- Inherited: Windows manifest-concurrency teardown race (test environment).

### 6. Disposition (recorded, not self-ratified)

The B5-I03 technical implementation now satisfies its authorized contract:
Option 1 enforced for `ContractInstance` and `InstrumentLifecycle`, frozen
`InstrumentAlias` schema preserved, G1–G4 closed with minimum matrix growth,
all measured verification green against the sealed baseline. This section
records evidence only — it does not promote any gate. `IDENTITY_GATE` =
`NOT_YET_EARNED`; `next_checkpoint_authorized` = `FALSE`; B5-I04+ =
UNAUTHORIZED; bloc 6 = UNAUTHORIZED; research = FROZEN. Acceptance is the
operator's call (HARD STOP after push).

---

## 10. Evidence correction record (B5-I03I, operator-directed, 2026-10-08)

Operator directive: correct demonstrable inconsistencies in the committed
I03 evidence and establish reproducibility of evidence generation from
tracked source. No identity semantics changed; production code untouched
(`resolver.py`, `aliases.py`, `lifecycle.py` byte-identical to the I03H
seal).

### 1. Original KB3 discrepancy

The sealed knowledge-boundary matrix narrated `cutoff =
2023-11-30T23:59:59.999999Z` for KB3 while claiming the cutoff equals
`known_to - 1 microsecond` with `known_to = 2023-12-01T12:00:00Z` — the
narrated instant sits 12 hours + 1µs BEFORE `known_to`, not one microsecond.
Independent reproduction (fixture rebuilt from the production models, not
importing the generator) proved the error was confined to hand-typed
`input_condition` narration: the generator executed
`K1 - timedelta(microseconds=1)` = `2023-12-01T11:59:59.999999Z`, a true
one-microsecond boundary. The narration strings had been copied from the
standing-test fixture, whose K0/K1 are midnight-based, while the generator
fixture is noon-based. The same narration error affected KB1
(`known_from - 1µs`) and KB5 (gap cutoff). No probe ever executed a wrong
timestamp; every observed status was measured at the claimed boundary; no
test result was relabeled.

### 2. Corrected executable input + measured result

KB1/KB3/KB5 `input_condition` strings now state the executed instants
(`2023-06-01T11:59:59.999999Z == known_from - 1us`,
`2023-12-01T11:59:59.999999Z == known_to - 1us < known_to=2023-12-01T12:00Z`,
and the KB5 gap cutoff re-anchored against the noon window) with the window
`[2023-06-01T12:00Z, 2023-12-01T12:00Z)` spelled out. Regenerated KB matrix:
**14/14 PASS**, `expected_status == observed_status` on every row.

### 3. Generator source custody

No frozen tracked generator existed; the producers lived only in `.bu_tmp/`.
The four deterministic producers were promoted verbatim to
`research/crypto_foundry/sensor_fabric/scripts/`: `b5_i03_mats.py`,
`b5_i03_scope.py`, `b5_i03_redteam.py`, `b5_i03_adv_wrap.py`. Only edits:
GEN_REF invocation strings now name the tracked path, the three narration
corrections above, and repo-convention `# noqa: E402` on the two post-`sys.path`
imports in redteam (matching existing tracked scripts). Invocation (from
`quant-lab/`): `PYTHONIOENCODING=utf-8 python
research/crypto_foundry/sensor_fabric/scripts/<name>.py`. Runtime dependency
on `.bu_tmp/` is zero (redteam results and the adversarial wrap read/write
next to the scripts); the remaining `.bu_tmp` strings inside the ADVERSARIAL
matrix are sealed-run provenance literals describing the original 2026-10-07
invocation, deliberately preserved. No scratch, cache, or I06 files were
promoted.

### 4. Artifact reproducibility (sha256; double-run byte-identical)

| Artifact | sha256 |
|---|---|
| BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json | `ae24942540a6b26a6096eefee3186a393482913d8f1d50f1ca2d6011387ffeac` |
| BLOC_05_I03_ALIAS_MATRIX.json | `efd7ac47f2c8852badc356e4fc60cdc7af8eb746f2ac92a19f313dad5a48c2bb` |
| BLOC_05_I03_FUTURE_LEAKAGE_MATRIX.json | `09b487e8622326a618be03373d20cb8dbf442520f931482d979e2df1850167bf` |
| BLOC_05_I03_LIFECYCLE_MATRIX.json | `4efae87d0772fed1f5a000eba1bd548a4459ddb028f4a4ebe63da0f4e6125ace` |
| BLOC_05_I03_MATCH_ORDER_MATRIX.json | `737e1d7846a8375f5809e593d32b7456483c4b7cfba6c08ccb295d7950a08a3f` |
| BLOC_05_I03_SCOPE_AUDIT.json | `92eb13a44166e5c9518068225d43e7346589b2fa23ab31f3b5283d00d5ec26a8` |

Re-running all four producers from tracked source reproduced all six
artifacts byte-identically (6/6). Run dates are pinned literals in the
scripts, not `date.today()`, so outputs are stable across days.

### 5. Test verification (this tree, vs I03H baseline)

- I03 focused: **84 passed** (baseline 84).
- Normalization: **497 passed** (baseline 497).
- I11R2: **14 passed**, byte-stability digest unchanged (baseline 14).
- Full project: **3895 passed / 14 skipped / 0 failed** in 1035.68s
  (baseline 3895/14).
- Static: ruff all-pass (changed scope), mypy 10 inherited / 0 identity,
  compileall OK, secret scan clean (new scripts included).

### 6. Cross-artifact audit + remaining limitations

Every lifecycle, match-order, future-leakage, alias, venue-isolation,
stablecoin, future-leakage-L1..L4, and scope-audit narration was audited
against its executed fixture values — all consistent; only the three KB
narrations were wrong (corrected above). `created` stamps on the
alias/future-leakage/lifecycle matrices moved 2026-10-07 → 2026-10-08
(regeneration day; row content unchanged apart from GEN_REF paths).

Limitations (disclosed, not masked): alias `known_to` remains structurally
absent (frozen eleven-field schema); cross-revision overlapping-knowledge
cutover not separately probed; ADVERSARIAL matrix not regenerated with new
rows (no `known_to` fixtures; byte-identical reproduction confirmed);
regenerating the sealed B4-I15 secret-safety matrix in this tree measures
`files_scanned` 132/309/257 vs sealed 122/279/207 (the workspace grew after
the B4-I15 seal — pre-existing, out of I03I scope; `result: OK` unchanged;
sealed bloc_04 restored, not rewritten); inherited Windows
manifest-concurrency teardown race not triggered this run.

### 7. Amendment A (B5-I03I re-verification, 2026-10-09): row labels in §10.1/§10.2

Prospective amendment appended to the sealed record; the sentences in §10.1
and §10.2 above are retained verbatim as originally published. On 2026-10-09
the I03I directive was re-verified against start head `67b7f4de1`: the sealed
knowledge-boundary matrix at `67b7f4de1` was diffed against the regenerated
matrix at current HEAD, and `input_condition` changed on exactly three rows —
**KB1, KB3, KB7b**.

- §10.1 states "The same narration error affected KB1 (`known_from - 1µs`) and
  KB5 (gap cutoff)". Measured: the affected rows are KB1, KB3 and **KB7b**
  (old narration `cutoff=2023-11-30T23:59:59.999999Z`; executed
  `K1 - timedelta(microseconds=1)` = `2023-12-01T11:59:59.999999Z`). KB5's
  `input_condition` (`cutoff=2023-12-02T12:00Z > known_to`) was already
  correct at the I03H seal and is unchanged by I03I. KB7b is the "cutoff
  inside the OLD knowledge window" row — neither the gap row (KB7a) nor KB5.
- §10.2's "KB1/KB3/KB5 `input_condition` strings now state the executed
  instants" should read **KB1/KB3/KB7b**. The parenthetical
  `2023-12-02T12:00:00Z` is KB5's executed instant (true, and never
  misnarrated); KB7b's corrected instant is `2023-12-01T11:59:59.999999Z`.

Error scope: prose row labels only — no matrix row, expected status,
observed status, flag, evidence reference, or artifact byte changed as a
result of this amendment. Re-verified 2026-10-09: all four tracked producers
ran twice from tracked source; 7/7 artifacts byte-identical to the committed
bytes (knowledge-boundary sha256 unchanged:
`ae24942540a6b26a6096eefee3186a393482913d8f1d50f1ca2d6011387ffeac`); all 76
matrix rows PASS (KB 14, leakage 4, match-order 10, lifecycle 17, alias 6,
adversarial 25) with zero expected/observed mismatches; an independent
fixture rebuilt from the production models (not importing the generator)
reproduces the five KB boundary verdicts 5/5. Custody: append-only; ledger
§167 records this amendment. No identity semantics, status, or gate changed.

---

## 11. Governance and divergence (recorded, not self-ratified)

`MAIN_DIVERGENCE_STATUS = EXTERNAL / UNRECONCILED / NON-BLOCKING_FOR_I03`  -  origin/main moved independently to `f89883471dbc93d481b43d73757c716afc817441` during the Bloc 5 workstream; per the FINALIZE directive no merge/rebase/cherry-pick/reset was performed and no reconciliation is implied. The build branch `agent/crypto-sensor-fabric-build` remains the checkpoint authority.

`PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED = PENDING_OPERATOR_REVIEW`; `BLOC_05_IMPLEMENTATION_STATUS = I03_COMPLETE_PENDING_OPERATOR_REVIEW`; `BLOC_05_NORMALIZATION_IMPLEMENTED = PARTIAL_PIT_IDENTITY_FOUNDATION`; `I03_IDENTITY_RESOLVER_SUBGATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`; `IDENTITY_GATE = NOT_YET_EARNED`; `next_checkpoint_authorized = FALSE`; recommended_next = OPERATOR REVIEW OF SENSOR-B5-I03; B5-I04+ UNAUTHORIZED; Bloc 6 UNAUTHORIZED; research FROZEN. I04 authorization occurs only after operator review of the pushed I03 final tree.
