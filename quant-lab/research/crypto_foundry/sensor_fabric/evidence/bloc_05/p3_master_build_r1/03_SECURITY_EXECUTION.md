# 03 — Security execution (A01–A20)

Measured on this branch with

```
PYTHONPATH=src python3 -m pytest -p no:cacheprovider -q \
  tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py
```

**26 passed.** The file is `test_b5_p3_consumer_security.py`; every test carries
a positive control, a concrete adversarial input, the production entry point,
the expected decision, the forbidden outcome and an assertion naming the control
that fired.

## Why this file is not the old one

The withdrawn attempt shipped a security file whose attacks were named but not
executed: several "attacks" imported nothing, or asserted that a refusal had
happened without ever reaching the code that refuses. That file cannot be
salvaged by copying, so it was not. Each row below names the *mechanism*
asserted, not merely "REFUSE was returned".

## A01–A20 execution matrix

| ID | Attack | Concrete input | Fires | Observed | Forbidden outcome |
|---|---|---|---|---|---|
| A01 | callback injection | `rederive=…`, `callback=…` on the request | `ConsumerRequest` extra-forbid + `evaluate(self, request)` signature | `ValidationError`; no `Callable` parameter exists | forged verification accepted |
| A02 | `model_construct` forgery | a full `RecordVerification.model_construct(...)` handed in as `candidate`/`verdict` | request schema + boundary revalidation | `ValidationError` on the field; a forged *request* revalidates and refuses on its naive cutoff | forged verdict accepted |
| A03 | contradictory verification | verifier patched to return an empty `fields_verified` | `assert_trustworthy` | `REFUSE / VERIFICATION_FAILED` | acceptance with no verified field |
| A04 | manifest substitution | `claimed_manifest_bytes` = attacker root | digest compare, never adopted | `REFUSE / TRUSTED_CONTEXT_MISMATCH` (control: matching bytes reach the pipeline) | attacker root used as authority |
| A05 | capability minting | the most permissive `CustodyAuthorityDerivation` the type allows, offered on 4 field names | no intake + no `_issue`/`is_issued`/`_ISSUANCE_MARKER` identifiers (AST) | `ValidationError` ×4; production answer still `INTEGRATION_REQUIRED` | minted object authorizes |
| A06 | marker copying | `object.__setattr__(source, "_issued", …)` | authority re-derived per evaluation | decision unchanged, `custody_source_authorized is False` | copied marker authorizes |
| A07 | cross-record evidence reuse | `OTHER_RECORD_DOC_REF` with intact bytes | binding to this artifact's approved reference set | `REFUSE / EVIDENCE_NOT_BOUND_TO_ARTIFACT` | another record's evidence accepted |
| A08 | cross-cutoff reuse | cutoff past `valid_until` | cutoff bound into the identity, PIT before authority | `REFUSE`; source never consulted; the derivation refuses that cutoff with `UNAUTHORIZED` | stale authority reused |
| A09 | synthetic promotion | `SYNTHETIC_TEST_ONLY` sought in the enum and in every class constant | enum is exactly 3-valued; no `SYNTHETIC` string constant | construction of such a verdict raises; `SYNTHETIC_TEST_ONLY` absent | a synthetic basis accepted as production |
| A10 | forged trust scope | verifier patched to `FULL_RECORD_TRUST` | `assert_trustworthy`, then the scope inspection | `REFUSE`, reason in `{FORGED_TRUST_SCOPE, VERIFICATION_FAILED}`; both layers present in `policy.py` | scope widening accepted |
| A11 | empty unverified dimensions | `unverified_dimensions=()`, `downstream_trusted=True` | verdict type law + `assert_trustworthy` | construction raises; patched verifier refuses | authentication read out of an empty gap list |
| A12 | unverified required field | `required_fields=("price_canonical",)` | field allowlist | `REFUSE / FIELD_NOT_IN_ALLOWLIST` (control: `aggressor_side` passes) | unverified field accepted |
| A13 | evidence substitution | `FlipCustody(DOC_BYTES, TAMPERED_BYTES)` | `_rebind` | `REFUSE / EVIDENCE_BYTES_MISMATCH` — **both** TRADE and LIQUIDATION | swapped bytes accepted |
| A14 | digest-only custody | custody returns `None` for every reference | verifier custody check | `REFUSE`, `custody_status == UNVERIFIED` — **both** kinds | digest treated as bytes |
| A15 | forged replay eligibility | a duck-typed object claiming `ELIGIBLE` | boundary revalidation + `assess_replay_eligibility` | `REFUSE` (A15b: a blocked gate stops before authority, `source.seen == []`) | caller eligibility accepted |
| A16 | stale cached verdict | two consumptions, then the store loses the blob | re-derivation per call | read count doubles per call; third refuses | reuse of an earlier verdict |
| A17 | PIT-inadmissible authority | cutoff before `available_at`, source says `AUTHORIZED` | PIT before authority | `REFUSE / PIT_INADMISSIBLE`, `source.seen == []` — **both** kinds | custody rescues a bad instant |
| A18 | verifier exception | `RuntimeError`; then `SystemExit(3)` | crash boundary | `REFUSE / VERIFIER_CRASH`, detail ≤200 chars; `SystemExit` propagates | exception → success; swallowed exit |
| A19 | missing provenance | `authority_provenance=None` | verifier provenance law | `REFUSE / VERIFICATION_FAILED`, detail names `PROVENANCE_MISSING` | provenance-free record accepted |
| A20 | empty-manifest authorization | shipped manifest + a source double saying `AUTHORIZED` | integration-absent mapping | `INTEGRATION_REQUIRED`, `custody_source_authorized is False` — **both** kinds | empty manifest authorizing anything |

Every row's positive control is in the same test: the un-attacked path is
exercised first and must reach the pipeline. A policy that refused everything
fails at least 14 of these tests on the control alone.

## Mutation controls

| Mutation | Control it removes | Unmutated | Mutated (forbidden, and observed) |
|---|---|---|---|
| `_rebind` → `None` | evidence rebinding | `REFUSE / EVIDENCE_BYTES_MISMATCH` | `ACCEPT_FIELD_BINDING` — swapped bytes get through |
| `_adjudicate_replay` → always eligible | replay gate | `REFUSE / REPLAY_BLOCKED` | `ACCEPT_FIELD_BINDING` — a blocked record gets through |
| `_PIT_REFUSALS` → ∅ | PIT classification | `REFUSE / PIT_INADMISSIBLE` | still refuses, but reports the wrong reason — **classification** mutation, not a boundary mutation, and reported as such |
| `_INTEGRATION_ABSENT_REFUSALS` → ∅ | integration-absent mapping | `INTEGRATION_REQUIRED` | `REFUSE` — the integration state is misreported |

Two mutations show a removal that produces acceptance; two show a removal that
corrupts reporting. That distinction is deliberate: it is the difference between
a security boundary and a diagnostic, and both are tested for what they are.

## Threat classes — what is and is not claimed

* **T1 hostile data, T2 hostile caller** — attacked above; claimed.
* **T4 / threat class C arbitrary code in the same interpreter** — *not*
  claimed, and documented in the test module docstring as X01–X06: X01 construct
  the policy over your own manifest, X02 monkeypatch the verifier, X03 replace
  the custody provider, X04 resource exhaustion, X05 host/dependency compromise,
  X06 how a future operator authority is granted.
  `test_scope_documentation_names_x01_to_x06` fails if that text disappears.

Several tests above monkeypatch the verifier. That is not a T4 defence claim: it
is the consumer refusing to trust what it is handed even when the thing handing
it over is compromised. The distinction matters — an in-process object cannot
withstand code running with the application's own privileges, and this packet
does not pretend otherwise.

## Adjacent regressions run

```
consumer suites (5 files)                     139 passed
governance set (10 files)                     344 passed
canonical collection                          4930 nodes, digest 716a0579…6905
```
