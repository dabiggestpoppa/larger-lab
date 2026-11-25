# RUNG 1 — INDEPENDENT ADVERSARIAL VERIFICATION PACKAGE (R0)

**Status: `RUNG1_INDEPENDENT_PROBES_READY` — probes executable and executed where possible;
no implementation is available to audit.**

| Field | Value |
|---|---|
| Mission | `SENSOR-B5-P3-RUNG1-INDEPENDENT-CONTRACT-CHALLENGE-R1` |
| Role | Independent Adversarial Verification Engineer (not implementation) |
| Branch | `agent/crypto-sensor-fabric-p3-consumer-rung1-audit-prep-r1` |
| Base (authorized lineage) | `13086755d22a539c6a4dcb20e782bce97fcde82d` |
| Production design | `295acb5245ecc47d6f5c0a07f8ff631aa7217c15` |
| Agent 1 implementation branch | `agent/crypto-sensor-fabric-p3-consumer-rung1-build-r1` @ `ea17eb5ae3df9319745c66780e85e0a9f1aa9b98` |
| A1 authorization precedes implementation | **YES** (`13086755d` is an ancestor of `ea17eb5ae`) |
| Implementation code in that commit | **NONE — withdrawn by Agent 1 before publication** |
| Prior security correction (preserved, not merged) | `6e6ef21929bf621976a2a45d8e6e3b989c63528f` |
| Prior R6 audit package | `5be77af4bc88c09a0ac5616951f3d34d68ad1eea` |
| Audited tree for governance behaviour | `13086755d` (source identical to `ea17eb5ae`) |

This package is a **non-collected research artifact**. Nothing here is a tracked
`test_*.py` under `quant-lab/tests/`, so no scope audit is widened and no new
canonical test path is created.

---

## 1. What happened to the implementation

Agent 1 published `ea17eb5ae` **during this mission**. The commit contains six
evidence documents and **no source file**: he implemented Rung 1, executed 32
contract tests, then withdrew the code because the tree cannot be green under the
frozen I01 audit until a *third* amendment is granted.

Independently verified by this audit, not taken on trust:

| Claim in his record | Independent measurement | Verdict |
|---|---|---|
| tracked Python returns to 1,102 | `git ls-tree -r ea17eb5ae \| grep -c '\.py$'` → **1102** | confirmed |
| the `consumer/` directory is gone | `git ls-tree -r ea17eb5ae \| grep -c 'normalization/consumer/'` → **0** | confirmed |
| I01 refuses the subpackage | I01 `test_only_authorized_subpackages_exist` allows `{identity, terms, time, common, sensors, authority}` — **`consumer` absent** | confirmed |
| A1 authorization precedes implementation | `13086755d` is an ancestor of `ea17eb5ae` | confirmed |
| 32 contract tests passed; 4,765 vs 4,733 nodes | **not reproducible** — see below | unverified |

**The reproducibility gap.** He records blob hashes
`f7f2ab98…` (models.py) and `837a7943…` (contract test), but neither object exists
in this repository (`git cat-file -t` → *could not get object info*), no
dangling commit among the 20 inspected contains a `normalization/consumer/`
path, and the branch reflog shows only `branch: Created from HEAD` followed by
the documentation commit. The implementation therefore exists **as prose and
hashes only**. Its results cannot be independently reproduced, and this audit
does not treat them as established.

That is an audit limitation, not a finding of dishonesty: the withdrawal logic is
sound and is corroborated by the governance probes below.

---

## 2. Deliverables

| File | Materializes as | Role |
|---|---|---|
| `test_rung1_contracts.py.txt` | `test_rung1_contracts.py` | C01–C22 contract challenge |
| `test_rung1_governance.py.txt` | `test_rung1_governance.py` | G1–G9 exact-file governance challenge |
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
AUDIT="$(cd quant-lab/.. && pwd)/quant-lab"     # the tree to probe
RUN="$(mktemp -d)"

for f in "$EVID"/*.py.txt; do
  cp "$f" "$RUN/$(basename "${f%.txt}")"
done

# fixture self-test: every fixture must really build before anything is claimed
PYTHONPATH="$AUDIT/src" python "$RUN/rung1_fixtures.py"

# contract challenge (C01-C22) and governance challenge (G1-G9)
PYTHONPATH="$AUDIT/src" python -m pytest "$RUN" -v -rs -p no:cacheprovider

# section 5 measurement
PYTHONPATH="$AUDIT/src" python "$RUN/probe_authority_distinction.py"

rm -rf "$RUN"
```

To run against a future pin, replace `$AUDIT` with an isolated checkout of that
commit and add the authorized implementation paths to it **outside** its
tracked tree (a copy under `$AUDIT/src/...` suffices; the probes import through
`PYTHONPATH` and never write to the audited tree). The probe resolves the audits
from the importable `crypto_sensor_fabric` package, so `PYTHONPATH` alone decides
which tree is audited — there is no path constant to edit.

---

## 4. What actually executed on `13086755d`

```
rung1_fixtures.py         7/7 fixtures VALID        (exit 0)
test_rung1_governance.py  8 passed, 3 failed, 1 skipped
test_rung1_contracts.py   1 passed, 25 skipped      (IMPLEMENTATION_PENDING)
py_compile                3/3 probe modules compiled
```

The fixture self-test result is load-bearing: `T1TradeRecord`,
`T1LiquidationRecord`, `ReplayEvidence` and a real
`NormalizationMethodologyRegistry` all construct from these fixtures, so a probe
that "refuses everything" because its own fixture is invalid is ruled out in
advance.

### 4.1 Three executed RED findings (governance, not Rung 1 code)

All three are defects in the **frozen** admission law. Each has a minimal
counterexample, and each is independent of any implementation.

| Case | Smallest counterexample | Observation |
|---|---|---|
| **G2** | `tests/…/test_b5_i01_scope_audit.py_evil.py` | The audits already contain exact-FILE entries, but `path.startswith(...)` makes them prefixes. A tracked `.py` beside the authorized file is admitted by both audits. |
| **G3** | `…/consumer/models.py_suffix.py`, `…/consumer/models.py/../policy.py` | Simulated: appending the authorized strings to the frozen tuple admits every suffix variant and a `..` climb-out. The naive amendment is provably insufficient. |
| **G7** | staged `…/consumer/models.py_suffix.py` | In a disposable git repository, staged, unstaged and untracked paths are each admitted by the *same* `startswith` predicate. Staged admission — what a commit ships — admits the suffix variant. |

**These findings converge with Agent 1's own prepared amendment**, which is
exactly the oracle specified here (`path in rung1_exact_paths` as a second,
exact-match clause), not a widened tuple.

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
**26**. The grant's shape is unaffected, but the packet's count is off by one and
should not be quoted as authoritative.

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

### 4.3 The third blocker D-1 omitted (G9)

The D-1 packet inventoried I05, I10, I09 (found not sealed) and I11R2. It did
**not** name **I01**, whose `test_only_authorized_subpackages_exist` admits only
`{identity, terms, time, common, sensors, authority}` — `consumer` is absent. A
grant naming only the two files could therefore never produce a green tree, which
is precisely why the implementation was withdrawn.

G9 pins that finding: I01's membership test is already **exact** (a set, not a
prefix), so the third amendment must add one subpackage name, while I05/I10 need
exact file paths. Three amendments, of **two different shapes**, are required:

| Audit | Shape of the required grant | Mechanism |
|---|---|---|
| I01 | one subpackage name | set membership (already exact) |
| I05 | two exact file paths | second exact-match clause beside the prefix tuple |
| I10 | two exact file paths | same clause, applied to its three loops |

### 4.4 Pending

* G5 — comparison against a *published* exact-file mechanism. Written as a
  conditional probe keyed on the behaviour of the audits (`startswith` still
  admits a suffix variant ⇒ not implemented). It begins executing on its own once
  the amendment lands, with no edit required.
* C00b–C22 — all 25 contract cases, pending retrievable implementation content.

---

## 5. What this package does not claim

* **Not independent acceptance of Rung 1.** No implementation content was
  executed, so A1.1–A1.5 remain unverified here. Agent 1's `32 passed` is
  recorded as *his* result, not endorsed.
* **Not a finding against Agent 1.** The three RED cases are defects in the frozen
  governance law that predate his branch; his withdrawal is corroborated.
* **Not a production authorization compromise.** See
  `AUTHORITY_DISTINCTION_OBSERVATION.md`.
* **Not canonical scope.** The full `test_b5_p3_consumer_security.py` lineage
  stays historical specification evidence and is **not** merged into Rung 1, and
  this package adds no tracked `.py` file anywhere (verified: 0 such files in the
  commit; I05+I10 scope audits report 52 passed with the package present).

## 6. Disposition

`RUNG1_INDEPENDENT_PROBES_READY`.

The probes are executable, syntax-checked, and have produced real governance
evidence against the frozen tree. The contract challenge is complete and idle
until implementation content is retrievable at a pinned commit. **The blocking
next act is governance, not code:** I01, I05 and I10 must each be amended (one
subpackage name; two exact file paths each), and only then can A2 land content
whose 32 contract results this package can actually reproduce.
