# Larger Lab Model Foundry (MF-B0 → MF-B4)

The first executable substrate of the Model Foundry: the laboratory in which
future model work can be scientifically trustworthy, reproducible, portable,
rights-aware, provider-neutral, contamination-aware — and incapable of quietly
becoming a second OCE.

```
MAKE COGNITION REPLACEABLE.
MAKE EVIDENCE, AUTHORITY, LINEAGE, AND SCIENTIFIC METHOD DURABLE.
```

## Doctrine

The Foundry's governing inequalities are enforced in code, not in prose:

```
MODEL OUTPUT != INSTITUTIONAL TRUTH      WEIGHTS != CANONICAL MEMORY
CAPABILITY   != AUTHORITY                ACCESS  != RIGHTS
AVAILABLE DATA != TRAINABLE DATA          BENCHMARK SCORE != CAPABILITY
PROVIDER OFFER != GUARANTEE               HOURLY PRICE != COST-TO-CLOSE
REGISTERED SOURCE != CLEAN SOURCE         HIDDEN EVAL != DEVELOPMENT DATA
NEGATIVE RESULT != FAILED PROJECT         UNKNOWN != FAVORABLE
```

## What exists

| Block | Module | What it does |
|---|---|---|
| MF-B0 | `foundry/constitution.py`, `foundry/boundary.py` | machine-legible constitution + 20-attack adversarial gate |
| MF-B1 | `foundry/resources.py`, `foundry/providers.py` | provider-neutral compute requests, cost-to-close placement, budget + operator hold |
| MF-B2 | `foundry/data.py` | source registry, rights dispositions, role machine, contamination graph, CEREBUS-family withholding |
| MF-B3 | `foundry/refinery.py` | deterministic dataset manifests, dedup, secret scan, point-in-time audit, source-level splits |
| MF-B4 | `foundry/evaluation.py` | protocol freeze, sealed access boundary, capability vectors, negative results + reopen |
| — | `foundry/cross_block.py` | cross-block scenarios F0–F11 |
| — | `foundry/oce_boundary.py` | One-OCE boundary: every temporary fixture declared with a retirement path |

## Run it

```bash
cd model-foundry
python -m pytest tests -q                 # authoritative suite
python -m foundry.cli report              # run every block, write receipts
python -m foundry.cli evidence            # regenerate the evidence package
```

Deterministic, offline, and free: no provider API is called, no session is
rented, no model is trained. Provider "offers" are hand-written fixture
observations in two different provider dialects, normalized into one contract.

## What is simulated (and says so)

* compute placement, launch, budget, and recovery are simulated;
* provider adapters are `OBSERVE`/`SIMULATE` fixtures, never live reads;
* the sealed-confirmation evaluation runs on fixtures;
* cross-runtime agreement in the CLI demo is **simulated**, so the capability
  conclusion there is `INCONCLUSIVE`, not `PASS`.

Every simulated element is declared with `noncanonical: true`,
`canonical_oce_target`, `replacement_condition`, and `retirement_evidence` —
see `fixtures/noncanonical_declarations.json` and
`../docs/model-foundry/integration-map.md`.

## What it may never be

The Foundry owns model-side domain semantics only. It owns no authority, no
identity, no institutional truth, no canonical memory, no production
deployment, no capital, and no constitutional amendment power. Those remain OCE
concerns, and `foundry.constitution.FOUNDRY_FORBIDDEN_AUTHORITIES` makes the
ceiling a test, not a promise.
