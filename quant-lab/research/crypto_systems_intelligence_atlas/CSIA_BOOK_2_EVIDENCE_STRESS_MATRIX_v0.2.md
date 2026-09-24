# CSIA Book 2 — Evidence Stress Matrix — v0.2

Status: RATIFICATION CANDIDATE
Companion to: Book 2 plan v0.2 and Source Authority Matrix v0.2
Supersedes for planning: `CSIA_BOOK_2_EVIDENCE_STRESS_MATRIX_v0.1.md`
Preserved unchanged: v0.1 and all fifteen original row descriptions

## 1. Purpose and controlled-edition rule

This matrix walks real-world failure shapes through:

```text
SOURCE → RAW EVIDENCE → CLAIM → CLAIM STATE → GRAPH EFFECT
```

The complete row narratives in v0.1 remain normative. This v0.2 edition
(a) corrects the v0.1 summary arithmetic, (b) records the disposition of
row 15 after operator decision D2-5, and (c) adds row 16 to exercise the
mechanical `CREATE_INFERRED` path. No v0.1 row is silently deleted or
rewritten.

## 2. Recomputed v0.1 row ledger

Every one of the fifteen original row-level classifications was recounted:

| Row | Stress | v0.1 classification | v0.2 disposition |
|---:|---|---|---|
| 1 | Ethereum specification revised | REQUIRED_EXTENSION | unchanged |
| 2 | Old XRPL docs remain indexed | REQUIRED_EXTENSION | unchanged |
| 3 | Governance passed; execution later | REQUIRED_EXTENSION | unchanged |
| 4 | Integration announced; deployment unverified | INFORMATION_GAP | unchanged |
| 5 | Bridge route closes | REQUIRED_EXTENSION | unchanged |
| 6 | USDC bridged-only to native issuance | REQUIRED_EXTENSION | unchanged |
| 7 | Solana RPC providers disagree | REQUIRED_EXTENSION | unchanged |
| 8 | ICP documentation renames a concept | DEFERABLE_EXTENSION | unchanged |
| 9 | Archived repository vs active-development narrative | INFORMATION_GAP | unchanged |
| 10 | Aggregator merges same-ticker assets | REQUIRED_EXTENSION | unchanged |
| 11 | Official website disappears | REQUIRED_EXTENSION | unchanged |
| 12 | API silently changes schema | REQUIRED_EXTENSION | unchanged |
| 13 | Source corrects historical data | REQUIRED_EXTENSION | unchanged |
| 14 | Explorer/indexer lags chain | INFORMATION_GAP | unchanged |
| 15 | Docs and chain disagree on activation time | OPERATOR_DECISION | REQUIRED_EXTENSION after D2-5 |

The original fifteen-row classification totals are therefore:

```text
STRUCTURAL_FAILURE      0
REQUIRED_EXTENSION      10  (1,2,3,5,6,7,10,11,12,13)
DEFERABLE_EXTENSION     1   (8)
INFORMATION_GAP         3   (4,9,14)
OPERATOR_DECISION       1   (15)
TOTAL                   15
```

### Explicit correction of the v0.1 error

The preserved v0.1 summary says `REQUIRED_EXTENSION = 9` while listing ten
rows classified REQUIRED_EXTENSION. This is a summary arithmetic error, not a
row-classification error. The corrected value is 10. The error remains visible
in v0.1 and is not backdated or hidden.

## 3. Row 15 replacement — documentation versus deployed activation

### Inputs and preserved lines

- **E1 / documentation line:** first-party documentation says activation at T1.
- **E2 / deployed-state line:** RPC/verified chain state says activation at T2.
- Both captures, content hashes, source identities, retrieval times, and
  claim identities remain independently queryable.

### Claim-family resolution

The immediate factual proposition is “activation occurred at time X” in the
DEPLOYMENT / ACTIVATION claim family. Under A-1 and A-4, deployed state pins
the factual activation boundary at T2 for that valid-time window. The
documentation claim remains evidence of what the specification/documentation
said; it is corrected or superseded through lineage, never erased.

This resolution does not conclude that the documentation source is globally
untrustworthy. That source may remain authoritative for SPECIFICATION,
GOVERNANCE INTENT, or HISTORICAL DOCUMENTATION.

### Required D2-5 outputs

1. Preserve E1 and E2 as separate evidence lines.
2. Resolve the graph fact by `SOURCE × CLAIM_FAMILY × VALID_TIME`.
3. Create a discrepancy meta-claim that references both factual claims and
   both evidence lines.
4. Append discrepancy history for the documentation source and
   DEPLOYMENT / ACTIVATION family.
5. Do not globally demote the source for this single event.
6. Permit a family-scoped downgrade only after repeated demonstrated,
   evidence-backed unreliability for that same family.
7. Version the downgrade by valid time and transaction time.
8. Preserve reversibility through successor authority decisions.
9. Require operator review for a persistent tier change.
10. Forbid an opaque global source trust score.

### v0.2 classification

```text
Classification: REQUIRED_EXTENSION
Reason: the family-scoped discrepancy history, versioned authority decision,
reversibility, and operator-review mechanism must be implemented later.
```

The original v0.1 OPERATOR_DECISION is closed by D2-5; its v0.1 label remains
preserved in the ledger above.

## 4. Row 16 — oracle dependency availability inference

### Setup

- **Parent P1 (OBSERVED):** “Protocol P declares a dependency on oracle O.”
  It is backed by immutable protocol documentation evidence E1 and its
  deployment/configuration observation E2.
- **Parent P2 (OBSERVED):** “Oracle O stopped serving chain C at time T.”
  It is backed by oracle status/response evidence E3 and independent
  chain-side observation E4.
- P1 and P2 are independent claims with separate claim IDs, states,
  propositions, and valid-time windows.

### Mandatory methodology M

M is a versioned, explicit rule:

```text
Given a protocol dependency claim and a service-availability claim for the
same protocol, dependency, and overlapping valid-time window, derive a
qualified dependency-availability risk proposition. The output states only
that degradation MAY be present; it does not assert usage, exploitability,
severity, or causality beyond the observed evidence.
```

M includes the dependency identity, chain identity, time window, service-
availability proposition, qualification “may,” and the rule version. Any
unbounded parameter is explicit and may be UNKNOWN; it is not fabricated.

### Required creation result

`CREATE_INFERRED(P1, P2, M)` must:

1. Validate I-1..I-10.
2. Allocate a **new** claim ID, I1.
3. Create the proposition “Protocol P may have degraded dependency
   availability on chain C during [derived or UNKNOWN] window.”
4. Record P1 and P2 as parent claims and retain their OBSERVED states.
5. Bind M and the explicit valid-time derivation.
6. Expose a transitive evidence lineage I1 → P1/P2 → E1..E4 → raw snapshots
   and content hashes.
7. Persist I1 in state INFERRED without changing, re-labeling, or deleting
   P1 or P2.
8. Prevent any INFERRED → OBSERVED transition.

### Challenge, corroboration, and supersession paths

- Contrary status/chain evidence may move I1 INFERRED → CONTESTED or REJECTED.
- An independent derivation with the same proposition and methodology may
  corroborate I1 to CORROBORATED when independence requirements are met.
- Direct observation of actual degradation creates a separate OBSERVED claim
  O1. O1 may corroborate, contest, or supersede I1 according to proposition
  and valid-time semantics; O1 never relabels I1.
- Missing parents, missing methodology, or a lineage that does not terminate
  in raw evidence causes atomic creation failure and no partial claim.

### v0.2 classification

```text
Classification: REQUIRED_EXTENSION
Reason: the new-claim creation action, parent-state immutability, mandatory
methodology, transitive lineage validation, and direct-vs-inferred claim
comparison are planned mechanisms that require later authorized implementation.
```

## 5. v0.2 expanded totals

After closing the operator decision and adding the INFERRED case:

```text
STRUCTURAL_FAILURE      0   (no rows)
REQUIRED_EXTENSION      12  (rows 1,2,3,5,6,7,10,11,12,13,15,16)
DEFERABLE_EXTENSION     1   (row 8)
INFORMATION_GAP         3   (rows 4,9,14)
OPERATOR_DECISION       0   (row 15 closed by D2-5)
TOTAL                   16
CHECKSUM                0+12+1+3+0 = 16
```

## 6. Structural conclusion

No scenario requires a change to the Book 2 epistemics architecture after the
v0.2 INFERRED repair:

- INFERRED is mechanically reachable through `CREATE_INFERRED`.
- Narrative evidence still cannot take a structural shortcut.
- Structural conflict still resolves by claim family, not recency or count.
- Staleness remains policy-scoped, not globally timed.
- Every promoted graph fact remains traceable to raw evidence through
  explicit claim and inference lineage.
- Research Mesh, QCAE, and OCE still have no direct promotion authority.

```text
STRUCTURAL_FAILURE = 0
BOOK_2_STRESS_MATRIX_DISPOSITION = ACCEPTED_CANDIDATE
BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
```

## 7. v0.1 → v0.2 changelog

- Recomputed all fifteen v0.1 rows and corrected REQUIRED_EXTENSION from 9
  to 10; the original error remains disclosed.
- Closed row 15 through D2-5 and changed its v0.2 disposition to
  REQUIRED_EXTENSION because the family-scoped authority mechanism now
  requires a planned extension.
- Added row 16 to prove INFERRED is a new lineage-explicit claim rather than
  a mutation of observed parents.
- Added direct-observation, contrary-evidence, corroboration, and supersession
  paths without allowing INFERRED → OBSERVED.
- Expanded the matrix to sixteen scenarios with a checksum of 16 and zero
  structural failures.
