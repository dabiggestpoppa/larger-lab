# BLOC 05 / SENSOR-B5-I09P1 — ADVERSARIAL TEST CONTRACT

**Companion to:** `BLOC_05_I09P1_REGISTRY_TRUST_BOUNDARY.md`
**Starting HEAD:** `05eb98aae110946713562535ac772b6af057532e`
**Harness:** `.bu_tmp/probe_i09p1.py` — disposable, untracked, never staged, writes no repository file.
**Posture:** no production or test byte is changed by this checkpoint. Every authority used below is **SYNTHETIC**.

---

## 1. What the harness is, and what it is not

It is a **falsifiable contract**: it measures the current surface, then models the proposed boundary and requires that model to reject the same seven inputs. It is not a producer, not an evidence artifact, not a reusable test suite, and not a claim about any venue.

Three labels are used, and no row may carry a label other than these:

| label | meaning |
|---|---|
| `CURRENT_BEHAVIOR_REPRODUCED` | executed against the real package today; the gap is real |
| `PROPOSED_TEST_ONLY` | executed against a design simulation inside the harness; proves the *design* rejects the input, not that production does |
| `NOT_EXECUTABLE_UNTIL_IMPLEMENTATION` | requires P2 source to exist before any measurement is possible |

A planned test is never reported as a passing production test.

Measured totals: **26 rows — 7 `CURRENT_BEHAVIOR_REPRODUCED`, 15 `PROPOSED_TEST_ONLY`, 4 `NOT_EXECUTABLE_UNTIL_IMPLEMENTATION`; 7 gaps reproduced, 0 unexpected, exit 0.**

---

## 2. Part A — the seven gaps, reproduced today

Executed through `ProviderSemanticRegistry(...)` and `normalize_liquidation(...)` only (public constructors). Every row is labelled `SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION`.

| gap | input | measured observation |
|---|---|---|
| G1 | caller-minted registry, invented evidence string, `VERIFIED_FIRST_PARTY` | `position=LONG execution=SELL admissions_all_admitted=True SEMANTICS_UNVERIFIED=False` |
| G2 | `methodology_id` no registry contains | `admitted=True position=LONG cited=['METHODOLOGY_THAT_DOES_NOT_EXIST_V99', …]` |
| G3 | Kraken evidence string on a `BINANCE_USDM` row | `admitted=True evidence=['KRAKEN_FUTURES_PUBLIC_API_DOCS_v4.pdf']` |
| G4 | native field no venue publishes | `admitted=True position=LONG` |
| G5 | `transformation="do_whatever_looks_right"` | `admitted=True transformation_accepted=True` |
| G6 | assumption asserting execution side *is* position side | `admitted=True four_way_separation_still_asserted=True` |
| G7 | hand-minted admitted decisions with an invented evidence reference | `ACCEPTED_WITH_CANONICAL_LONG` |

G7 is the most consequential: the record-level law validates a **hand-built** admission whose evidence string exists nowhere, so model validity does not imply upstream authorization.

---

## 3. Part B — the proposed boundary, simulated

### 3.1 Two authority roles

The model deliberately separates actors, because the whole finding is that today one actor can be both:

* **Untrusted author** — mints artifact bytes, and may put any digest it likes *inside* those bytes.
* **Trusted approver** — owns the manifest: the expected digest, the permitted methodologies, the per-provider evidence bindings, the declared native fields, the approved transformations and assumption resolutions.

The loader holds no authority of its own: it compares bytes to the **manifest**, so the untrusted author's self-declared digest is structurally irrelevant.

### 3.2 Measured rejections

| gap | probe | measured outcome |
|---|---|---|
| G1 | artifact carrying its own self-declared digest | `DIGEST_MISMATCH` |
| G1 | self-approval attempt: rewrite bytes *and* the digest beside them | `DIGEST_MISMATCH` |
| G2 | approved bytes citing an unregistered methodology | `UNREGISTERED_METHODOLOGY` |
| G3 | approved bytes whose row cites another venue's evidence | `EVIDENCE_NOT_BOUND_TO_PROVIDER` |
| G4 | approved bytes declaring an unpublished native field | `NATIVE_FIELD_NOT_DECLARED` |
| G5 | approved bytes with an unapproved transformation | `TRANSFORMATION_NOT_APPROVED` |
| G6 | approved artifact whose blocking assumption is unresolved | `BLOCKING_ASSUMPTION_UNRESOLVED` |
| G7 | hand-minting the authority object with a forged approval id | `TypeError: loader-only constructor` |
| G7 | a plain dict claiming admission, no loader-issued context | `UNTRUSTED_AUTHORITY` |

The self-approval row is the one directive §03 demands: changing both the artifact and its embedded expected digest does **not** produce an approval, because the expectation lives in the manifest the author cannot edit.

### 3.3 Positive control (synthetic authority, explicitly not provider documentation)

The same bytes approved through the manifest load and admit:

`admitted=True approval_id=SYNTHETIC-APPROVAL-1 digest=79e7f141882c…`

This row exists to prove the gate is not a blanket refusal: authority is the thing that moves it, and that authority is labelled synthetic in every field it touches.

### 3.4 Mutation and lifecycle

| probe | measured outcome |
|---|---|
| consumer called with no authority context | `UNTRUSTED_AUTHORITY` |
| single-bit mutation of approved bytes | `DIGEST_MISMATCH` |
| confidence rung edited after approval | `DIGEST_MISMATCH` |
| replay of a previously valid, now revoked approval | `APPROVAL_REVOKED` |
| two loads of identical bytes | `same_digest=True same_approval=True row_count=4` (deterministic) |

---

## 4. Part C — rows that cannot be measured yet

| row | why blocked |
|---|---|
| I10 consumer requires the context | `normalize_trade` types its registry as `object`; adoption is a P2 source change |
| I11 consumer requires the context | `normalize_liquidation` takes a public `ProviderSemanticRegistry`; the gate is a P2 source change |
| record-level digest persistence | no `registry_digest`/`approval_id` field exists on any T1 record today |
| approval lifecycle (rotation, expiry, revocation) | the harness models revocation; the real operator review workflow cannot be measured here |

Reporting these as passing would be exactly the "documentation alone" failure directive §09 forbids.

---

## 5. The contract P2 must satisfy

Executable, non-negotiable, one test each:

1. `test_approved_artifact_requires_manifest_entry` — no entry ⇒ refusal.
2. `test_authority_rejects_self_declared_digest` — artifact-supplied digest is ignored.
3. `test_bit_flip_detected` — one changed byte ⇒ `DIGEST_MISMATCH`.
4. `test_confidence_tamper_detected` — post-approval rung edit ⇒ `DIGEST_MISMATCH`.
5. `test_authority_rejects_unregistered_methodology`.
6. `test_authority_rejects_foreign_evidence`.
7. `test_authority_rejects_foreign_provider_row`.
8. `test_authority_rejects_undeclared_native_field`.
9. `test_authority_rejects_unapproved_transformation`.
10. `test_authority_blocks_unresolved_assumption`.
11. `test_authority_context_not_constructible_by_caller`.
12. `test_trade_consumer_refuses_plain_registry`.
13. `test_liquidation_consumer_refuses_plain_registry`.
14. `test_record_carries_registry_digest`.
15. `test_revoked_approval_refused`.
16. `test_expired_approval_refused`.
17. `test_same_bytes_same_digest`.
18. `test_positive_synthetic_approval_admits` — the gate is not blanket.
19. `test_two_actor_self_approval_impossible` — the P1 demonstration, promoted to a real suite.
20. `test_empty_manifest_admits_nothing` — the shipping default.

**Fixture law:** every suite row is labelled synthetic in its own bytes; no test may assert a real venue's semantics, and no manifest entry may be created to make a test pass.

---

## 6. Fidelity caveats (stated so the model is not over-read)

1. The simulation proves the **design** is falsifiable; it does not prove the production seam exists. Adoption is P2.
2. The manifest is passed as bytes in the harness; in production its provenance is a reviewed commit, and that review is a human process the harness cannot model.
3. The harness models revocation and expiry as data, not as an operator workflow with latency and mistakes.
4. A digest establishes approved-byte integrity only. It cannot establish that a venue's documentation supports a claim; that remains `B5-I09b`, externally blocked.
5. The `ARTIFACT_NOT_APPROVED` branch exists in the model but was not the code path reached by the G1 probes: those presented the *approved* artifact id with different bytes, so digest verification refused first. The branch is covered by contract test 1, not by this run.
