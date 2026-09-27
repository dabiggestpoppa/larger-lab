# OCE Golden System
## OPH, Cadence, and Sophontic Existing-Amendment Patchset v0.1

**Document ID:** OCE-PATCHSET-OPH-CADENCE-SOPHONTIC-001

**Status:** PROPOSED PLANNING PATCHSET — OPERATOR REVIEW REQUIRED

**Parents:** A-004, A-005, A-007, A-009, A-010

**Evidence parent:** `OCE_OPH_CADENCE_SOPHONTIC_ARCHITECTURE_IMPACT_REVIEW_v0.1.md`

**Build authorization:** NONE

---

## 0. Patch rule

The parent amendments remain intact historical documents. This patchset proposes only the clauses below.

If ratified, these clauses control future planning where they are more specific than the v1.0 parent text. They do not silently change the meaning of completed stress-suite receipts, create canonical schemas, or authorize implementation.

---

## 1. A-004 patch — cognition/evidence separation and handoff continuation

### 1.1 Context classification

Every cognition-facing context item shall be classified as one of:

- `WITNESSED_CANONICAL_REF` — reference to governed institutional state;
- `WITNESSED_NONCANONICAL` — observed but not promoted evidence;
- `DERIVED` — deterministic or model-derived result with lineage;
- `SIMULATED_PRIVATE` — counterfactual, imagined, planned, or internally generated state;
- `UNRESOLVED` — incompatible or insufficiently interpreted observation.

Context compaction may not erase these distinctions.

### 1.2 Private-imagination firewall

`SIMULATED_PRIVATE` content may influence planning but may not:

- appear as a witnessed event;
- satisfy an external-effect verification requirement;
- create a source record;
- close an EvidenceGap requiring observation;
- expand authority;
- become canonical without an explicit, provenance-preserving promotion event.

### 1.3 ResumeCapsule extension

Future `ResumeCapsule` planning shall add, where applicable:

```yaml
continuation_contract_ref: string | null
protected_observation_refs: []
ephemeral_state_disposition: PRESERVED | DISCARDED | UNAVAILABLE | NOT_REQUIRED
unverified_effect_refs: []
reconstruction_equivalence_required: boolean
```

The capsule proves resumability only. It does not by itself prove cognitive identity or behavioral equivalence.

### 1.4 Evidence-first loop clarification

The A-004 loop is refined conceptually to:

```text
OBSERVE
-> ORIENT
-> PLAN
-> SIMULATE PRIVATELY
-> ACT WITHIN AUTHORITY
-> READ CONSEQUENCE
-> VERIFY EFFECT INDEPENDENTLY
-> REDUCE EVIDENCE
-> LEARN
-> CHECKPOINT
```

Predicted, attempted, acknowledged, actual, and verified effects remain distinct.

### 1.5 Added acceptance tests

- deleting all private simulated state does not delete canonical truth;
- a counterfactual cannot satisfy a witnessed-evidence requirement;
- a fresh runtime can distinguish unverified effects from verified effects;
- a ResumeCapsule cannot claim continuation equivalence without its referenced test.

---

## 2. A-005 patch — public claims, promotion, and obstruction

### 2.1 Public-claim law

OCE shall distinguish:

```text
private interpretation
-> candidate public claim
-> governed evidence review
-> canonical promotion | unresolved | blocked | rejected
```

Agreement among agents may nominate a candidate public claim. Agreement alone cannot promote it.

### 2.2 Obstruction semantics

An obstruction is a valid institutional result when a requested transition lacks evidence, translation, authority, compatibility, or safe continuation.

An obstruction may be represented using existing governed objects and terminal states, including:

- `EvidenceGap`;
- `UnresolvedPatternRecord`;
- `DATA_BLOCKED`;
- `AUTHORITY_BLOCKED`;
- `OPERATOR_HOLD`;
- `EVIDENCE_UNCERTAIN`;
- a contract-specific policy block.

This patch does not require one universal `ObstructionRecord` schema.

### 2.3 Forced-coherence prohibition

No worker, integrator, Governor, or runtime may satisfy a completion requirement by averaging incompatible claims, erasing dissent, inventing translation, or selecting a winner for narrative neatness.

### 2.4 Added acceptance tests

- ten agreeing agents with one evidence lineage cannot canonize a claim;
- evidence removal converts the dependent claim to unresolved/blocked rather than leaving it promoted;
- incompatible typed claims remain explicitly obstructed until a valid translation or adjudication exists.

---

## 3. A-007 patch — cognitive continuation and dependency contracts

### 3.1 `CognitiveContinuationContract`

Every material substitution claim shall bind a versioned contract containing at minimum:

```yaml
CognitiveContinuationContract:
  subject_id: string
  role_or_capability_scope: string
  identity_boundary: string
  public_ports: []
  private_state_classes: []
  canonical_state_references: []
  protected_observations: []
  protected_forbidden_behaviors: []
  causal_record_schema: string
  repair_operators: []
  obstruction_conditions: []
  goal_provenance: string
  authority_ceiling: string
  action_verification_contract: string
  recovery_equivalence: string
  behavioral_signature_suite: string
  cognitive_dependency_profile_ref: string
```

This is a candidate logical contract. Schema ratification belongs to a later implementation plan.

### 3.2 Claim boundary

Passing a continuation contract proves only the declared operational envelope. It does not prove consciousness, metaphysical personal identity, universal task equivalence, or unrestricted runtime interchangeability.

### 3.3 Certification extension

Runtime certification shall eventually record:

- substitution classes supported;
- safe degraded behavior;
- private-state loss semantics;
- morphology/topology dependencies;
- behavioral-signature results;
- known non-equivalent replacements;
- maximum outage tolerance;
- recovery and rollback evidence.

### 3.4 Added acceptance tests

- a replacement that reconstructs state but violates a protected behavior is rejected;
- a replacement cannot inherit broader authority from the runtime it replaces;
- unknown equivalence yields `CONTINUATION_UNPROVEN` or governed hold;
- provider/model family substitution preserves canonical and authority fingerprints.

---

## 4. A-009 patch — causal attractors and bounded self-change

### 4.1 Attractor claim ladder

Institutional attractor claims shall distinguish:

```text
DESCRIPTIVE_RECURRENCE
-> PREDICTIVE_PATTERN
-> INTERVENTION_SUPPORTED_DYNAMICS
-> GOVERNED_PRACTICE_CANDIDATE
```

Repeated correlation, stylistic similarity, or geometric visualization cannot skip this ladder.

### 4.2 Required intervention evidence

Where practical, a promoted attractor intervention should show that:

- changing the proposed causal premise changes the predicted downstream behavior;
- irrelevant presentation changes do not erase the protected result;
- removal of required evidence creates uncertainty or obstruction;
- the effect reproduces across an appropriately independent path.

### 4.3 Self-change boundary

A cognitive organ may propose a change to its own method or organization. Promotion requires:

- explicit affected surface;
- protected-observation inventory;
- evaluation fixed outside the current candidate;
- continuation-impact analysis;
- bounded execution and rollback where possible;
- independent evidence proportional to consequence;
- operator approval where current authority requires it.

### 4.4 Source quarantine reaffirmed

Attractor success does not prove consciousness, truth, ethics, quantum cognition, nonlocal transmission, or teleodynamic cosmology.

---

## 5. A-010 patch — continuation-aware transformation

### 5.1 Transformation admissibility additions

Add three conditions to high-impact transformation review:

10. **Protected observations:** the candidate names the distinctions and records that must survive.
11. **Continuation impact:** the candidate identifies whether it is repair, migration, substitution, or identity-relevant reconstruction.
12. **Equivalence evidence:** required continuation tests and rollback triggers are frozen before promotion where practical.

### 5.2 Valid obstruction state

`CONTINUATION_UNPROVEN` is a valid transformation-window result. It means the candidate may be useful but the required identity/behavioral preservation claim has not been established.

It may lead to:

- more evidence collection;
- narrower scope;
- sandbox-only use;
- rollback;
- `NO_CHANGE`;
- `OPERATOR_HOLD`.

It may not be rewritten as PASS because the new system is more capable on unrelated benchmarks.

### 5.3 Reconsolidation extension

Reconsolidation shall consider:

- protected-observation preservation;
- behavioral-signature change;
- authority and evidence semantic preservation;
- private-state contamination;
- morphology/topology effects;
- recovery and rollback proof.

### 5.4 Added acceptance tests

- a more capable replacement fails promotion when it breaks a protected distinction;
- transformation can end `CONTINUATION_UNPROVEN` without forced rollback or promotion;
- the candidate cannot redefine its own behavioral signature during the window;
- rollback restores canonical and authority state, not merely service availability.

---

## 6. Explicit no-change decisions

No patch is required to:

- A-006 autonomous discovery and knowledge refinery;
- A-008 autonomous quant research institution;
- A-011 external economic environment and Opportunity Exchange.

Those programs consume the clarified evidence, continuation, and routing rules after ratification but do not own them.

No current block number, G-series gate, completed scenario receipt, or MF-B0 through MF-B4 build requirement changes under this patchset.

---

## 7. Operator decision

Proposed decision:

`RATIFY_OPH_CADENCE_SOPHONTIC_EXISTING_AMENDMENT_PATCHSET`

Ratification changes planning contracts only. It authorizes no schema migration, stress-suite implementation, cognitive training, runtime swap, self-modification, deployment, or external effect.
