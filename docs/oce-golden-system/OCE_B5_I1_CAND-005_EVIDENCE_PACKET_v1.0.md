# OCE Golden System
## B5-I1 — Evidence Packet: CAND-005

**Document ID:** OCE-B5-I1-PACKET-CAND-005
**Version:** 1.0
**Status:** INTAKE_EVIDENCE — UNSCORED
**Candidate identifier:** CAND-005
**Working name (register-only):** Audit-Artifact QA Workbench
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)

---

## 0. Sensor Fabric distinction (explicit)

This candidate processes **security-audit artifacts** (`tv_vm_audit/` — VM configuration, process/file/registry/network activity CSVs, IOC list, baseline/diff/verdict documents). It does **not** touch, execute, or advance `quant-lab/research/crypto_foundry/sensor_fabric/bloc_05/` material. It is quant-adjacent only in subject matter (a trading-VM security exercise produced the artifacts); it performs no trading, no order logic, no market data processing.

## 1. Observable operator outcome

`AUTHORED_SPEC` — The operator asks "is this audit artifact set internally consistent and complete?" and runs one local command over an artifact set: CSV schemas validated, IOC hashes cross-checked against file inventories, baseline-vs-post-run diff rows reconciled, verdict documents checked for referenced evidence, and a signed (digest-stamped) QA summary printed with per-check PASS/FAIL. Success is judgeable from the summary (protocol C1).

Basis: `REPO_ASSET` — a complete real artifact set exists: `tv_vm_audit/` (15 files: `03_PROCESS_TREE.csv`, `04_FILE_ACTIVITY.csv`, `05_REGISTRY_ACTIVITY.csv`, `06_NETWORK_ACTIVITY.csv`, `00_SAMPLE_HASH.txt`, `13_IOCS.json`, `02_BASELINE.md`, `11_POST_RUN_DIFF.md`, `14_FINAL_VERDICT.md`, …).

## 2. Operator-testable acceptance scenarios

`AUTHORED_SPEC` —

1. S-1 (intake-set QA): run over `tv_vm_audit/` as of the intake commit; every schema/check PASSes on the real set (it is a completed, coherent audit); summary digest printed; exit 0.
2. S-2 (schema violation): a scratch copy with a malformed CSV row FAILs schema validation naming file/row/column; canonical set untouched.
3. S-3 (hash mismatch): alter a scratch CSV byte; the digest cross-check FAILs showing expected vs observed digest.
4. S-4 (verdict evidence gap): a scratch verdict referencing a nonexistent evidence file FAILs the reference check with the unresolved target named.
5. S-5 (reconciliation): baseline vs post-run diff rows that contradict (a file marked unchanged in the diff but present in activity CSV) FAIL reconciliation with both rows quoted.

## 3. OCE lifecycle coverage matrix

`AUTHORED_SPEC` —

| OCE surface | Exercised by CAND-005 |
|---|---|
| Intent | Operator declares the artifact set + check profile as bounded intent. |
| Planning | Check battery plan (schema → hashes → refs → reconciliation) with gates. |
| Grants | Read-only filesystem grants; denial envelope for out-of-set paths. |
| Workers | Checks run as discrete jobs; per-check results collected. |
| Artifacts | QA summaries + input digests stored as digest-referenced artifacts. |
| Evidence | Summary is manifest-shaped: input digest, checks, observed values, disposition. |
| Review | Operator approves QA summary; audit methodology stays legible. |
| Identity | Run identity recorded; summaries carry producer identity. |
| Packaging | Local CLI + versioned check profiles. |
| Observability | Header: files scanned, rows parsed, checks run, duration. |
| Recovery | Atomic summary writes; interrupted runs marked partial, never finalized. |

## 4. Deterministic-kernel boundary

`AUTHORED_SPEC` — Deterministic core: CSV schema validation (fixed column contracts per artifact type), digest computation and cross-checking, reference resolution (verdict/IOC → file), baseline/diff reconciliation logic, summary rendering. Fixed artifact set + fixed profile → byte-identical summary (timestamps excepted). LLM-permitted surfaces: none required.

## 5. Bounded input inventory

`AUTHORED_SPEC` grounded on `REPO_ASSET`:

| Input | Path/bounds |
|---|---|
| Artifact set | A declared directory such as `tv_vm_audit/` (15 files at intake; 5 CSVs with fixed column contracts; 1 IOC JSON; markdown verdict docs) |
| Check profile | Versioned profile: which schemas, hash files, reference rules, reconciliation rules |
| Exclusions | Nothing outside the declared set is read |

No network. No execution of artifact content (CSVs/JSON are parsed as data, never run). Unbounded ingestion: none — the set is closed and size-bounded.

## 6. Canonical-state proposal

`AUTHORED_SPEC` — State = QA record: `{qa_id, artifact_set_digest, profile_version, per_check_results[], disposition}` — one append-only JSON per run, schema-validated; input digests make runs replayable. No database.

## 7. Local-run topology

`AUTHORED_SPEC` — Single-process Python CLI; reads the declared artifact directory; writes only its own `out/` directory. No services, no network, no interpreters invoked on artifact content.

## 8. Explainable-output example

`AUTHORED_SPEC` — Format demonstration (not a measurement):

```
CAND-005 qa q-0001  set=tv_vm_audit (digest 9f21c7…)  profile=v1
  csv-schema      PASS 5/5 files (03: 412 rows, 06: 87 rows, …)
  digest-check    PASS 15/15 files match 00_SAMPLE_HASH.txt
  ioc-crossref    PASS 14/14 IOCs resolve to inventoried paths
  verdict-refs    PASS 9/9 evidence references resolve
  diff-reconcile  PASS 0 contradictions between 11_POST_RUN_DIFF and activity CSVs
  DISPOSITION: QA_PASS
```

Failures quote the exact offending row/ref and both conflicting values.

## 9. Completion-window estimate and basis

`AUTHORED_SPEC` — Fits B5-I2→B5-I5 in approximately 4–6 governed increments. Basis: narrow fixed-schema domain (one artifact family), well-bounded parsers; the main work is check wiring and negative/adversarial tests per plan B5.C3.S3.

## 10. Recovery scenario

`AUTHORED_SPEC` — Injected failure: process killed after schema checks, before digest checks. QA record shows completed checks + `complete=false`; restart resumes at the first incomplete check; partial records display `PARTIAL` and are never finalized into a disposition. Write-temp-then-rename keeps the out/ directory free of half-written summaries.

## 11. Governed change-cycle scenario

`AUTHORED_SPEC` — Change: "add a registry-activity concentration check (flag processes touching > N distinct keys)." Applied as governed change: intent → plan → profile `v2` (additive) → new check module + tests → regression: `v1` checks produce identical results on the intake set → prior QA records remain valid and unedited.

## 12. Reuse inventory vs platform-extraction risk

`AUTHORED_SPEC` — Reuse: digest/hash conventions (`hashes.py` patterns), schema-validation patterns (`schema_validator.py`), evidence-manifest shapes for QA records. Bespoke: CSV column contracts for this artifact family and reconciliation rules. Platform-extraction risk: LOW — a single-purpose QA tool over one artifact family; nothing platform-shaped is extracted.

## 13. Governed-path mapping (C10 — all eleven paths)

`AUTHORED_SPEC` — identity: run identity in every summary · intent: declared set+profile · planning: ordered check battery · grants: read-scope grants with denials · workers: checks as jobs · artifacts: digest-stamped QA records · evidence: manifest-shaped results · review: operator-approved QA summary · packaging: local CLI + versioned profiles · observability: run header counts/durations · recovery: atomic partial-run discipline.

## 14. D1–D14 evidence (positive evidence for every "does not require")

| D | Disqualifier | Evidence | Class |
|---|---|---|---|
| D1 | Capital/execution authority | Parses audit files; no capital/execution surface | AUTHORED_SPEC |
| D2 | Live trading/broker credentials | Processes security-audit CSVs about credential-access events as data; holds/uses no credentials; no broker API | REPO_ASSET |
| D3 | Irreversible external effects | Read-only over artifacts; writes only `out/` | AUTHORED_SPEC |
| D4 | Regulated submissions | Local QA report only | AUTHORED_SPEC |
| D5 | Public write access | No publish path | AUTHORED_SPEC |
| D6 | Sensitive mass data | Fixed artifact set already in-repo; no bulk personal data collection | REPO_ASSET |
| D7 | Paid external hosting | Local only; `$0` | AUTHORED_SPEC |
| D8 | Cloud-only operation | Fully local (§7) | AUTHORED_SPEC |
| D9 | Vercel/Railway/SonarCloud/Kilo | Not referenced; stdlib parsers | AUTHORED_SPEC |
| D10 | External hosting authority | None | AUTHORED_SPEC |
| D11 | Public SaaS | Not a service | AUTHORED_SPEC |
| D12 | LLM as canonical state | Deterministic kernel; JSON QA records | AUTHORED_SPEC |
| D13 | Platform rewrite in disguise | Single artifact family, single-purpose checks; bounded reuse (§12) | AUTHORED_SPEC |
| D14 | Recurring cost > `$0` | No paid services | AUTHORED_SPEC |

No UNKNOWN answers. Static contract evidence only; no runtime measurements claimed.
