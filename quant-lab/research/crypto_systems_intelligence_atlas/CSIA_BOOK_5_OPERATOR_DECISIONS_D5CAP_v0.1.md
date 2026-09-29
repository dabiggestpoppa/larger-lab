# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — OPERATOR DECISION PACKET (D5CAP NAMESPACE) v0.1

**Document ID:** CSIA-B5-OPDEC-001
**Version:** 0.1
**Status:** OPERATOR DECISION PACKET — NO DECISIONS MADE OR RECOMMENDED HERE
**Namespace note:** `D5CAP-*` IDs are a Book 5 planning namespace; they do not
collide with historical Book 0 `D5` (anti-drift cadence confirmation) and are
recorded per Constitution §5.4 when decided.

**Purpose:** only genuinely open structural questions are presented. Questions
answered by accepted doctrine or by plan-level ratification were deliberately
**not** opened: site-identity location (D7 recon default, plan §1.1),
flow-type enum closure and location-type list (ratify at plan review with
§9.3-style extension procedure), Book 6 seam rule (plan §8.2),
exit-boundary predicate (plan §7).

---

# D5CAP-1 — LIABILITY REPRESENTATION

**Question:** are liabilities a position subtype or separate typed economic
objects?

```text
OPTION A — LIABILITY-AS-POSITION-SUBTYPE
  Every liability is a CapitalPosition with position_kind = LIABILITY_SIDE.
  + one uniform query surface
  - forces phantom holders for holder-less obligations (bridge backing,
    LST redemption pools, insurance funds)

OPTION B — SEPARATE TYPED LIABILITY OBJECTS   [plan recommendation, §2.3]
  DebtLiability / ReserveLiability / RedemptionClaim as their own record
  family with role-links to positions.
  + represents holder-less obligations honestly; claims and liabilities
    remain joinable
  - two record families must stay consistent
```

**Impact:** position family shape, 5C/5D/5F record contracts, D7
double-counting invariant enforcement. Reversibility: medium (mechanical
migration between designs is possible but touches every liability-bearing
record).

```text
D5CAP-1 SELECTION: A | B (operator fills)
```

---

# D5CAP-2 — PRINCIPAL-LINEAGE REPRESENTATION

**Question:** typed lineage DAG records, or lineage field-chains on events?

```text
OPTION A — TYPED CapitalPrincipalLineage RECORDS (DAG)   [plan recommendation, §5]
  Lineage nodes reference claim/representation/position records; edges are
  transformation/flow events; conservation rules enforce one-principal
  accounting; cycles detectable as a contract property.
  + queryable, replayable, cycle-detection is structural
  - a new record family

OPTION B — LINEAGE FIELD-CHAINS ON EVENTS
  Each flow/transformation points to its predecessor lineage pointer.
  + fewer records
  - traversal, cycle detection, and dedup become consumer convention,
    not contract
```

**Impact:** double-counting enforcement strength (ALG-8), 5G collapse
methodology, stress rows 2/11–14 provability. Reversibility: hard if chosen
weakly (lineage is the backbone of every principal-domain computation).

```text
D5CAP-2 SELECTION: A | B (operator fills)
```

---

# D5CAP-3 — 5G OUTPUT SHAPE

**Question:** how does Bloc 5G structure its derived outputs?

```text
OPTION A — VERSIONED SNAPSHOTS + TOPOLOGY VIEWS   [plan recommendation, §22]
  CapitalFieldSnapshot (versioned, immutable compositions at valid time T)
  + CapitalFieldPath / CapitalPrincipalLineage view / CapitalTopologyView
  as projections over snapshots.
  + replay-first (P24); immutable snapshots; projections cheaply re-derivable
  - more artifact types

OPTION B — SINGLE VIEW MODEL
  One parameterized topology view computed on demand at any valid time.
  + minimal artifact surface
  - published-topology stability and citation (§29 reproducibility) weaker;
    on-demand recomputation cost at query time
```

**Impact:** 5G exit-gate evidence (replay at two historical valid times),
reproducibility posture, downstream Book 6/8 consumption. Reversibility: high.

```text
D5CAP-3 SELECTION: A | B (operator fills)
```

---

# Recording form (per §5.4)

When the operator decides, append to `CSIA_OPERATOR_DECISION_LOG.md`:

```text
DECISION LOG ENTRY {
  decision_id: D5CAP-n
  operator_selection: <verbatim option>
  source_packet: CSIA_BOOK_5_OPERATOR_DECISIONS_D5CAP_v0.1.md
  affected_bloc: <5C/5D/5F for D5CAP-1; cross-bloc for D5CAP-2; 5G for D5CAP-3>
  immediate_consequence: <plan §-refs>
  reversibility: <as stated above>
  effective_timestamp: <date>
  binding_commit_sha: <assigned at commit>
}
```

No decision is inferred from silence. Book 5 plan ratification may occur
independently of D5CAP selections, but a ratified plan with open D5CAP items
carries those items as binding-open until decided.
