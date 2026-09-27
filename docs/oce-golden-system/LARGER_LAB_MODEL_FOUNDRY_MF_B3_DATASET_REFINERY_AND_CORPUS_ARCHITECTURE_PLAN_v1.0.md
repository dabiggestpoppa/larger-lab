# Larger Lab Model Foundry
## MF-B3 — Dataset Refinery and Corpus Architecture Planning Dossier

**Document ID:** LL-MF-B3-PLAN-001  
**Version:** 1.0  
**Status:** DEEP PLANNING DRAFT — NO BUILD AUTHORIZATION  
**Dependency:** MF-B2 Data Constitution  
**Purpose:** Convert governed sources into reproducible training/dev corpora without losing rights, provenance, contamination, transformation, or partition semantics.

---

# 1. Block contract

MF-B3 owns the domain-specific transformation from governed sources to immutable dataset manifests.

It does not own generic OCE artifact/evidence infrastructure.

The invariant is:

> **Every token entering a training run must have a reconstructable lineage back to an allowed source role and a deterministic or explicitly versioned transformation path.**

---

# 2. Refinery stages

Canonical pipeline:

```text
SourceRecord
  ↓
Acquisition / immutable capture
  ↓
Parsing
  ↓
Normalization
  ↓
Structure extraction
  ↓
Quality + integrity checks
  ↓
Dedupe / contamination checks
  ↓
Domain/type classification
  ↓
Filtering
  ↓
Example/sequence construction
  ↓
Partition assignment
  ↓
DatasetManifest
```

Each stage emits versioned transformation metadata.

---

# 3. Parser architecture

Parsers are capability implementations, not truth authorities.

For each source class, record:

- parser identity/version;
- input schema/type;
- output schema;
- extraction losses;
- encoding handling;
- table/code/math preservation;
- error/quarantine semantics;
- deterministic/non-deterministic behavior;
- known unsupported constructs.

OCR should be treated as noisy transformation and tagged accordingly.

---

# 4. Normalization doctrine

Normalization may fix representation; it must not silently alter meaning.

Examples:

- Unicode normalization;
- whitespace/layout cleanup;
- code fencing;
- equation preservation;
- metadata separation;
- document section boundaries;
- timestamp/unit normalization for structured data.

Every lossy normalization must be declared.

---

# 5. Dedupe architecture

Dedupe runs at multiple levels:

- exact bytes;
- normalized text;
- document/chunk hashes;
- near-duplicate similarity;
- code clone similarity;
- benchmark answer overlap;
- derived/synthetic ancestry.

Dedupe does not erase provenance. It creates canonical identity + aliases/relationships.

The goal is not maximum compression. The goal is to prevent accidental over-weighting, leakage, and false source diversity.

---

# 6. Corpus architecture

The Foundry uses a layered corpus rather than one undifferentiated soup.

Initial domains:

- foundational technical language;
- Python / code;
- algorithms / software engineering;
- mathematics;
- probability / statistics;
- ML / AI;
- science / signal processing;
- time series / econometrics;
- market microstructure / quantitative finance;
- research methodology;
- tool-use/task traces;
- raw-data reasoning;
- OCE-specific procedural examples only where appropriate.

Exact mixture weights are experiment variables, not constitutional constants.

---

# 7. Example-type taxonomy

The refinery distinguishes at minimum:

- RAW_TEXT;
- CODE;
- CODE_WITH_TESTS;
- MATH_DERIVATION;
- QA;
- INSTRUCTION_RESPONSE;
- TOOL_TRACE;
- EXPERIMENT_TRACE;
- DATA_ANALYSIS_TASK;
- NEGATIVE_EXAMPLE;
- ABSTENTION_EXAMPLE;
- SYNTHETIC;
- STRUCTURED_MARKET_DATA_TASK.

This enables later mixture experiments without re-parsing all sources.

---

# 8. Sequence construction

Sequence builders are versioned.

They define:

- document packing policy;
- boundary tokens;
- truncation rules;
- code/math preservation;
- max sequence length;
- multi-document mixing;
- causal masking assumptions;
- instruction formatting;
- tool-call formatting;
- weighting/repetition policy.

A sequence builder cannot move an eval/retrieval-only source into training.

---

# 9. Partition integrity

Partition assignment happens after source-role checks and before training.

Requirements:

- immutable partition manifest;
- group-aware splitting where related records could leak;
- time-aware splitting for market/time-series tasks where relevant;
- source-family-aware splitting;
- synthetic-parent-aware splitting;
- benchmark-family exclusions;
- hidden eval physically/logically separate from train artifacts.

Row-level random splitting is prohibited when it would create dependency leakage.

---

# 10. Market-data corpus special rules

Raw quant discovery data requires additional semantics:

- instrument identity;
- provider identity;
- timezone/session rules;
- revisions/corrections;
- point-in-time availability;
- corporate actions where relevant;
- missingness;
- precision;
- resampling method;
- future leakage checks;
- train/eval temporal boundaries.

A market dataset without point-in-time/time semantics cannot support strong predictive research claims.

---

# 11. Code corpus special rules

Code sources record:

- repository/version/license;
- language;
- dependency context;
- test presence;
- build/execution status where measured;
- generated/vendor code classification;
- vulnerability/security concerns;
- benchmark-solution overlap.

Executable validation is stronger than style-based quality inference.

---

# 12. Dataset fingerprints

Every immutable dataset version has:

- manifest digest;
- source-set digest;
- transformation graph/version;
- record count;
- token count;
- partition counts;
- dedupe statistics;
- contamination relationships;
- rights summary;
- known exclusions/limitations.

A changed transformation or source set creates a new dataset version.

---

# 13. Quality and inspection sampling

Automated filters must be audited with sampled human/independent review.

Metrics include:

- parser failure rate;
- malformed fraction;
- duplicate fraction;
- language/domain misclassification;
- code syntax/test failures;
- math corruption;
- synthetic fraction;
- source concentration;
- train/eval overlap;
- rights/unknown fraction.

No filter promotes itself based solely on its own score.

---

# 14. Curriculum and weighting

Curriculum/mixture weights are `TrainingRecipe` inputs, not permanent dataset properties.

This permits experiments such as:

- code-heavy vs balanced;
- math-first vs mixed;
- finance-heavy vs general scientific;
- raw-data-heavy later-stage adaptation.

The base corpus remains reproducible independent of one curriculum.

---

# 15. Failure semantics

Refinery failures include:

- SOURCE_UNRESOLVED;
- RIGHTS_BLOCKED;
- PARSE_FAILED;
- LOSSY_TRANSFORM_UNACCEPTABLE;
- DUPLICATE_COLLAPSED;
- CONTAMINATION_BLOCKED;
- PARTITION_LEAKAGE;
- SCHEMA_INVALID;
- PIT_INVALID;
- SYNTHETIC_LINEAGE_MISSING;
- MANIFEST_MISMATCH;
- UNKNOWN_DATA_FAILURE.

Failures become quarantine/NegativeKnowledge records rather than silent drops where material.

---

# 16. MF-B3 implementation increments

- **MF-B3-I0** freeze transformation graph and DatasetManifest schema;
- **I1** acquisition + immutable source capture;
- **I2** parser interfaces + fixtures;
- **I3** normalization + structural extraction;
- **I4** exact/near dedupe + alias lineage;
- **I5** domain/example classification;
- **I6** sequence builders + partitioning;
- **I7** market/code special validators;
- **I8** contamination/rights/partition adversarial suite;
- **I9** freeze first candidate training/dev dataset manifests.

---

# 17. Exit gate

MF-B3 passes only if:

- a dataset can be rebuilt from source + transformation manifests;
- duplicate aliases do not masquerade as independent sources;
- evaluation material cannot enter train partitions through sequence builders;
- market temporal leakage is detected;
- synthetic lineage survives all transforms;
- code/math corruption is measured;
- data rights follow the transformed artifact;
- exact corpus/version used by a run is fingerprinted.

Possible exits:

`PASS_MF_B3_DATASET_REFINERY`
`REVISE_MF_B3`
`BLOCKED_DATA_LINEAGE`
`BLOCKED_PARTITION_INTEGRITY`
`OPERATOR_HOLD`

No material model training is authorized until MF-B4 also reaches its planning gate.
