# Larger Lab Model Foundry
## MF-B1 — Compute and Experiment Resource Layer Planning Dossier

**Document ID:** LL-MF-B1-PLAN-001  
**Version:** 1.0  
**Status:** DEEP PLANNING DRAFT — NO BUILD AUTHORIZATION  
**Dependency:** MF-B0 adversarial carry-forwards  
**Primary OCE destination:** B10 Resource Intelligence + B6 provider adapters + B8 scheduling  
**Purpose:** Make compute a replaceable, budgeted, evidence-producing capability rather than a provider dependency.

---

# 1. Block contract

MF-B1 defines how a scientific experiment asks for compute, how provider offers are normalized, how cost and reliability are measured, how checkpoints survive provider loss, and how resource use becomes part of the evidence record.

The block MUST NOT become a standalone cloud platform or generic OCE scheduler.

The invariant is:

> **The experiment defines the compute requirement; the marketplace does not define the experiment.**

---

# 2. Canonical domain contracts

## 2.1 `ComputeRequest`

Provider-neutral declaration:

- request_id;
- experiment/protocol ref;
- minimum VRAM;
- accelerator family/features;
- precision requirements;
- minimum system RAM;
- local/scratch storage;
- persistent checkpoint storage;
- expected wall-time envelope;
- interruption tolerance;
- preemption tolerance;
- framework/CUDA/JAX/PyTorch compatibility;
- data-boundary/security class;
- geographic constraints if material;
- network requirements;
- reproducibility class required;
- max experiment budget;
- max per-hour budget where useful;
- cleanup/termination semantics.

## 2.2 `ComputeOffer`

Normalized provider observation:

- provider + offer ID;
- accelerator identity;
- VRAM/RAM/storage;
- advertised price;
- storage/network/surcharge semantics;
- availability timestamp;
- region;
- trust/security class;
- preemption semantics;
- environment/container support;
- estimated setup overhead;
- historical reliability refs;
- offer provenance;
- freshness/expiry.

An offer is an observation, not a guarantee.

## 2.3 `PlacementDecision`

Records why a provider/instance was chosen:

- eligible offers;
- excluded offers and reasons;
- expected cost-to-close;
- estimated runtime;
- interruption risk;
- checkpoint/recovery plan;
- security/data-boundary fit;
- expected information value;
- selected offer;
- fallback path.

## 2.4 `ComputeReceipt`

Observed realized resource use:

- exact provider/instance;
- accelerator/runtime fingerprints;
- start/end;
- billed duration;
- storage/network charges;
- realized total cost;
- setup time;
- training/eval throughput;
- failures/preemptions;
- restarts;
- peak VRAM/RAM;
- checkpoint events;
- provider discrepancies;
- cleanup confirmation.

---

# 3. Resource selection doctrine

## 3.1 Optimize cost-to-close, not hourly rate

A cheaper GPU is not cheaper if it requires more wall time, fails more often, or cannot checkpoint safely.

Selection compares expected experiment completion cost and evidence yield.

## 3.2 Cheapest adequate compute first

Use the least expensive admissible resource capable of meeting the experiment's evidence requirement.

Possible ladder:

1. local CPU / no-GPU dry run;
2. notebook/small GPU smoke test;
3. commodity 24–32GB GPU;
4. 40–48GB accelerator;
5. 80GB+ accelerator;
6. multi-GPU / specialized hardware only when the protocol requires it.

The ladder is not rigid. Evidence requirements govern.

## 3.3 Provider neutrality

Initial adapters may cover:

- OctaSpace;
- RunPod Secure;
- RunPod Community where risk tolerance permits;
- Colab for interactive notebooks/smoke work;
- future marketplaces/providers.

No provider becomes required architecture.

---

# 4. Compute marketplace intelligence

The long-term routing surface belongs to OCE Resource Intelligence under the semantic capability:

`COMPUTE.GPU.RENT`

The Foundry may prototype provider normalization but MUST NOT own generic institutional provider authority.

Historical observations should learn workload-specific relationships:

- tokens/sec;
- training-step throughput;
- setup latency;
- failure/preemption rate;
- restart overhead;
- total cost;
- checkpoint portability;
- driver/framework compatibility.

Routing may later estimate expected cost-to-close by workload class.

No historical model may override hard experiment requirements.

---

# 5. Security and trust classes

Compute requests classify data and artifact sensitivity before remote placement.

Suggested classes:

- PUBLIC_RESEARCH;
- LICENSED_NONPUBLIC;
- PRIVATE_OPERATOR;
- SECRET_BEARING_PROHIBITED_REMOTE;
- SEALED_EVAL;

Raw secrets never enter provider metadata, prompts, receipts, or logs.

Hidden evaluation payloads should not be placed on untrusted workers unless the evaluation architecture explicitly permits it.

---

# 6. Checkpoint and provider-loss resilience

Every material training run defines:

- checkpoint cadence;
- local-vs-remote checkpoint storage;
- integrity hashes;
- resume semantics;
- provider-loss fallback;
- max recomputation budget;
- cleanup rules.

A provider disappearing must not destroy scientific lineage.

Checkpoint portability is measured, not assumed.

---

# 7. Reproducibility levels

MF-B1 introduces typed reproducibility:

- `ENVIRONMENT_REPRODUCIBLE` — exact environment/container/critical hardware semantics preserved where possible;
- `FUNCTIONALLY_REPRODUCIBLE` — materially equivalent result under compatible replacement stack;
- `STATISTICALLY_REPRODUCIBLE` — repeated run reproduces result distribution within frozen tolerance;
- `NONREPRODUCIBLE` — important conditions cannot be reconstructed.

Every run claims only the strongest class actually supported.

---

# 8. Budget doctrine

Budgets exist at multiple levels:

- experiment;
- day/week/month;
- provider;
- program phase.

Initial operator intent may use a small recurring experimental envelope, but no exact dollar amount becomes architectural law.

The scheduler must surface:

- projected cost;
- worst-case authorized cost;
- realized cost;
- cumulative budget use;
- marginal evidence gained.

No hidden auto-renewing instance or unattended storage cost.

---

# 9. Failure semantics

Compute failures are classified:

- PROVIDER_UNAVAILABLE;
- CAPACITY_UNAVAILABLE;
- ENVIRONMENT_MISMATCH;
- OOM;
- PREEMPTED;
- STORAGE_FAILURE;
- NETWORK_FAILURE;
- CHECKPOINT_FAILURE;
- FRAMEWORK_INCOMPATIBLE;
- BUDGET_BLOCKED;
- SECURITY_BLOCKED;
- UNKNOWN_RESOURCE_FAILURE.

Failures update provider/workload knowledge but do not automatically condemn a scientific hypothesis.

---

# 10. MF-B1 implementation increments

- **MF-B1-I0** freeze ComputeRequest/Offer/Receipt/Placement contracts;
- **I1** local dry-run + resource estimator;
- **I2** first provider adapter with read-only price/offer normalization;
- **I3** second independent provider adapter;
- **I4** cost-to-close comparison + historical receipt store;
- **I5** checkpoint portability drill;
- **I6** security/data-boundary routing tests;
- **I7** provider-loss / preemption recovery drill;
- **I8** budget/failure/cleanup adversarial tests;
- **I9** operator gate for limited paid smoke-test authorization.

---

# 11. Exit evidence

MF-B1 passes only if:

- one experiment can be expressed without naming a provider;
- at least two providers can be normalized without changing the experiment contract;
- routing explains exclusions and selection;
- realized costs reconcile to receipts;
- provider loss can be recovered or honestly classified;
- remote compute cannot gain durable OCE authority;
- a stopped run stops billing resources under the controlled path;
- scientific conclusions remain independent of provider identity.

Possible exits:

`PASS_MF_B1_RESOURCE_LAYER`
`REVISE_MF_B1`
`BLOCKED_PROVIDER_SEMANTICS`
`BLOCKED_SECURITY_BOUNDARY`
`OPERATOR_HOLD`

No training campaign is authorized by this plan alone.
