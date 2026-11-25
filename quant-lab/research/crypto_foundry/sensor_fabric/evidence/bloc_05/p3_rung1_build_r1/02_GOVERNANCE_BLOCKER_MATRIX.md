# 02 — Governance blocker matrix, measured

Every row below was executed against the real tree, with the two authorized files present, at
base `13086755`. Nothing here is inferred from reading: each refusal is the actual assertion
message.

## 1. The row that blocks

### I01 — `test_b5_i01_scope_audit.py`

```
def test_only_authorized_subpackages_exist() -> None:        # line 68
    allowed = {"identity", "terms", "time", "common", "sensors", "authority"}   # line 89
    present = {
        entry.name
        for entry in PACKAGE.iterdir()
        if entry.is_dir() and entry.name != "__pycache__"
    }
    assert present <= allowed, f"unauthorized subpackages: {sorted(present - allowed)}"
```

Measured: `1 failed, 46 passed` — `AssertionError: unauthorized subpackages: ['consumer']`.

Two details matter for the ask:

* `present` tests `entry.is_dir()` only, so an implicit namespace directory counts. Omitting
  `__init__.py` does **not** avoid the refusal (it avoids only the separate inventory unit).
* The set grows by **one named package at a time**. The I09P2A comment at line 89 records that
  precedent for `authority`. Adding `"consumer"` is the same disclosed pattern, not a new one.

This audit is **not** in the authorized amendment set. That is the whole blocker.

## 2. The rows the grant covers

### I05 — `test_b5_i05_scope_audit.py`

`allowed_prefixes` (18 entries, `startswith`) plus the single mechanical-republish exception.
Measured with the two files present: **failed** on

```
assert unauthorized_untracked == [], f"unauthorized untracked paths: {unauthorized_untracked}"
```

both new paths are outside every prefix. The audit also asserts over **staged** and
**unstaged** sets, so staging cannot hide a path from it — which is why the amendment must
precede implementation, as the commit ladder requires.

### I10 — `test_b5_i10_scope_audit.py`

`allowed` (25 entries, `startswith`) asserted over staged, unstaged and untracked. Measured:
`1 failed, 21 passed` on `test_only_the_i10_authorized_prefixes_carry_tracked_changes`.
Same two paths, same refusal.

## 3. The rows that do not block (re-measured, not inherited)

| Audit | Result with the files present | Reading |
|---|---|---|
| I09 scope audit | **9 passed** | `consumer/` is outside every sealed tree (`identity`, `terms`, `time`, `normalization/{__init__,models,enums}.py`, `registry`, `config/…`). The R0 finding holds. |
| I11R2 binding audit + evidence | **14 passed** | Passed *because* the files were untracked: the audit counts **tracked** Python. It fails only once the files are staged, which is exactly what the republish step exists for. |

## 4. Inventory

| Measurement | Value |
|---|---|
| Tracked `.py` at base and at publication | **1,102** |
| Tracked `.py` with Rung 1 staged (expected) | **1,104** |
| Unit avoided by omitting `__init__.py` | 1 (would be 1,105) |
| `python_files_scanned` in the published I11R2 artifact | **1,102**, unchanged |

## 5. After withdrawal

With the two files removed, all six audits — I01, I05, I09, I10, I11R2 binding, I11R2
evidence — were run together:

```
122 passed
```

and the canonical universe returned to **4,733** at digest
`1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837` — the anchor digest,
byte for byte. The branch therefore ships a tree that passes its own governance, rather than
one that documents an exception to it.
