# BLOC 05 / SENSOR-B5-I10R1 - INDEPENDENT AUDIT AND RATIFICATION HOLD

Checkpoint: SENSOR-B5-I10R1 (audit + adjudication + readiness; READ-ONLY on production)
Starting HEAD: 13b0b39d7c36d72b608568f571b0bbb9d39de513
Frozen plan: 4bb677f9e0266f4dc48405181696019f359ae49f
Decision: **I10_RATIFICATION_HOLD**

This record is append-only. It does not modify, rewrite or re-pin any sealed artifact.

## 1. Custody (verified, not assumed)

| Check | Observed |
|---|---|
| LOCAL_HEAD | 13b0b39d7c36d72b608568f571b0bbb9d39de513 |
| REMOTE_BUILD_HEAD | 13b0b39d7c36d72b608568f571b0bbb9d39de513 (equal) |
| TRACKED_TREE | CLEAN (three pre-existing untracked scratch paths preserved) |
| FROZEN_PLAN | 7/7 byte-identical to 4bb677f9 |
| Routing lock | I08E1 / I09E1 / I09R1 / I10D1 / I10E1 NOT re-executed |

## 2. Full-suite closure verification (ledger section 182)

Commit 13b0b39d7 touches exactly two files, both governance: the progress ledger and
BLOC_05_I10_IMPLEMENTATION_EVIDENCE.md. No production byte, test byte or pin changed.

    python -m pytest tests -q  ->  4357 passed, 14 skipped, exit 0 (1264.53s)

Independently confirmed this run: I10 focused suites 66 passed, exit 0. The 20-item
independent probe and the H1 harness both re-executed green at this HEAD. The canonical
full-suite gate is therefore accepted on the measured section-182 run.

## 3. Semantic evidence custody: JSON pointer diff

    PREDECESSOR 96e0ded3ce  0c844947bfca29c67e540abda52e72ec047966dab3af1ad28c4f9b506fce7636
    SUCCESSOR   384282cbca  2587e373f269692bb69ed809c153ce6d6efb354e08b48f6520c22cecf54ff50a

Exactly **four** changed pointers, all inside the dependency inventory:

| Pointer | Old | New |
|---|---|---|
| /sha256_inventory/tests/.../test_b5_i01_scope_audit.py | 478b9f39...a504 | 6a7a0280...56eb |
| /sha256_inventory/tests/.../test_b5_i05_scope_audit.py | 5e8b89d4...1bab | 4e88f325...8877 |
| /sha256_inventory/tests/.../test_b5_i08_scope_audit.py | 5b70c012...da20 | 806e8829...0a5b |
| /sha256_inventory/tests/.../test_b5_i09_scope_audit.py | 5eab5a70...2024 | ec1b4c4d...0771 |

Verified: 35/35 semantic rows present, case ids identical, **zero** row fields changed,
no provider mapping promoted, no provisional evidence certified, no acceptance row
altered. The delta is authorized dependency-inventory hashes only.

## 4. Historical source/test diff audit

    FILE                              RAW(numstat)  LOGICAL  CRLF old->new
    b5_i06_replay_safety.py           1276/1227     59       0 -> 1276
    test_b5_i01_scope_audit.py         433/429      22       0 -> 433
    test_b5_i05_scope_audit.py         412/407       9       0 -> 412
    test_b5_i08_scope_audit.py         305/298      11       0 -> 305
    test_b5_i09_scope_audit.py         241/242       1       0 -> 241

Logical changes (all narrow, all disclosed in the I10 evidence): I08_DISCLOSED_SRC_PREFIX
became DISCLOSED_SRC_PREFIXES with sensors/ added; allowed sets gained "sensors"; one
"/common/" assertion became "/common/ or /sensors/"; inventory hashes were repinned.
No assertion was removed and no protection was deleted.

## 5. Adversarial scope probe

An unauthorized fourth module was injected into normalization/sensors/ and the five scope
audits were run: exactly **one failed precisely**
(test_sensors_package_is_exactly_the_three_authorized_modules, diff on the extra name),
117 passed. The injected file was removed and the tree re-verified clean. Negative-path
custody is intact.

## 6. Independent I10 probes: 20/20 PASS

| # | Observation |
|---|---|
| 1 | isBuyerMaker=true -> provisional SELL, canonical_admitted False |
| 2 | isBuyerMaker=false -> provisional BUY, canonical_admitted False |
| 3 | canonical aggressor_side stays UNKNOWN |
| 4 | absent evidence -> UNKNOWN, provisional_side None |
| 5 | price 1.0001 vs 999999 -> identical provisional side (price never substitutes) |
| 6 | native price "3120.4000" and qty "12.50000000" preserved exactly |
| 7 | native_event_id 990001 / native_sequence_id 811-812 preserved |
| 8 | venue and contract_instance_id preserved |
| 9 | LINEAR: 2.5 contracts x 0.001 = 0.0025 BTC base, 150.0000 USDT quote |
| 10 | INVERSE: 2.5 x 100 / reference 60000 = 0.0041666... BTC base |
| 11 | no PIT terms -> quantity_base and notional_usd blocked |
| 12 | notional_usd blocked, value null, CONVERSION_BLOCKED |
| 13 | unresolved_citation B5_I08_UNITS_V1 visible |
| 14 | missing differs from zero; a zero quantity still creates no notional |
| 15 | REST vs archive acquisition refs stay distinct for the same event id |
| 16 | cross-venue observations stay distinct |
| 17 | no dedupe/collapse symbol exists (I17 boundary intact) |
| 18 | no replay-eligibility symbol invented (I06 boundary intact) |
| 19 | notional methodology is B5_I08_UNITS_V1, no substitute |
| 20 | registry row stays AMBIGUOUS, admits_critical_t1_use False |

A contract-instance mismatch was also refused: an ETHUSDT observation normalized against
BTCUSDT terms raised ValueError (bloc_05/07 F3).

## 7. Historical I08 reproduction (H1)

    source_ref 03522870d40b839a2eac28eff7841bfb161e05f3
    producer exit 0; rows 55 (pass 55, fail 0)
    measured sha256 == expected sha256 == 260ec571...462cd4
    worktree created and removed

The current-tree U08-19 refusal is the documented checkpoint-time inventory refusal, owned
by the pytest scope audits rather than by the historical proof. U08-20 retains its broad
(0,1) allowance; that remains an open custody weakness.

## 8. Findings

**F1 (blocking).** BLOC_05_I10_IMPLEMENTATION_EVIDENCE.md line 143 records the semantic
successor digest as `459568e909180c1ad5e3a03eaee6e36dbcec9e5660b38620d3195bcd763afc4f`.
No committed blob has that digest; the committed artifact and the operative I06 pin are
`2587e373...f50a`. The evidence record states a false digest for a sealed artifact.

**F2 (blocking).** The I10E1 commit re-encoded five sealed historical custody files from
LF to whole-file CRLF. The logical change is 1-59 lines per file while the raw diff is
241-1276 lines. Nothing semantic changed, but the re-encoding was never disclosed and it
inflates every custody diff that follows.

**F3 (tracked).** U08-20 still permits an inverted (0,1) discrimination that the frozen
cases do not discriminate.

**F4 (tracked).** The I08 producer cannot be re-run at HEAD (U08-19 is now non-pass because
I09E1 legitimately added three common/ modules). It fails closed and does not rewrite.

**F5 (tracked).** BLOC_05_I10_READINESS_ASSESSMENT.md still asserts AUTHORITY = NONE.

**F6 (tracked).** I09R1 records R09-01..R09-20 only; R09-21/R09-22 are absent repo-wide and
the twenty-counterexample seven-field table was never tabulated.

## 9. Decision and remediation

    I10_RATIFICATION_HOLD

The implementation is behaviourally sound: 20/20 independent probes, 66 focused tests, H1
reproduction, negative-path custody intact. Ratification is withheld because the evidence
record itself is false on F1 and incomplete on F2. Certifying a document that misstates a
sealed artifact's digest would ratify an untrue record.

Remediation (requires its own authorization; none of it is executed here):

R1. Append a clarification record correcting F1 to `2587e373...f50a`, citing the four
    authorized inventory pointers. Do not edit the sealed I10 evidence table.
R2. Disclose F2 in the same record, and optionally normalize the five files back to LF in a
    separately authorized mechanical commit that repins the four inventory hashes and the
    I06 I10_DISCLOSED_SHA256 entries together.
R3. Leave U08-20 (F3) to B5-I08R2 or to an explicit re-scope.

Once R1 and R2 are recorded, I10 may be adjudicated again against the same measured
evidence without re-running the implementation.

## 10. R10 matrix

| Gate | Result |
|---|---|
| R10-01 custody + frozen authority | PASS |
| R10-02 local == remote | PASS |
| R10-03 clean tree, scratch preserved | PASS |
| R10-04 frozen plan 7/7 | PASS |
| R10-05 production scope = sensors/ + fixtures only | PASS |
| R10-06 35/35 semantic rows preserved | PASS |
| R10-07 changed pointers limited to inventory hashes | PASS |
| R10-08 recorded successor digest equals committed blob | **FAIL (F1)** |
| R10-09 I01 scope integrity | PASS, defect F2 |
| R10-10 I05 scope integrity | PASS, defect F2 |
| R10-11 I06 producer integrity | PASS, defect F2 |
| R10-12 I08 scope integrity | PASS, defect F2 |
| R10-13 I09 scope integrity | PASS, defect F2 |
| R10-14 negative-path custody (4th module rejected) | PASS |
| R10-15 native values + identity preserved | PASS |
| R10-16 Binance behavioural mapping (Layer 1) | PASS |
| R10-17 provisional semantic safety | PASS |
| R10-18 I04B linear/inverse correctness | PASS |
| R10-19 unresolved I08 conversion safety | PASS |
| R10-20 lineage + I17 boundary | PASS |
| R10-21 full canonical regression | PASS (section-182 run, scope verified) |
| R10-22 H1 reproducibility | PASS |
| R10-23 deterministic evidence | PASS (fail-closed, artifact byte-identical) |
| R10-24 governance binding, no gate promotion, fast-forward | PASS |

One mandatory gate failed, so there is no global PASS and no ratification.

## 11. Non-claims

B5-I10 acceptance is NOT granted by this record. Nothing here earns I09-b provider
certification, T10-07 duplicate collapse, cross-family USD methodology registration, or any
of the eight Bloc 5 program gates. B5-I11 is NOT authorized.
