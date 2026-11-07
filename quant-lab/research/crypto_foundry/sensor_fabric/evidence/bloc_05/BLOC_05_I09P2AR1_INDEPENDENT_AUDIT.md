# SENSOR-B5-I09P2aR1 — INDEPENDENT AUTHORITY AUDIT

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Audit HEAD:** `6b112f196ef086550bd9e4b107bc23bfabbf0f0a` (= remote)
**Implementation parent:** `89c693945706edbf15dde3fccd389653e05adef2`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Entering status:** `B5-I09P2A_IMPLEMENTATION_COMPLETE`, not operator-ratified
**Nature:** independent audit + governed adjudication. No production or test byte changed; the only durable output is this record and ledger §191.

**VERDICT: `I09P2A_RATIFICATION_HOLD`.**

The fail-closed mechanical layer is validated. The trust boundary it depends on is not enforced by any production integration, and record-level provenance is data rather than proof. Under directive §11 that is a HOLD, not a bounded acceptance.

---

## A — Custody

| Item | Observed |
|---|---|
| local HEAD | `6b112f196ef086550bd9e4b107bc23bfabbf0f0a` |
| remote branch tip | `6b112f196ef086550bd9e4b107bc23bfabbf0f0a` (equal) |
| tracked tree | clean |
| untracked | the three preserved scratch paths only (`.bu_tmp/`, `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`, `b5_i03_redteam_results.json`) |
| commits above I09P1 | exactly two (`89c6939457` implementation, `6b112f196e` artifact republish) |
| frozen plan | `agent/crypto-sensor-fabric-plan` resolves to `4bb677f9e`; no planning document appears in the commit range |
| I09P1 records | `BLOC_05_I09P1_REGISTRY_TRUST_BOUNDARY.md`, `…_ADVERSARIAL_TEST_CONTRACT.md`, ledger §189 reachable |
| I09P2a record | `BLOC_05_I09P2A_IMPLEMENTATION_EVIDENCE.md`, ledger §190 reachable |
| B5-I09a / I10 | acceptance records reachable and unedited |
| I11 | hold chain reachable (`I11R1`, `I11R2`, `I11F1`) and unedited |

No reset, rebase, amend, squash or force-push.

## B — Frozen authority reconstruction

`normalization/common/semantic_registry.py` is text-in only and unchanged since the I09 checkpoint; `…/methodologies.py` likewise; `…/sensors/side_maps.py` holds the single frozen Binance polarity rule. `normalization/authority/__init__.py` (496 lines) is the only new authority surface, and `config/crypto_sensor_fabric/provider_semantics/approval_manifest.json` is its trust root.

Chain as built, transition by transition:

| Transition | Trusted | Checked | Merely asserted |
|---|---|---|---|
| registry bytes → loader | nothing | SHA-256 against the **manifest's** `sha256` | that the bytes describe a real venue |
| manifest → loader | the manifest's provenance | JSON parse, duplicate keys, schema, types, duplicate approval ids | that a human reviewed it |
| digest → approval entry | the entry's digest | exact match; revocation; validity window vs caller-supplied instant; `registry_schema_version` | that `approved_at`/`valid_until` are truthful |
| row → methodology | the methodology registry | `require(methodology_id, version)` + `allowed_methodologies` | that the methodology models the venue |
| row → evidence | the manifest's binding | `evidence[provider][field]` membership, pending token refused | that the cited document exists or says what is claimed |
| row → native field / transformation / assumptions | the manifest | declared-field membership, transformation equality where named, assumption resolution | that the manifest's claims are correct |
| authority → consumer | the loader seal (in-process) | `isinstance` + `attests(row)` | that the consumer holds a genuinely issued authority |
| admission → exported record | nothing | nothing | the whole admission claim |

## C — G1–G7 measured against production code

Disposable probe `probe_i09p2ar1.py` (untracked scratch, never staged), 18 rows, 18 pass, exit 0. Each attack constructs the input rather than describing it.

| Gate | Attack | Observed | Result |
|---|---|---|---|
| G1 | caller calls `SemanticAuthority.model_validate({...})` | `ValueError` — loader seal required | REFUSED |
| G2 | row cites a methodology id minted by the caller, manifest lists it | `UNREGISTERED_METHODOLOGY` (methodology registry does not know it) | REFUSED |
| G3 | row cites `OTHER_VENUE_DOC` for a Binance field | `EVIDENCE_NOT_BOUND_TO_PROVIDER` | REFUSED |
| G4 | row uses a field absent from `declared_native_fields` | `NATIVE_FIELD_NOT_DECLARED` | REFUSED |
| G5 | row transformation differs from `approved_transformations[field]` | `TRANSFORMATION_NOT_APPROVED` | REFUSED |
| G6 | manifest resolves no blocking assumption of the row | `BLOCKING_ASSUMPTION_UNRESOLVED` | REFUSED |
| G7 | admitted decision re-created by a caller | byte-identical model dump; no field distinguishes it | **PARTIAL** |

G7 is not "closed because the record carries an id". `LiquidationSideAdmission.model_validate(approved.model_dump())` reproduces an admitted decision exactly, and `T1TradeRecord` exposes **no** approval, authority or digest field at all (`matching_fields=[]`). The approval id is data a caller can type.

## D — Manifest trust-root analysis

Nine boundary probes, each measured:

1. caller replaces registry bytes → `DIGEST_MISMATCH`.
2. caller changes the registry's embedded self-declared digest → `DIGEST_MISMATCH` (the expected digest is never read from the artifact).
3. caller changes both bytes and the embedded digest → `DIGEST_MISMATCH` while the **approved** manifest is used.
4. caller supplies another manifest object → **authority issued for whatever that manifest approves**.
5. caller changes artifact *and* manifest under their own control → **authority issued** (`approval=ATTACKER-APPROVAL`).
6. shipped production manifest → `NO_APPROVAL` (zero artifacts).
7. separately authorized synthetic manifest → authority issued, correctly labelled synthetic.
8. revoked / expired approval replayed → `APPROVAL_REVOKED` / `AUTHORITY_EXPIRED`; window without an instant → `EVALUATION_TIME_REQUIRED`.
9. registry schema revision differs from the approved one → `VERSION_MISMATCH`.

Adjudication of the four separable outcomes:

| Outcome | Verdict |
|---|---|
| `LOADER_LOGIC_VALIDATED` | **YES** — every refusal above measured in production code |
| `TRUSTED_MANIFEST_SOURCE_ENFORCED` | **NO** — nothing in `src/` reads the manifest from disk, pins its digest, or provides an application initialization boundary; `load_semantic_authority` takes `manifest_bytes` from its caller |
| `PROVIDER_EVIDENCE_AUTHENTICATED` | **NO** — evidence references are strings the manifest declares; no blob binding is enforced |
| `OPERATOR_APPROVAL_PROVEN` | **NO** — no signature, no review attestation, no custody chain |

Probe 5 is the decisive measurement: when one actor controls artifact and manifest, the loader issues authority. The module-private sentinel resists *data*, not code with the application's privileges, and no deployment boundary narrows who may call the loader.

## E — G7 record / export attack results

| Mutation | Effect on the record | Distinguishable downstream |
|---|---|---|
| `approval_id` | re-typed, validates | no |
| `registry_digest` | re-typed, validates | no |
| provider identity | re-typed | no |
| evidence reference | re-typed | no |
| confidence | re-typed (any rung) | no |
| canonical side | re-typed | no |
| acquisition lineage | re-typed refs | no |
| methodology identity | re-typed | no |

`LiquidationSideAdmission` requires the two provenance fields when `admitted=True`, which stops an *accident*. It does not stop a *claim*: the model is constructible, frozen only in the Pydantic sense, and no consumer re-validates it against an independently trusted approval context.

**Minimum contract to close G7** (specified, not implemented): an authority-verifying consumer that receives the record *plus* `(manifest_bytes, artifact_bytes, evaluation_at)`, re-loads the authority itself, and refuses any `side_admissions` entry whose `(approval_id, registry_digest)` does not match the authority it just derived — i.e. provenance verified at the boundary, never trusted from the payload. `T1TradeRecord` additionally needs a provenance field, because it has none.

## F — I10 consumer findings

Measured by suite (`test_b5_i10_*`, `test_b5_i11f1_semantic_admission.py`) and by reading `normalize_trade`:

- a bare `ProviderSemanticRegistry` computes `provisional_side` and leaves `aggressor_side = UNKNOWN` (three-conjunct gate: ladder AND authority AND `attests`);
- an object exposing only `.resolve()` cannot serve as authority — `resolve_authority_inputs` accepts only the two model types;
- unapproved evidence stays provisional; the pending token cannot promote;
- the shipped manifest admits nothing (`NO_APPROVAL`);
- Binance behavioural side evidence remains provisional, and `COMMUNITY_DOCUMENTED` never becomes first-party (`is_first_party_grade` unchanged);
- `notional_usd` remains blocked with `unresolved_citation = B5_I08_UNITS_V1`;
- PIT trade economics, duplicate collapse and fingerprinting are untouched (`trade.py` changed only in its `registry` type and the gate).

No accepted I10 behaviour was altered.

## G — I11 consumer findings

Measured by `test_b5_i11_liquidation_semantics.py`, `…i11f1…`, `…i11r1…` (91 tests green) and by reading `_admit_field` / `_admissions`:

- a registry object alone cannot certify a side: the ladder check passes and `UNTRUSTED_AUTHORITY` is recorded;
- position, execution, aggressor and maker/taker remain four separate canonical fields with four separate decisions;
- one mapping cannot authorize another field (`FIELD_MISMATCH`, and `attests` re-resolves the row inside the authority's own registry);
- contradictory sides remain `QUARANTINED` before any authority consideration;
- provisional values remain inspectable; refusal reasons are enumerable;
- all-or-nothing promotion is unchanged (`fully_admitted` requires every supplied claim);
- `SEMANTICS_UNVERIFIED` still tracks the canonical slots exactly;
- zero/missing and PIT conversions untouched; `liquidation_usd` still blocked.

**I11 operator acceptance is not granted by this record.** The I11R2 hold stands.

## H — Empty production-manifest proof

`approval_manifest.json` parses to `artifacts == {}` and `revoked_approval_ids == []`; loading any artifact under it refuses `NO_APPROVAL`. The positive fixtures live only in test modules and in the disposable probe, and each is labelled synthetic. No synthetic approval is reachable from production configuration: there is no production configuration path that supplies a manifest at all.

## I — Second-commit custody review

`89c6939457..6b112f196e` touches exactly one file, `BLOC_05_I06_SCOPE_AUDIT.json`, with **2 changed lines inside one existing row** (`configurations_unchanged`): the clause/detail text gained the disclosed `SENSOR-B5-I09P2A` phrasing. Row count, row ids, `pass` values and every other row are unchanged; no failure became a pass; no allowlist was widened by that commit. Both producers now pass `--check` against the committed bytes (`b5_i06_replay_safety.py --check` = 0, `b5_i09_semantics.py --check` = 0), so the second commit corrected a real drift rather than masking one.

## J — Historical producer / pin verification

| Artifact | Measured SHA-256 | Operative pin | Match |
|---|---|---|---|
| `bloc_05_time_validation.json` | `9ba207fd74339c1bcd8422b39d104ea242a4094a4733eb7f9e3c974328168040` | `P2A_DISCLOSED_EVIDENCE_SHA256` + ledger §190 | YES |
| `bloc_05_replay_safety_validation.json` | `04770f5f31dfe275c91db044614f19c31983cb758b61839fe1c00dd14ff79f2a` | ledger §190 | YES |
| `bloc_05_semantic_validation.json` | `7eeca3ec3b96eeb8d1f21437e6bbad655d6726be88ad424d7b30d73e68c3ff3a` | ledger §190 | YES |

`normalization/{common,identity,terms,time}` is byte-identical to `e2df7109b4` (empty diff), so the I08 detached-worktree reproduction was **not** required and was not re-run; its custody is unchanged by this checkpoint. No evidence artifact was regenerated for this audit.

## K — Focused tests and regression provenance

Re-executed now, on this exact tree:

```text
tests/crypto_sensor_fabric/normalization + storage/test_i11r2_binding_audit.py
  1104 passed, exit 0
```

Accepted from documented provenance (code and test bytes unchanged since that run, verified by the clean tree and the pin table above): the canonical suite `4498 passed, 14 skipped, exit 0` measured on `6b112f196e` for ledger §190. It was **not** re-run here; doing so is optional under directive §09.

## L — Ratification matrix P09-01 … P09-24

| Gate | Frozen clause | Expected | Observed | Independent evidence | Verdict | Limitation |
|---|---|---|---|---|---|---|
| P09-01 | authority unchanged | plan untouched | 7/7 plan paths absent from range; branch resolves `4bb677f9e` | git range | EARNED | — |
| P09-02 | trusted approval source identity | independently controlled source | loader takes caller-supplied manifest bytes; no source enforced | probe 4/5/9, source read | **NOT EARNED** | no deployment boundary |
| P09-03 | approved-byte integrity | digest from manifest only | `DIGEST_MISMATCH` on bytes, self-digest, and bit flip | probes 2/3 | EARNED (integrity only) | says nothing about authenticity |
| P09-04 | provider/evidence binding | foreign evidence refused | `EVIDENCE_NOT_BOUND_TO_PROVIDER` | probe G3 | EARNED | refs are strings, not blobs |
| P09-05 | methodology resolution | unknown refused | `UNREGISTERED_METHODOLOGY` via both registry and manifest list | probe G2 | EARNED | registry itself is caller-supplied text |
| P09-06 | provider-field correctness | undeclared field refused | `NATIVE_FIELD_NOT_DECLARED` | probe G4 | EARNED | — |
| P09-07 | confidence ladder unchanged | sealed ladder | `common/` diff empty; ladder tests green | diff + suite | EARNED | — |
| P09-08 | pending evidence refusal | pending never admits | `PENDING_EVIDENCE` preserved; pending token refused in manifests | suite + `ApprovedArtifact` law | EARNED | — |
| P09-09 | cross-venue refusal | venue polarity not transferred | `side_maps` rule table unchanged; foreign provider evidence refused | suite + probe G3 | EARNED | — |
| P09-10 | direct construction closed | caller cannot mint | `ValueError` on unsealed construction | probe G1 | EARNED (in-process data barrier) | same-privilege code can import the seal |
| P09-11 | I10 consumer enforcement | bare registry cannot promote | `aggressor_side = UNKNOWN` under bare registry | suite | EARNED | — |
| P09-12 | I11 consumer enforcement | registry alone cannot certify | `UNTRUSTED_AUTHORITY` recorded | suite + source | EARNED | — |
| P09-13 | native data preservation | natives verbatim | unchanged tests green | suite | EARNED | — |
| P09-14 | all-or-nothing semantics | no hybrid promotion | `fully_admitted` unchanged | suite | EARNED | — |
| P09-15 | zero/missing noninterference | zero not promoted | unchanged tests green | suite | EARNED | — |
| P09-16 | PIT noninterference | conversions unchanged | unchanged tests green | suite | EARNED | — |
| P09-17 | determinism | same bytes → same authority | probe issues identical approval/digest twice | probe P0 | EARNED | — |
| P09-18 | mutation sensitivity | one-byte flip detected | `DIGEST_MISMATCH` | probe P3 | EARNED | — |
| P09-19 | historical custody | sealed evidence intact | one disclosed 2-line row edit, mechanically produced; everything else byte-identical | git range + producers | EARNED | artifact drift existed and was corrected by a second commit |
| P09-20 | regression | canonical suite | `4498 passed, 14 skipped, exit 0` on this tree | ledger §190 + clean tree | EARNED (accepted provenance) | not re-run in this audit |
| P09-21 | governance binding | mechanical republish only | binding audit 4/4; count delta = two new Python files | suite | EARNED | — |
| P09-22 | no fabricated provider certification | empty manifest, synthetic labelled | `artifacts == {}`; `NO_APPROVAL` | probe P1 | EARNED | — |
| P09-23 | no gate promotion | eight gates unearned | unchanged | governance record | EARNED | — |
| P09-24 | fast-forward Git custody | local == remote, linear | `6b112f196e` both sides; two commits, no merge | git | EARNED | — |

**23 of 24 earned mechanically. P09-02 is not earned, and by the directive's own rule no gate requiring a real operator-approval mechanism may be earned from a synthetic root.**

## M — Decision

`I09P2A_RATIFICATION_HOLD`

Reason, stated plainly: the loader is correct, and it is correct about bytes that the same actor who supplies the artifact also supplies the approval for. Probe 5 demonstrates self-approval whenever the caller controls the manifest. Until a production initialization boundary loads the approved manifest from an independently controlled source and consumers verify provenance instead of reading it, describing this system as an authenticated trust root would be false.

What HOLD does **not** dispute: the mechanical refusals, the empty production manifest, the removed `registry: object` duck-typing, and the fact that a caller-minted registry can no longer promote a canonical field.

## N — Outstanding obligations

| Obligation | Kind | Owner |
|---|---|---|
| trusted manifest source (path + digest + init boundary) | enforcement | engineering (P2b) |
| downstream provenance verification contract | enforcement | engineering (P2b) |
| provenance field on `T1TradeRecord` | enforcement | engineering (P2b) |
| evidence references bound to storage blobs | enforcement | engineering (P2b) |
| PIT registry-revision constraint at ingestion | enforcement | engineering (P2b) |
| real provider documentation and first real approval | provider evidence | operator, external |
| `B5_I08_UNITS_V1` sensor-family ruling | governance | operator |

## O — Next engineering directive (proposed, NOT executed)

**SENSOR-B5-I09P2b — Trusted Consumption and Export-Provenance Closure.** Engineering remediation only; no real exchange approval, no invented evidence, no gate promotion.

Scope: (1) an operator-controlled manifest location whose digest is pinned in a reviewed governance line, with an application initialization function that is the only producer of `SemanticAuthority` in production; (2) a consumer-side verifier that re-loads the authority and refuses record payloads whose provenance does not match; (3) an explicit provenance field for `T1TradeRecord`; (4) blob-level evidence binding through the existing storage custody; (5) PIT revision constraints so a registry revision unavailable at cutoff cannot be applied retroactively; (6) adversarial tests for each; (7) explicit statement that the synthetic root remains synthetic.

Real-provider onboarding/certification stays a separate future checkpoint (`B5-I09b`), never merged into P2b.

## P — Git

Audit commit and remote equality are recorded in ledger §191 and verified after push. No production, test, plan or evidence artifact was modified by this audit.

---

**FINAL:** `I09P2A_RATIFICATION_HOLD` — loader logic validated, trusted manifest source not enforced, G7 export provenance PARTIAL. No gate promoted; B5-I09b DEFERRED; I11 RATIFICATION_HOLD; BLOC_05 INCOMPLETE; I12/I17 unauthorized; research FROZEN.
