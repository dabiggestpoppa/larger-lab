# 03 — The prepared exact-file amendment, and why it was not applied

The directive is right that appending a filename to a `startswith()` tuple grants nothing: a
string in a prefix tuple is a prefix. So the amendment is a **second, exact-match predicate**,
kept separate from the historical tuples.

## 1. The predicate

```python
#: SENSOR-B5-P3-RUNG1-BUILD-R1 (operator directive: AUTHORIZE_D1_ONLY).
#: EXACT paths, not prefixes.  A ``consumer/`` prefix would also authorize
#: policy.py (Rung 2) and custody_authority.py / rebinding.py (Rung 3) under a
#: Rung 1 decision, which D-1 does not grant.  Every historical prefix and every
#: historical named exception above stays exactly as it was.
rung1_exact_paths = frozenset(
    {
        "src/crypto_sensor_fabric/normalization/consumer/models.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py",
    }
)

def _authorized(path: str) -> bool:
    return path.startswith(allowed_prefixes) or path in rung1_exact_paths
```

Applied identically in **I05** (`_authorized`, already a function — one clause added) and in
**I10** (which asserts inline; it gains the same `_authorized` helper and its three loops call
it). Both audits then keep their existing treatment of staged, unstaged and untracked
changes, and neither historical exception is touched.

## 2. Counterexamples the amendment must carry

| Path | Expected | Why |
|---|---|---|
| `src/crypto_sensor_fabric/normalization/consumer/models.py` | admitted | exact D-1 file |
| `tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py` | admitted | exact D-1 file |
| `…/consumer/models.py.backup` | refused | suffix is not the file |
| `…/consumer/policy.py` | refused | Rung 2, not granted |
| `…/consumer/custody_authority.py` | refused | Rung 3, not granted |
| `…/consumer/rebinding.py` | refused | Rung 3, not granted |
| `…/consumer/__init__.py` | refused | not granted; not needed (namespace import measured) |
| `…/test_b5_p3_consumer_security.py` | refused | sibling workstream (`16b4a0b2`) |
| every historical permitted path | still permitted | prefixes unchanged |

The `.backup` and `policy.py` rows are the ones that prove exactness: a prefix clause would
admit both.

## 3. Why it is documented here instead of committed

Applying it would leave the tree **green on I05 and I10 and red on I01**, because the
directory itself is the subpackage I01 refuses. A commit in that state would claim a Rung 1
implementation while its own governance fails, and it would put an unauthorized expansion
(I01) one keystroke from being normalised as precedent. Neither is acceptable, so the
amendment is published as text with its counterexamples and no commit.

The moment I01's single named entry exists, this exact patch plus the two file contents
(hashes in `04_IMPLEMENTATION_RESULT_AND_WITHDRAWAL.md`) complete A2 without further design
work.
