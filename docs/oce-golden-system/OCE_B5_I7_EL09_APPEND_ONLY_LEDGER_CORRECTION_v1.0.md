# OCE B5-I7 — EL09 X1: append-only ledger evidence law correction

**Stage:** `B5-I7-EL09-X1` (corrective rung of the ratified B5-I7 evidence law set)
**Status:** correction implemented; subject to CI and same-agent audit
**Base:** `7393228dd4b21be9440785204ea9e640800d5d95` (merged `origin/main`, PR #20)
**Authority:** operator directive `AUTHORIZED_STAGE=B5-I7-EL09-APPEND-LAW-X1_AND_B5-I8-P0-RESUME`
**Cost:** `$0` · **Cloud/provider mutations:** 0 · **`capital.authority = none`**

---

## 1. Subject

`B5I7-EL09` ("manifest rows are recomputed from bytes, never typed in") is enforced by
`infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py::TestEL09::test_manifest_rows_recomputed_hash_and_size`.
One of the thirteen rows it verifies is the Book 5 progress evidence ledger — a document that
**is append-only by law**. This correction repairs the verifier's permanent whole-file
interpretation for that one path. It does not touch the historical row.

## 2. The historical row remains accurate

| Field | Value |
|---|---|
| path | `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` |
| sha256 (LF-normalized) | `83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30` |
| size_bytes | `191950` |
| attested at | `08bf0b2dd14ca7b9bdd7f4dc32bb25297f42dbcd` (B5-I7 implementation head) and `7393228d…` (PR #20 merge) |

Recomputed at both commits: **13/13 rows match** the frozen manifest. The row was, and remains,
an accurate attestation of the complete ledger at B5-I7 ratification. **The row is not false and
was not edited.** It is reproduced byte-for-byte in the frozen addendum
`OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json`.

## 3. The defect

The ledger is explicitly append-only: the Book 5 governance rule requires every stage to preserve
prior bytes and append its own evidence. `B5-I7` itself appended `§18.11` this way, and the next
authorized stage (B5-I8 P0) appended `§19` legitimately.

The original checker asserted, for every row:

```
sha256(whole_current_file) == row.sha256  and  len(whole_current_file) == row.size_bytes
```

For an append-only document that is unsatisfiable the moment any later stage does what the law
requires. Observed failure (not inferred):

| Field | Value |
|---|---|
| run | `41724079443` (attempt 2), job `126232778697`, artifact `13274838782` |
| head | `145d31e9849c0b8ea67477f744210d0270a4f4cc` (PR #21, B5-I8 P0) |
| failing node | `TestEL09::test_manifest_rows_recomputed_hash_and_size` |
| assertion | `OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md: hash mismatch` |
| observed | `2b139f1211c2f8e382c0b29d974e1dc2a8469c8997507c4c1bc32e3e6424218b` / `198231` |
| attested | `83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30` / `191950` |

The append was legitimate, the row was truthful, and the verifier was wrong in exactly one
respect: it applied a whole-file equality test to an immutable-prefix obligation.

## 4. Corrected invariant

For the exact Book 5 ledger path only:

```
current_bytes[:191950] == historical_bytes
sha256(current_bytes[:191950]) == 83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30
len(current_bytes) >= 191950
```

Properties enforced:

- no historical byte may change (any mutation, insertion, deletion, truncation, reordering or
  same-length substitution inside the prefix fails);
- the ledger may only grow;
- appended suffix bytes are **that stage's** evidence and are explicitly **not** claimed as covered
  by the historical row;
- the historical digest and size are used unchanged, as recorded.

The prefix length is taken from `row.size_bytes` and the digest from `row.sha256`; neither is
recomputed, retyped or relaxed.

## 5. Verification modes (fail-closed)

| Mode | Applies to | Test |
|---|---|---|
| `whole_file` | every manifest row except the exact ledger path | exact size **and** whole-file digest |
| `append_only_prefix` | exactly `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | prefix digest over `size_bytes` + monotonic size |

Rules:

- classification is by **exact path equality**, never substring, suffix or extension matching;
- exactly one ledger row must exist — a missing or duplicated ledger row fails;
- an optional `verification` field is validated if present: an unknown value fails, and a value
  that contradicts the governed classification fails (so no unrelated file can be declared
  append-only, and the ledger cannot be declared whole-file);
- digest must be 64 lowercase hex; size must be a non-negative integer;
- CRLF→LF normalization is identical to the original manifest law;
- the row population of the superseding manifest must equal the historical population.

## 6. Superseding manifest (why one is needed)

The verifier is itself a manifest row. Correcting it necessarily changes its own bytes, so its
historical row cannot also describe it. Rather than edit the frozen addendum — forbidden — this
correction introduces:

`docs/oce-golden-system/OCE_B5_I7_EL09_X1_SUPERSEDING_MANIFEST_v1.0.json`

- `preserved_rows: 12` — twelve rows are **byte-for-byte copies** of the historical rows, and the
  law asserts that equality, so the correction cannot quietly weaken any immutable target;
- `revisioned_row` — the verifier, pinned by **exact whole-file hash and size** of the corrected
  file (not existence-only);
- `ledger_prefix_row` — the historical ledger digest and size, unchanged;
- `historical_manifest` — digest and size of the frozen addendum it derives from.

The frozen addendum `OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` is **not modified**.

## 7. Control inventory

Executed inside the frozen node (no new nodes; the inventory stays at 27).

Positive controls (4): real repository; single valid suffix; multiple suffixes; immutable target
passes only under exact equality.

Negative controls (17), each refused **by the law** and asserted on its message:

| Control | Expected refusal |
|---|---|
| mutate one prefix byte, same total size | immutable prefix hash mismatch |
| alter a prefix newline | immutable prefix hash mismatch |
| insert bytes inside the prefix | immutable prefix hash mismatch |
| delete bytes inside the prefix | shorter than the historical prefix |
| truncate below 191950 | shorter than the historical prefix |
| reorder prefix content | immutable prefix hash mismatch |
| wrong digest | immutable prefix hash mismatch |
| wrong size | shorter than the historical prefix |
| malformed digest (uppercase) | not 64 lowercase hex |
| unknown verification mode | unknown verification mode |
| missing ledger row | exactly one Book 5 ledger row |
| duplicate ledger row | duplicate path |
| unrelated file declared append-only | contradicts the governed mode |
| append to an immutable non-ledger target | that path: size mismatch |
| same bytes under a different path | different path: size mismatch |
| fabricate/alter a preserved historical row | historical manifest row was rewritten |
| (frozen falsification retained) | manifest verification fails |

## 8. What did not change

- historical manifest row: **byte-identical**, digest and size untouched;
- frozen B5-I7 addendum, record, reuse inventory, mutation results, acceptance matrix,
  operator ratification: **not modified**;
- production tree (`infrastructure/console/**`): **not modified** — no panel, CLI or packaging
  behaviour changed;
- CI workflow: **not modified** (the existing whole-file selection picks up the corrected law);
- no historical evidence erased; no gate suppressed, skipped or xfailed; no mutation floor reduced.

## 9. Boundaries held

- **B5-I8 remains planning-only.** This correction authorizes no implementation, no resolver, no
  web view, no `oce/frontend` work.
- **B5-I9 remains `LOCKED`. Book 6 remains `UNAUTHORIZED`.** Post-Book-6 blind evaluation is not
  started.
- No cloud, provider, telemetry, broker or capital authority was used.

## 10. Same-agent disclosure

This correction was authored, implemented, validated and audited by the same agent:
**`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`**. No independent reviewer examined it. The
discriminating controls are the substitute for independence, and they are falsifiable: each
negative control must be refused by the law with a specific message.

## 11. Cost and authority accounting

Cost `$0`. No cloud resources, no provider calls, no telemetry, no broker or capital authority.
`capital.authority = none`. Freebuff untouched. No history rewrite: the correction is a new commit
on a new branch from merged `origin/main`.
