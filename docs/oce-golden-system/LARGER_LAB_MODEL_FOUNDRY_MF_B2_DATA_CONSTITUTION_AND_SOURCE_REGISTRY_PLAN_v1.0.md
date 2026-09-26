# Larger Lab Model Foundry
## MF-B2 — Data Constitution and Source Registry Planning Dossier

**Document ID:** LL-MF-B2-PLAN-001  
**Version:** 1.0  
**Status:** DEEP PLANNING DRAFT — NO BUILD AUTHORIZATION  
**Dependency:** MF-B0 constitutional boundary; MF-B1 resource contract  
**Purpose:** Define what data may enter training, evaluation, retrieval, blind discovery, quarantine, or exclusion — with provenance, rights, contamination, and epistemic role explicit before model exposure.

---

# 1. Block contract

MF-B2 makes data governance scientific infrastructure.

The primary invariant is:

> **A source is not training data merely because we can download it.**

Every source receives identity, provenance, rights basis, epistemic role, contamination relationships, and disposition before it enters a derived corpus.

---

# 2. Source roles

A `SourceRecord` may authorize one or more explicitly controlled roles, but role transitions require a new decision/version.

Primary roles:

- TRAIN_CPT;
- TRAIN_SFT;
- TRAIN_PREFERENCE;
- DEV;
- PUBLIC_EVAL;
- HIDDEN_EVAL;
- SEALED_CONFIRMATION;
- BLIND_DISCOVERY;
- RETRIEVAL_ONLY;
- QUARANTINED;
- EXCLUDED.

No default role is TRAIN.

---

# 3. Rights / licensing basis

Every trainable source requires a rights basis.

Suggested values:

- `EXPLICIT_OPEN_LICENSE`;
- `PUBLIC_DOMAIN`;
- `OPERATOR_OWNED`;
- `PROVIDER_TERMS_ALLOW`;
- `DIRECT_PERMISSION`;
- `RIGHTS_REVIEW_REQUIRED`;
- `UNKNOWN`;
- `PROHIBITED`.

`UNKNOWN` and `RIGHTS_REVIEW_REQUIRED` fail away from model training until resolved.

A rights decision records:

- source/version;
- evidence/locator supporting decision;
- applicable jurisdiction/terms where relevant;
- allowed transformations;
- redistribution limits;
- expiration/change conditions;
- reviewer/decision provenance.

Rights metadata is evidence-backed, not self-declared.

---

# 4. Provenance graph

Each source should support lineage such as:

```text
ORIGINAL SOURCE
    ↓
mirror / archive / export
    ↓
parser
    ↓
normalized records
    ↓
filtered corpus
    ↓
training dataset
    ↓
training run
    ↓
checkpoint
```

Derived data never erases the original source lineage.

Unknown origin is a material limitation.

---

# 5. Contamination model

Contamination is typed, not binary.

Suggested classes:

- EXACT_DUPLICATE;
- NEAR_DUPLICATE;
- PARAPHRASE_OR_DERIVATIVE;
- SAME_ANSWER_TEMPLATE;
- BENCHMARK_DISCUSSION;
- SOLUTION_EXPOSURE;
- SOURCE_FAMILY_OVERLAP;
- MODEL_GENERATED_FROM_EXPOSED_MODEL;
- RETRIEVAL_EXPOSURE;
- CONTEXT_EXPOSURE;
- UNKNOWN_ANCESTRY.

A model may be usable despite contamination, but the claim strength must reflect it.

---

# 6. Train / Eval / Retrieval separation

The Foundry must prevent silent role collapse.

## 6.1 Training

Training sources may teach skill, representation, or domain language.

## 6.2 Evaluation

Evaluation material exists to measure capability and must not become tuning material without retiring/reversioning the benchmark.

## 6.3 Retrieval

Retrieval-only material may support current work without entering weights.

This is the preferred role for mutable doctrine, current policy, changing project state, and many copyrighted/private reference works.

---

# 7. CEREBUS withholding policy

CEREBUS source material and close derivatives are withheld from early training pathways intended to support blind reconstruction.

The policy must cover:

- direct manuals;
- extracted text;
- summaries;
- derived training examples;
- terminology-heavy prompts;
- solution labels;
- explicit rule tables;
- retrieval exposure;
- experimenter-context exposure where relevant.

Pretrained base-model ancestry is recorded as UNKNOWN unless independently established.

Therefore base-model experiments can demonstrate `BLIND_TASK_PERFORMANCE`, not necessarily controlled independent rediscovery.

---

# 8. Domain/source taxonomy

Initial taxonomy should support at least:

- mathematics;
- probability/statistics;
- algorithms/data structures;
- software engineering;
- Python;
- systems/programming;
- ML/AI;
- scientific reasoning;
- experimental design;
- signal processing;
- time series;
- econometrics;
- market microstructure;
- quantitative finance;
- public market data;
- documentation/tool use;
- OCE procedural behavior;
- synthetic/generated data.

Taxonomy is descriptive; it does not determine quality by itself.

---

# 9. Data quality vector

Never collapse data quality into one universal scalar.

Candidate dimensions:

- source reliability;
- rights clarity;
- correctness;
- completeness;
- dedupe risk;
- contamination risk;
- domain relevance;
- representativeness;
- temporal relevance;
- formatting/parsing integrity;
- code executability where applicable;
- answer verifiability;
- diversity;
- synthetic fraction.

Disposition is a governed rule over the vector, not “quality score > X.”

---

# 10. Synthetic data constitution

Synthetic data is permitted only with explicit lineage.

Every generated record/set binds:

- generator model/runtime;
- generator checkpoint;
- prompt/procedure version;
- source materials used;
- evaluator/filter path;
- generation date;
- contamination relationships;
- whether generator had access to hidden/benchmark material.

Synthetic descendants never lose the parent lineage.

A synthetic corpus cannot become “external confirmation.”

---

# 11. Private / copyrighted material boundary

Private/operator-provided or copyrighted materials may be valuable for retrieval, study, evaluation design, or operator-authorized internal transformations.

But the training disposition must be explicitly determined rather than inferred from possession.

Where training rights are unclear:

`RETRIEVAL_ONLY` or `QUARANTINED` is the default safe state.

The Model Foundry does not invent legal permission.

---

# 12. Source mutation / version drift

URLs and hosted datasets can change.

The Source Registry should preserve where possible:

- immutable digest;
- commit/release/version;
- retrieval timestamp;
- original locator;
- mirrored artifact where rights permit;
- observed license/terms version;
- schema/profile.

A changed source becomes a new version, not silent replacement.

---

# 13. Hidden evaluation source firewall

Hidden/confirmation material requires stronger access controls.

Builder agents may receive task execution interfaces without raw answer keys.

The system records:

- who accessed hidden payloads;
- when;
- purpose;
- model/runtime exposure;
- whether contamination invalidates future use.

A hidden benchmark exposed to the training path is compromised, not “still mostly hidden.”

---

# 14. MF-B2 implementation increments

- **MF-B2-I0** freeze source/rights/role/contamination enums and contracts;
- **I1** SourceRecord registry + immutable fingerprints;
- **I2** rights-basis workflow and fail-closed trainability decision;
- **I3** role assignment + transition history;
- **I4** dedupe/contamination relationship engine v1;
- **I5** CEREBUS withholding/source-family map;
- **I6** synthetic lineage registry;
- **I7** hidden-eval access/firewall simulation;
- **I8** source drift/versioning/revocation tests;
- **I9** operator gate for corpus-building authorization.

---

# 15. Adversarial tests

MF-B2 must reject or correctly classify:

- unknown-license book marked trainable;
- mirror copy with missing original provenance;
- benchmark solutions hidden inside code comments;
- paraphrased eval answers entering SFT;
- synthetic examples generated by a model exposed to the holdout;
- CEREBUS-derived terminology disguised as generic market research;
- retrieval-only source silently added to training;
- source whose license changes;
- duplicate data under changed filenames;
- private data exported to remote compute without authorization;
- model-generated source claiming external independence.

---

# 16. Exit gate

MF-B2 passes only when:

- every corpus-bound source has a resolvable SourceRecord;
- every trainable source has an evidence-backed rights basis;
- Train/Eval/Retrieval transitions are explicit and versioned;
- contamination relationships can invalidate or downgrade claims;
- CEREBUS withholding is operationally expressible;
- synthetic lineage survives derivation;
- hidden evaluation access is auditable;
- unknown provenance/rights fail closed.

Possible exits:

`PASS_MF_B2_DATA_CONSTITUTION`
`REVISE_MF_B2`
`BLOCKED_RIGHTS_POLICY`
`BLOCKED_CONTAMINATION_MODEL`
`OPERATOR_HOLD`

No material training is authorized merely by passing MF-B2.
