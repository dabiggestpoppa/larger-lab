# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD SYNTHESIS MATRIX (BLOC 5G) v0.1

**Document ID:** CSIA-B5-5G-001
**Version:** 0.1
**Status:** PLANNING PROOF MATRIX — NOT RATIFIED
**Binding authority:** D7 decision (Option B) — "5G MAY DERIVE FROM CANONICAL CAPITAL FACTS. 5G MAY NOT CREATE CANONICAL CAPITAL FACTS." (Operator Decision Log, BOOK 5 DECISION (D7))
**Companion:** plan v0.1 §11/§22; stress matrix; pre-ratification review Q9.

---

# 1. Canonical write proof

```text
5G CANONICAL WRITE COUNT = 0 (by construction)

Basis:
1. 5G output shapes (CapitalFieldSnapshot / CapitalFieldPath /
   CapitalPrincipalLineage view / CapitalTopologyView) are composition
   artifacts whose every field is either (a) a pointer to a canonical
   5A–5F record, (b) a methodology/version identifier, (c) a temporal
   parameter, or (d) an UNKNOWN/INCOMPLETE propagation marker
   (plan §22 required-fields list).
2. No 5G shape contains a field whose value could originate an economic
   observation: no quantity field exists that is not copied from an
   input_record_ref with its methodology; no existence field exists that is
   not derived from referenced records.
3. 5G holds no Book 2 promotion path, no source registry, no evidence
   channel — there is no mechanism by which a 5G output could become a
   canonical claim (P1, B5-P25).
4. Outputs are marked DERIVED and are reproducible from inputs + methodology
   (§29 reproducibility); a derived artifact that can always be recomputed
   cannot silently accrete independent truth.
```

# 2. Derivation-completeness proof (every output traces to canonical inputs)

Per-output invariant set (planning contract; executable at implementation):

```text
INV-5G-1  input_record_refs is complete: every non-temporal, non-methodology
          field value traces to at least one referenced canonical record.
INV-5G-2  methodology_id + methodology_version present; recomputation with
          the same inputs + methodology yields the same output (replayable).
INV-5G-3  valid_time is an explicit parameter; historical replay at any
          valid time T reproduces the topology that canonical records
          as-of T support (P24).
INV-5G-4  unknown_propagation: any missing/unresolvable input renders
          dependent outputs INCOMPLETE with a gap list — never substituted,
          interpolated, or zero-filled (P2).
INV-5G-5  principal-collapse occurs only via an explicit collapse-methodology
          ID; without it, representations remain linked (never summed).
INV-5G-6  liability_treatment: liabilities enter as records; dropping or
          netting them without methodology is a contract violation (P16).
INV-5G-7  exposure_treatment: exposure-domain quantities never merge into
          principal-domain totals (ALG-5/9).
```

# 3. Attack tests (no hidden authority / no naive aggregation / no fabrication)

| Attack | Expected naive failure | Required 5G behavior | Planned defense |
|---|---|---|---|
| 5G output later treated as canonical source by a consumer | hidden authority accretes | consumers re-derive from 5A–5F; 5G output marked DERIVED with recomputation path | INV-5G-1/2; §4.4 support-layer pattern; P15 |
| Missing constituent record | gap silently filled (zero/nearest/interpolated) | INCOMPLETE + gap list; topology shows the hole | INV-5G-4; P2 |
| Multi-representation sum requested | naive total capital inflated | collapse only via collapse-methodology ID; linked otherwise | INV-5G-5; ALG-8 |
| Liability dropped for cleaner topology | net capital overstated | liabilities as records; netting only with methodology | INV-5G-6; ALG-6 |
| Exposure folded into capital | notional counted as principal | domain separation enforced | INV-5G-7; ALG-5/9 |
| Snapshot mutated after publication | history rewritten | snapshots immutable; corrections are new versions with supersession | §12 temporal doctrine; P24 |
| 5G flow-type invented ("EXIT_SIGNAL") | trading-signal leakage | vocabulary fixed to plan §3 enum + §7 exit doctrine; descriptive only | D7 exit semantics; P28; §5.3a |

# 4. Result

```text
5G_CANONICAL_WRITE_COUNT = 0
DERIVATION_INVARIANTS    = 7 (INV-5G-1..7 planned, executable later)
ATTACK_TESTS             = 7 (all defended by planned contracts)
HIDDEN_AUTHORITY_FOUND   = FALSE
NAIVE_AGGREGATION_PATH   = BLOCKED (INV-5G-5 + ALG-8)
MISSING_INPUT_FABRICATION = BLOCKED (INV-5G-4)
REPLAY_DEMONSTRATION     = required at exit gate (two historical valid times)
```

5G's exit gate (`PASS_CSIA_B5_CAPITAL_FIELD_V1`) requires: zero canonical
writes demonstrated, all seven invariants testable, missing-input case →
INCOMPLETE, and replay consistency at two historical valid times.
