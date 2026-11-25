# RUNG 1 — INDEPENDENT ADVERSARIAL VERIFICATION PACKAGE (R0)

**Status: `RUNG1_INDEPENDENT_PROBES_READY` — implementation absent, execution pending.**

| Field | Value |
|---|---|
| Mission | `SENSOR-B5-P3-RUNG1-INDEPENDENT-CONTRACT-CHALLENGE-R1` |
| Role | Independent Adversarial Verification Engineer (not implementation) |
| Branch | `agent/crypto-sensor-fabric-p3-consumer-rung1-audit-prep-r1` |
| Base (authorized lineage) | `13086755d22a539c6a4dcb20e782bce97fcde82d` |
| Production design | `295acb5245ecc47d6f5c0a07f8ff631aa7217c15` |
| Prior security correction (preserved, not merged) | `6e6ef21929bf621976a2a45d8e6e3b989c63528f` |
| Prior R6 audit package | `5be77af4bc88c09a0ac5616951f3d34d68ad1eea` |
| Audited tree for governance behaviour | `13086755d` (the Rung 1 branch head) |
| Agent 1 implementation | **ABSENT** — see below |

This package is a **non-collected research artifact**. Nothing here is a tracked
`test_*.py` under `quant-lab/tests/`, so no scope audit is widened and no new
canonical test path is created.

---

## 1. Why execution is pending

`agent/crypto-sensor-fabric-p3-consumer-rung1-build-r1` does not exist, locally
or on `origin`. The only Rung 1 branch is
`agent/crypto-sensor-fabric-p3-consumer-rung1-r1`, whose head is the D-1
authorization commit `13086755d` itself — i.e. the branch still contains the
*authorization packet* and **no** `consumer/models.py`. There is therefore no
implementation to audit, no A1 commit to verify as preceding implementation, and
no contract test to inspect.

Per mission section 7 the probes are published in executable form now, every
implementation-dependent case is recorded as
`NOT_EXECUTED — IMPLEMENTATION_PENDING`, and no failure is manufactured to stand
in for an absent implementation.

---

## 2. Deliverables

| File | Materializes as | Role |
|---|---|---|
| `test_rung1_contracts.py.txt` | `test_rung1_contracts.py` | C01–C22 contract challenge |
| `test_rung1_governance.py.txt` | `test_rung1_governance.py` | G1–G8 exact-file governance challenge |
| `rung1_fixtures.py.txt` | `rung1_fixtures.py` | fixture architecture for Rungs 1–4 (self-testing) |
| `probe_authority_distinction.py.txt` | `probe_authority_distinction.py` | section 5 authority measurement |
| `FIXTURE_SPECIFICATION.md` | — | section 6 fixture specification |
| `AUTHORITY_DISTINCTION_OBSERVATION.md` | — | section 5 classification |
| `rung1_independent_audit_results.json` | — | machine-readable ledger of what actually ran |
| `README.md` | — | this file |

---

## 3. Exact materialization and execution command

Run from Git Bash. It never touches an audited branch.

```bash
EVID="quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/p3_rung1_independent_audit_r0"
AUDIT="$(cd quant-lab/.. && pwd)/quant-lab"     # the audited tree to probe
RUN="$(mktemp -d)"

for f in "$EVID"/*.py.txt; do
  cp "$f" "$RUN/$(basename "${f%.txt}")"
done

# fixture self-test: every fixture must really build before anything is claimed
PYTHONPATH="$AUDIT/src" python "$RUN/rung1_fixtures.py"

# contract challenge (C01-C22) and governance challenge (G1-G8)
PYTHONPATH="$AUDIT/src" python -m pytest "$RUN" -v -rs -p no:cacheprovider

# section 5 measurement
PYTHONPATH="$AUDIT/src" python "$RUN/probe_authority_distinction.py"

rm -rf "$RUN"
```

Against the future pinned implementation, replace `$AUDIT` with an isolated
checkout of that commit. The probe resolves the audits from the importable
`crypto_sensor_fabric` package, so `PYTHONPATH` alone decides which tree is
audited — there is no path constant to edit.

---

## 4. What actually executed on `13086755d`

```
rung1_fixtures.py       7/7 fixtures VALID   (exit 0)
test_rung1_governance.py  7 passed, 3 failed, 1 skipped
test_rung1_contracts.py   1 passed (import state), 25 skipped (IMPLEMENTATION_PENDING)
py_compile                3/3 probe modules compiled
```

The fixture self-test result is load-bearing: `T1TradeRecord`,
`T1LiquidationRecord`, `ReplayEvidence` and a real
`NormalizationMethodologyRegistry` all construct from these fixtures. A probe
that refuses everything because its own fixture is invalid is therefore ruled
out in advance.

### 4.1 Three executed RED findings (governance, not Rung 1 code)

All three are defects in the **frozen** admission law that Agent 1 was told to
replace with true exact-file authorization. Each has a minimal counterexample.

| Case | Smallest counterexample | Observation |
|---|---|---|
| **G2** | `tests/…/test_b5_i01_scope_audit.py_evil.py` | The audits already contain exact-FILE entries, but `path.startswith(...)` makes them prefixes. A tracked `.py` beside the authorized file is admitted by both audits. |
| **G3** | `…/consumer/models.py_suffix.py`, `…/consumer/models.py/../policy.py` | Simulated: appending the two authorized strings to the frozen tuple (the instructed anti-pattern) admits every suffix variant and a `..` climb-out. The naive amendment is provably insufficient. |
| **G7** | staged `…/consumer/models.py_suffix.py` | In a disposable git repository, staged, unstaged and untracked paths are each admitted by the *same* `startswith` predicate. Staged admission, which is what a commit ships, admits the suffix variant. |

### 4.2 The structural finding behind them

The frozen allowlists do not contain one kind of entry. They contain **three**,
and no one-bit "exact or prefix" switch can represent them:

| Kind | Example | I05 | I10 |
|---|---|---|---|
| `dir` (trailing `/`) | `src/crypto_sensor_fabric/normalization/time/` | 9 | 8 |
| `file` (has an extension) | `tests/…/test_b5_i01_scope_audit.py`, `.gitignore` | 4 | 9 |
| `legacy_prefix` (bare stem, no extension) | `tests/…/test_b5_i08`, `tests/…/test_b5_i05_` | 5 | 9 |
| **total entries** | | **18** | **26** |

**Count discrepancy, recorded rather than smoothed:** the D-1 authorization
packet (`01_AUTHORIZATION_MATRIX.md`) states 25 I10 entries; the tuple parses to
**26**. The grant's shape is unaffected, but the pre-existing packet's count is
off by one and should not be quoted as authoritative.

A mechanism that treats every non-`/` entry as exact silently **revokes**
`legacy_prefix` grants that later checkpoints already shipped (G6 proves the
oracle must keep them). The probes therefore specify an explicit entry kind
rather than inferring one, and G6b asserts that no `legacy_prefix` can silently
contain a Rung 1 grant.

**Required behaviour, executed as an oracle (G4, G4b, G6, G6c):** exact `file`
entries compare by equality; `dir` and `legacy_prefix` entries remain prefixes;
any candidate containing a `..` segment is refused; a directory grant for
`consumer/` is refused because it would admit every sibling. The oracle admits
exactly the two authorized paths and refuses all eleven forbidden paths,
including `consumer/policy.py`, `consumer/custody_authority.py`,
`consumer/__init__.py`, and the historical security suite path.

### 4.3 Pending

* G5 — comparison against Agent 1's real exact-file mechanism. It is written as
  a conditional probe keyed on the *behaviour* of the audits (`startswith` still
  admits a suffix variant ⇒ not yet implemented). It will begin executing on its
  own once the amendment lands, with no edit required.
* C00b–C22 — all 25 contract cases, pending `consumer/models.py`.

---

## 5. What this package does not claim

* Not independent acceptance: no implementation was executed, so A1.1–A1.5 are
  unverified.
* Not a finding against Agent 1: the three RED cases are defects in the frozen
  governance law that predate his branch.
* Not a production authorization compromise: see
  `AUTHORITY_DISTINCTION_OBSERVATION.md`.
* Not canonical scope: the full `test_b5_p3_consumer_security.py` lineage stays
  historical specification evidence and is **not** merged into Rung 1, and this
  package adds no tracked `.py` file anywhere.

## 6. Disposition

`RUNG1_INDEPENDENT_PROBES_READY` — probes are executable, syntax-checked, and
have produced real governance evidence; the contract challenge awaits a
published implementation.
