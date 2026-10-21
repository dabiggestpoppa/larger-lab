---

# B4-CXR7U9R48 — AUTHORITY COHERENCE REPAIR AND DEEP IMMUTABILITY

**This section supersedes nothing in R47. It records what R47 and R47S
achieved, the two defects R47 left open, and every R48 repair.** R47's
evidence remains valid for the tests R47 actually ran.

## 1. What R47 and R47S legitimately achieved

R47 proved one record read and one selector read per decision, removed
caller-declared authority roots, anchored the coordinate before path
resolution, and made selector parsing singular and bounded. R47S1 closed a
real command-argument-injection channel at the `docker exec` / `docker cp`
operands. R47S2 cleared reliability findings that were real defects. R47S3
repaired the R43 negative control that had silently stopped weakening the
engine, after Linux CI exposed it as a barrier timeout.

R47S implementation-head authoritative workflow runs:
`36946471672` b1, `36946471666` b2, `36946471606` b3, `36946471626` b4,
`36946476467` B1-I1R — all SUCCESS at `cb2f0ed8a0db82568222a894624ea4bc369724b8`.

## 2. The two defects R47 left open

### 2.1 Post-R47 authority-coherence defect (directory generation mixing)

R47 proved a *count* of reads, not their *provenance*. The record was read
through a PATHNAME while the selector was read through the admitted directory
descriptor, so a whole-directory replacement landing between them produced an
ACCEPTED decision combining a PROMOTED record from generation A with a
`finalize` selector from generation B.

Reproduced deterministically before the repair: the weakened R47-shaped
control returns `record_state='PROMOTED'` with `selector='finalize'` and the
mixed verdict is accepted. The shipped engine at `5cc57a02` refuses the same
attack. This discrimination is an executable proof, not an assertion.

### 2.2 Shallow immutability defect

`@dataclass(frozen=True)` stopped attribute rebinding and nothing else. The
nested mappings remained ordinary dicts, so `snapshot.record["state"] =
"FINALIZED"` and `snapshot.selector.claim["transition"] = "finalize"` both
succeeded, and a caller holding the dict it supplied could rewrite decision
material underneath a decision already in progress.

### 2.3 Generalised anchor-scan limitation (R47S3's own proof)

The S3 integrity scan accepted an anchor if it occurred in ANY approved target
text. That is a weaker claim than it appears: an anchor that drifted out of
its intended target but happened to occur somewhere else would have passed.
This was found by simulating the S2 reformat — the first version of the check
had no teeth at all, because hoisting the R43 anchor into a module constant
made it invisible to a scan that only read inline `.replace()` literals.

## 3. Every R48 repair

| SHA | Tree | Subject |
|---|---|---|
| `f9d1ae7f937ddb52b409e2af9ecf5e6ee1d99847` | `d97236fe906a4c839310760d8f289ebb7685b6f1` | R48R1 bind recovery record and selector to one directory fd |
| `bbb58b2ae3007d0fafe0f4c7a8f6d99334b3c422` | `b4f16b76a4147d8c24049f909bd30050771b4056` | R48R2 make recovery authority deeply immutable |
| `116c42bf61b4809ae6c6cfd6fd2a8a127ee0613d` | `d3422f9570bcd362770cc0275bd684695fbc8aa4` | R48R3 prove coherent authority generation and immutability |
| `5cc57a02188c525b865273782fc58dd2515c6f5c` | `38ebdbe1c09cc129e42550d3a0102db8f9c065bc` | R48R4 simplify classification and bind negative controls to targets |

R48R1: one admitted transitions-directory descriptor owns BOTH reads. The
record is opened descriptor-relative with `os.open(name, flags, dir_fd=...)`,
bounded before and during the read, admitted for type, privacy, durable-name
census, inode stability and pathname identity. The directory identity is
rechecked after both reads — descriptor-relative on POSIX, re-identified
without following a redirection on Windows — and any change fails closed.
`_load_transition_record` no longer participates in any authority decision; a
caller-supplied record is a cross-check only.

R48R2: authority material is deeply immutable. Mappings are rebuilt as an
immutable dict refusing `setitem`/`delitem`/`pop`/`popitem`/`update`/
`setdefault`/`clear`/`ior`; sequences become tuples; sets become frozensets.
A dict SUBCLASS is used rather than `MappingProxyType` because the engine's own
decision law is expressed in `isinstance(x, dict)` checks and canonical digests
must stay JSON-serialisable.

R48R3: 33 deterministic proofs, every attack paired with a weakened control.

R48R4: the classifier is one dispatch table over pure per-state handlers.
Writing the proofs found a real defect: an unhashable `state` raised
`TypeError` out of the table lookup instead of failing closed. Six negative
controls were retargeted with their weakened behaviour unchanged.

## 4. Test truth

Full local collection on this Windows host: **591 passed, 48 skipped, 1
failed**. The single failure is `test_backup_hardening.py::
test_incomplete_full_backup_rejected`, a pre-existing host-timing failure
(60 s `subprocess.TimeoutExpired` around `backup.sh --scope state-only`);
it reproduces identically at the authorised start head and passes in Linux CI.

All R4x recovery/recovery-authority suites: **377 passed, 18 skipped**. The 18
skips are declared platform gates; the R48R3 directory-replacement and
deep-immutability proofs execute on every platform, and the three POSIX-only
record attacks execute in Linux CI.

R48 added 72 mandatory nodes (33 in R48R3, 39 in R48R4), all selected by
`run-validation.sh` and all present in the registry with zero duplicate node
IDs.

## 5. External checks — unchanged, and disclosed

- **SonarCloud** check run `110650539392` — **FAILURE** at the R47S
  implementation head. GitHub's annotation feed is a 50-item SAMPLE of the
  open new-code issues; absence from it is not proof an issue is resolved, so
  no repository-wide finding count is claimed here. No NOSONAR, no
  exclusions, no profile or threshold changes were made in R48.
- **Kilo Code Review** check run `110649645875` — **FAILURE**, provider-side,
  during workspace setup and before code review: `sandbox storage full`,
  exit 128, in `git-lfs smudge` on
  `quant-lab/research/crypto_foundry/alt_rotation/data_1/ALT_DATA_1_ASSET_MULTISCALE_FEATURES.parquet`
  (`Clone succeeded, but checkout failed`). Remedy is operator-side: raise the
  provider's LFS/sandbox storage quota, or set `GIT_LFS_SKIP_SMUDGE=1` in the
  checkout environment. The LFS object is untouched. Kilo is NOT claimed to
  have succeeded on the basis of any local test.

## 6. Accounting

cloud mutations = 0 · broker mutations = 0 · capital mutations = 0 ·
execution mutations = 0 · recurring cost = $0 · capital.authority = none.
origin/main remains `7c7816f382947bbc8a1f2154435fc436f2428fa8`, untouched.

**Status: INTERNAL R48 IMPLEMENTATION COMPLETE. `MERGE_AUTHORIZED = false`
while SonarCloud and Kilo remain non-success.**