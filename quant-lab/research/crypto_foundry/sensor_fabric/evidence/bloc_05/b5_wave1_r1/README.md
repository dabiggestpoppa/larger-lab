# SENSOR-B5-WAVE1-R1 — Independent verification and golden-fixture progress

**Label:** `SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT`
**Target:** `B5_WAVE1_INDEPENDENT_VERIFICATION_AND_FIXTURE_PROGRESS`
**Mission:** `SENSOR-B5-WAVE1-INDEPENDENT-AND-GOLDEN-FIXTURES-R1`
**Carrier branch:** `agent/crypto-sensor-fabric-b5-wave1-audit-r1`
**Frozen authority:** `4bb677f9e0266f4dc48405181696019f359ae49f`
**Accepted production candidate (unchanged):** `66200f3cb18ee5cea1483d986e64502f388eeb77`
**Prior milestone publication:** `a59fa400241874c6201669e799bfa2d7039019e5`

P3 is closed. Nothing in this package reopens it, re-runs it, or re-characterizes it.

---

## 0. Scope, and what this package does not do

This is an evidence-only commit on a new carrier branch. It contains no production
source change, no test change, no manifest change, no configuration change, and no
merge. Every prior audit branch still points at its own head
(`6c4874b43`, `6a1a7a5d6`, `d6b3f9f83`, `95c9ee01d`, `a59fa4002`).

| Hard stop | State |
| --- | --- |
| Production source changes | none |
| Unilateral provider approval | none |
| Fixture self-ratification | none — every fixture is `NOT_REVIEWED` / `ratified_golden: false` |
| Authority activation | none |
| Manifest changes | none |
| Merge | none |
| Trust or gate promotion | none — no gate is claimed |
| Bloc 6 advancement | none |
| Concurrent canonical execution | none launched |
| Re-run of the P3 matrix / mutations / consumer suite | none — not required, not performed |

`02_corpus_validation.json` re-checks all three laws mechanically: no fixture is
ratified, no Tier A fixture claims a capture, no Tier C record claims an offline
payload, and no synthetic record claims provider semantics.

---

## 1. What was actually published

The implementation branch `agent/crypto-sensor-fabric-b5-wave1-r1` named in the
mission **does not exist** — locally or on the remote — and no `I12`–`I15` module
exists anywhere in this repository's history:

```
git log --all --oneline -- '*normalization/sensors/oi.py'        -> (empty)
git log --all --oneline -- '*normalization/sensors/funding.py'   -> (empty)
git log --all --oneline -- '*normalization/sensors/book.py'      -> (empty)
git log --all --oneline -- '*normalization/sensors/positioning.py' -> (empty)
git log --all --oneline -- '*normalization/sensors/basis.py'     -> (empty)
git log --all --oneline -- '*normalization/lineage/__init__.py'  -> (empty)
git log --all --oneline -- '*normalization/query/__init__.py'    -> (empty)
```

Measured at the audited head (`01_checkpoint_state.json`):

| Checkpoint | Expected path | Published? | Wave 1 state |
| --- | --- | --- | --- |
| I10 trade | `sensors/trade.py` | yes | accepted, not reopened |
| I11 liquidation | `sensors/liquidation.py` | yes | accepted, not reopened |
| I12 OI | `sensors/oi.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I13 funding | `sensors/funding.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I14 book / book metric | `sensors/book.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I15 positioning | `sensors/positioning.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I15 basis | `sensors/basis.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I16 lineage | `lineage/__init__.py` | **no** | `BLOCKED_PENDING_IMPLEMENTATION` |
| I17 duplicates | `duplicates/__init__.py` | **no** | not started |
| I19 query | `query/__init__.py` | **no** | not started |

Two further substrate facts, measured rather than assumed:

* `config/crypto_sensor_fabric/provider_semantics/approval_manifest.json` has
  `artifacts: {}` and `revoked_approval_ids: []`, authority id
  `B5_I09P2A_EMPTY_TRUST_ROOT_V1`. **No semantic admission is possible**, so any
  canonical funding, positioning or basis claim is currently unrepresentable. A
  normalizer that emitted one would be a defect, not a feature.
* `B5_I08_UNITS_V1` is absent from `methodology_registry.yaml` (9 methodology ids,
  all `PROVISIONAL`). Every `*_usd` field therefore stays blocked. This is the
  documented `UNIT_GATE` state, not a new finding, and it is why §3 treats the
  blocked-USD behaviour as a positive control rather than a gap.

Because I12–I15 have no entry point, no claim about them can be admitted. That is
the rolling verification result, and it is reported as pending — not as a pass.

### 1.1 Carrier-tree disclosure

The branch was first cut from the audit-r4 carrier (`a59fa4002`), and that carrier's
production tree **trails the accepted candidate by nine files** — `normalization/consumer/custody_authority.py`,
`normalization/consumer/policy.py`, and seven P3 consumer/replay test modules from
the F4/F5 repair series. Those commits carry evidence only; the production delta
comes from the audit lineage forking before the candidate's repairs.

The evidence was therefore re-published on a carrier based on the P3 publication
`96f4cd28e`, whose production tree is byte-identical to `66200f3cb` (verified:
`git diff 66200f3cb HEAD -- quant-lab/src quant-lab/tests quant-lab/config` is
empty), and the whole harness was re-run there. Every module these probes touch —
`sensors/trade.py`, `sensors/liquidation.py`, `terms/conversion.py`, `enums.py`,
`methodology_registry.yaml`, `provider_semantics/approval_manifest.json` — is
identical on both trees, and the re-run reproduced all seven result artifacts
**byte-for-byte**. The prior audit branch is preserved unchanged at `a59fa4002`.

This is disclosed rather than silently corrected because a reader could otherwise
reasonably assume an evidence branch's production tree is the candidate's.

---

## 2. I12–I15 rolling independent verification

Method: probe the entry points themselves, then exercise the shared substrate the
unpublished checkpoints will have to honour. Nothing is inferred from a worktree
that does not exist.

| Checkpoint | Entry point probe | Cases prepared | Verdict |
| --- | --- | --- | --- |
| I12 OI | `ModuleNotFoundError` | 10 | `BLOCKED_PENDING_IMPLEMENTATION` |
| I13 funding | `ModuleNotFoundError` | 10 | `BLOCKED_PENDING_IMPLEMENTATION` |
| I14 book / book metric | `ModuleNotFoundError` | 14 (8 sequence-gap) | `BLOCKED_PENDING_IMPLEMENTATION` |
| I15 positioning / basis | `ModuleNotFoundError` | 10 | `BLOCKED_PENDING_IMPLEMENTATION` |

Substrate controls that *do* execute today (`03_i12_i15_rolling_verification.json`):

* the USD derivation is blocked with `unresolved_citation = B5_I08_UNITS_V1`, and
  `B5_I08_UNITS_V1` is confirmed absent from the config registry — the block is
  attributable, not merely absent;
* a diagnostic registry (correct shape, no authority) yields
  `provisional = SELL` while the canonical side stays `UNKNOWN`;
* with no registry at all, even the provisional mapping is `None` — the mapping is
  never guessed;
* `SEMANTICS_UNVERIFIED` is present on the refused row.

These are the behaviours I12–I15 must preserve. When they publish, the 44 prepared
fixtures become executable without further authoring.

---

## 3. Independent controls against the published families (I10 / I11)

`04_i10_i11_fixture_execution.json` — **20 assertions, 20 passed**, through the real
`normalize_trade` and `normalize_liquidation` entry points.

Covered laws:

* native price and quantity survive normalization unchanged;
* a documented-but-unapproved provider boolean yields `provisional = SELL` (and the
  mirrored `BUY` for `isBuyerMaker=false`) while the canonical side stays `UNKNOWN`;
* price direction is never an input to a side (the adversarial case still refuses);
* a stablecoin quote raises `STABLECOIN_CONVERSION_UNAVAILABLE`, emits no USD twin,
  and cites `B5_I08_UNITS_V1`;
* liquidation keeps position side and execution side separate, and a single
  collapsed `side` leaves both canonical fields `UNKNOWN`;
* `liquidation_usd` is blocked, never zero;
* a non-zero row keeps `zero_interval_state = NOT_APPLICABLE`.

---

## 4. I21 property controls

`05_i21_property_controls.json` — **10 controls, 10 passed**.

| # | Property | Result |
| --- | --- | --- |
| P1 | identical input → byte-identical record | holds |
| P2 | execution-order change does not alter a record | holds |
| P3 | native value survival (price, quantity) | holds |
| P4 | null ≠ zero (blocked amount is `None`) | holds |
| P5 | flags unique and in declared canonical order | holds |
| P6 | no cross-venue dedupe for identical economics | holds |
| P7 | registry shape is not authority (canonical side `UNKNOWN` both ways) | holds |
| P8 | liquidation null ≠ zero | holds |
| P9 | normalizer code is network-free and clock-free | holds |
| P10 | a blocked amount cannot carry a value | holds |

Machine-local state control: the whole harness was run twice, with
`PYTHONHASHSEED` 0/UTC and 777/Europe-Berlin substitute-timezone (and earlier
0/UTC vs 12345/Asia-Tokyo). All seven result artifacts were **byte-identical**
across runs, and the run digest is stable at
`3beec3bafcfd296e7a26f6706517c053ba9d12d0d91a310ef80697e2b5cd6e0d`.

---

## 5. I16 preparation

`06_i16_lineage_id_preparation.json` — state `BLOCKED_PENDING_IMPLEMENTATION`.

Prepared and measured:

* the T1 record has **no** `t1_record_id` / `record_id` / `id` field; the tree mints
  no T1 identity yet, so a deterministic-ID claim would be unsupported;
* content digests are stable across repeats, interleaving, revisions and processes —
  the property a future ID must inherit;
* `normalization_generation` is a caller-supplied passthrough today, not a
  derived immutable generation;
* lineage carries `raw_projection_refs`, `acquisition_refs`,
  `evidence_blob_hashes`, `code_version`, `config_version` and
  `conversion_lineage_refs` with `lineage_state = LINEAGE_COMPLETE`;
* identical duplicate blob references are refused at input construction;
* a changed `source_revision_id` changes content, so a revision cannot silently
  reuse the prior record's identity.

**`LINEAGE_GATE` is not claimed, and must not be**: there is no lineage package, no
deterministic T1 ID, and only 2 of 8 sensor families are implemented. Closing the
gate on that set would be the partial-sensor-set error the inventory warns about.

---

## 6. I20 corpus — what exists, and what it is not

`fixtures/corpus_manifest.json` — **58 fixtures**, corpus digest
`b15278b0696036dbdcce7dafa1fab677ba22daa01ce4c9403ba4eda13aa6295b`
(sha256 over sorted `<path>\0<sha256>\n` rows), per-file digests pinned.

| Tier | Count | What it can prove | What it cannot |
| --- | --- | --- | --- |
| `TIER_A_DOCUMENTED_FIELD_SHAPE` | 27 | the normalizer handles the provider's documented field vocabulary and units | anything about provider semantics or real values |
| `TIER_B_SYNTHETIC_ADVERSARIAL` | 28 | refusal and reconstruction behaviour | actual provider semantics |
| `TIER_C_PROVIDER_EVIDENCE_REFERENCED` | 3 | that provider evidence exists at a recorded level | usable input — the payload bytes are not retained offline |

Coverage achieved (machine-checked in `02_corpus_validation.json`):

| Requirement | Result |
| --- | --- |
| ≥ 3 providers | **7** — Binance USD-M, Gate Futures, Deribit, OKX Swap, Bybit Linear, Kraken Futures, Coinalyze |
| BTC and an altcoin | BTC + ETH |
| Linear and inverse | `LINEAR_PERPETUAL` + `INVERSE_PERPETUAL` (Deribit, OKX `BTC-USD-SWAP`, Kraken `PI_XBTUSD`) |
| All required sensor families | 8/8 — trade, liquidation, OI, funding, book snapshot, book metric, positioning, basis |

Tier A by provider: Binance 10, Deribit 5, OKX 4, Gate 3, Kraken 3, Bybit 2.
Fixtures by checkpoint: I10 5, I11 4, I12 10, I13 10, I14 14, I15 10, plus 2
identity/time cases and 3 Tier C evidence references. **44 fixtures are ready and
waiting on I12–I15 entry points.**

Every record carries the twelve required metadata fields: provider, instrument
identity, contract type, sensor family, exact source, acquisition provenance,
native units, timestamp semantics, semantic claim, evidence digest, known
limitations, approval status.

### 6.1 The corpus is not golden evidence, and cannot be made so by this agent

No fixture is ratified (`ratified_golden: false`, `approval_status: NOT_REVIEWED`
throughout). The reason is measurable, not procedural:

**no first-party captured payload bytes are retained anywhere in this repository.**
Bloc 2 evidence is existence/metadata level (`E0_CLAIM_ONLY`, `E4_MULTI_ERA_VERIFIED`,
`SOURCE_AVAILABILITY_VERIFIED only — row timestamps/schema not inspected`). Bloc 3
network-smoke records HTTP status, row counts and a `raw_content_hash` — but not the
payload. Therefore Tier A reconstructs *field shape* from the frozen in-repo
documentation, with authored values, and says so in every record.

The three Tier C records point at the strongest available evidence
(Binance OI E4 multi-era, Deribit live book smoke with
`raw_content_hash = 25ea4221…`, Binance funding E0/GEO_BLOCKED) and are explicitly
**unusable as inputs**. Promoting any of them to golden evidence would require
inventing the payload, which is fabrication.

---

## 7. I14 sequence-gap matrix (authored, pending entry point)

Eight controllable offline cases, all `TIER_B_SYNTHETIC_ADVERSARIAL`, family
`MECHANICAL_BOOK_SNAPSHOT`, with the required outcome recorded per case:

| Fixture | Case | Required outcome |
| --- | --- | --- |
| `FX-B-SEQ-VALID-CONTIGUOUS-001` | valid contiguous chain from `lastUpdateId+1` | `RECONSTRUCT_OK`, metrics allowed |
| `FX-B-SEQ-MISSING-001` | update 2006 absent | `REFUSE` / `BOOK_SEQUENCE_GAP`, no interpolation, no partial-book publish |
| `FX-B-SEQ-DUPLICATE-001` | bit-identical update replayed | `IDEMPOTENT_OR_REFUSE` / `DUPLICATE_SEQUENCE_RECORD`, never double-applied |
| `FX-B-SEQ-OUT-OF-ORDER-001` | later update arrives first | `REFUSE` / `SEQUENCE_DISCONTINUITY`, no silent reordering |
| `FX-B-SEQ-SNAPSHOT-UPDATE-MISMATCH-001` | first update neither overlaps nor continues | `REFUSE` / `SNAPSHOT_UPDATE_MISMATCH` |
| `FX-B-SEQ-RESET-001` | sequence resets to 1 | `REFUSE` / `SEQUENCE_RESET_REQUIRES_SNAPSHOT` |
| `FX-B-SEQ-METRIC-ACROSS-GAP-001` | spread / depth / imbalance requested over a gap | `REFUSE` / `METRIC_ACROSS_GAP_REFUSED`, no stale book served |
| `FX-B-SEQ-RECOVERY-SNAPSHOT-001` | authorized recovery snapshot, then contiguous | `RECONSTRUCT_OK_AFTER_RECOVERY`, pre-gap book discarded, 2 epochs |

**Interface proposal for Agent 1 (not a requirement, not a blocker).** The matrix is
normalizer-agnostic and holds no code dependency. For I14 to consume it, the entry
point needs to accept: a snapshot with a sequence cursor, an ordered update list with
`(U, u, pu)` or `(seq, prevSeq)`, and an explicit recovery-snapshot argument carrying
an authorization reference. The expected refusal codes above are the frozen
`BOOK_SEQUENCE_GAP` vocabulary from `bloc_05/04` §16 plus the
`NormalizationQualityFlag` members already declared in `enums.py`
(`BOOK_SEQUENCE_GAP`, `BOOK_PARTIAL_ONLY`, `TIME_SEQUENCE_MISSING`). Nothing here
proposes new semantics. No Agent 1 process was stopped or blocked for this.

---

## 8. Material findings and repair requirements

`60_FINDINGS.json` carries the machine-readable form. Summary:

| ID | Severity | Finding | Owner |
| --- | --- | --- | --- |
| `F1` | material | Binance `sumOpenInterest` unit and bucket aggregation function are undocumented, so I12 must emit `OI_UNIT_UNVERIFIED` rather than pick one | Agent 1 + provider evidence |
| `F2` | material | Bybit funding history omits the interval; Kraken's route returns a sampled series whose sample interval ≠ funding interval. An 8h default is unsound | Agent 1 + provider evidence |
| `F3` | material | No reviewed free route publishes a provider-native book metric; `MECHANICAL_BOOK_METRIC` at T1 must be Fabric-defined with a registered methodology (`DEPTH_BPS_RECONSTRUCTION_V1` is still `PROVISIONAL`) | Agent 1 (I14) |
| `F4` | material | No reviewed route publishes a provider-native basis, and positioning vocabularies differ by population; cross-venue basis and cross-provider ratio equivalence must refuse | Agent 1 (I15) |
| `F5` | material | No first-party captured payload bytes are retained; I20 cannot be ratified from the current evidence base | Agent 1 + operator (capture retention) |
| `F6` | blocking for I16 | No lineage package, no deterministic T1 ID; `LINEAGE_GATE` unclaimable and must not be claimed on 2/8 families | Agent 1 (I16) |
| `F7` | observation | `B5_I08_UNITS_V1` absent from the methodology registry — every `*_usd` stays blocked (positive control, not a defect) | operator (I08 admission) |
| `F8` | positive | I10/I11 hold 20/20 fixture assertions and 10/10 property controls, including cross-process determinism | none |
| `F9` | process | I14 fixture interface proposed; awaiting Agent 1 publication, no block issued | none |
| `F10` | process (self) | the audit-r4 carrier's production tree trails the candidate by nine consumer/test files; evidence re-published on a candidate-exact tree and re-run byte-identically | resolved |

No finding is a request to change accepted behaviour. `F1`–`F5` are evidence
dependencies, `F6` is sequencing, `F7` is an operator decision.

---

## 9. CoinGlass exploratory lane

`50_COINGLASS_BENCHMARK.md`. Conclusion: CoinGlass Legend is a **UI product**
(`legend.coinglass.com`: supercharts, liquidity heatmap, footprint, large trades),
not an API tier. The API is paid-only with **no free tier**, commercial use requires
Standard ($379/mo) or above, and modelled liquidation heatmaps are not realized
liquidation events. No scraping, no purchase, no signup, no endpoint call was made.
It is recorded as an optional corroboration candidate with four hard preconditions,
and is **not** a production dependency.

---

## 10. Remaining fixture and authority dependencies

1. **Captured payload retention** — one first-party payload per (provider, family,
   instrument) with SHA-256, endpoint, and acquisition time. Without it no Tier A
   fixture can become golden, and I20 cannot be ratified.
2. **I09 semantic admission** — the approval manifest is empty; canonical side,
   positioning and basis claims stay unrepresentable until approved artifacts exist.
3. **`B5_I08_UNITS_V1`** — operator admission decision; blocks `oi_usd` (I12) and any
   rate-based USD figure (I13).
4. **Funding interval evidence** — per-instrument interval for Bybit and Kraken.
5. **OI unit + aggregation documentation** — Binance bucket semantics.
6. **I12–I15 publication SHAs** — release the 44 prepared fixtures for execution.
7. **Recovery-snapshot authorization record** — for the I14 recovery case, so
   "authorized recovery" is a fact rather than a fixture flag.

---

## 11. Non-claims

* not organizationally independent;
* no gate claimed (`gates_claimed: []`) — `SEMANTIC_GATE`, `UNIT_GATE`,
  `LINEAGE_GATE`, `GOLDEN_T0_T1_GATE` remain open;
* no provider semantics established, no provider approved;
* no fixture ratified as golden evidence;
* no claim that any I12–I15 behaviour is correct — there is no implementation to test;
* no claim about CoinGlass data quality beyond its published documentation;
* the corpus proves *our* refusal and reconstruction contracts, not any venue's truth.

---

## 12. Reproduction

```bash
QUANT_LAB=.worktrees/p3-rung1-audit-prep/quant-lab
EVIDENCE=$QUANT_LAB/research/crypto_foundry/sensor_fabric/evidence/bloc_05/b5_wave1_r1

# 1. re-author the corpus (writes fixtures/ and fixtures/corpus_manifest.json)
B5_WAVE1_EVIDENCE="$PWD/$EVIDENCE" python probes/author_corpus.py.txt

# 2. re-run the verification harness (writes results/)
B5_QUANT_LAB="$PWD/$QUANT_LAB" B5_WAVE1_EVIDENCE="$PWD/$EVIDENCE" \
  python probes/probe_wave1.py.txt

# 3. verify the package digest
sha256sum -c "$EVIDENCE/EVIDENCE_DIR.sha256"
```

The probe scripts are shipped as `.py.txt` so this branch adds **no tracked Python
module** and cannot alter collected-test counts. Running them is expected to
reproduce the corpus digest and run digest quoted above byte-for-byte.
