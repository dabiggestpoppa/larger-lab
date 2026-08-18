# QL-EXEC-R2.1 — DEFECT AUDIT

## D1 — Broker-specific fill codes used as universal default

**Before** (`mt5.py`):
```python
_DEFAULT_FILL_POLICY_CODES = {FOK: 1, IOC: 2, RETURN: 0}   # Ox-observed
...
self._fill_policy_codes = dict(fill_policy_codes or _DEFAULT_FILL_POLICY_CODES)
```
Every future MT5 broker silently inherited the Ox-permuted mapping.

**After:**
```python
self._fill_policy_codes = self._resolve_fill_policy_codes()
# profile override  ->  standard_fill_policy_codes(mt5_module)  ->  {} (fail closed)
```
Generic default is derived from the injected module's `ORDER_FILLING_FOK/IOC/RETURN`
constants. Ox mapping requires `profile=ox_observed_execution_profile()`.

**Verdict:** REPAIRED.

## D2 — UNKNOWN / BROKER_DEFAULT fallback too permissive

**Before:**
```python
return self._fill_policy_codes.get(FillPolicy.RETURN_OR_PARTIAL, 0)  # silent RETURN
```
An unprovable fill mode was submitted as RETURN.

**After:** resolution is probe → first usable declared symbol policy → `None`.
`None` becomes `UNSUPPORTED_CAPABILITY` and **no order request is submitted**.

**Verdict:** REPAIRED (fail closed).

## D3 — Success carried UNKNOWN_BROKER_ERROR

**Before:**
```python
class OrderResult: error_category = BrokerErrorCategory.UNKNOWN_BROKER_ERROR
...
error_category = UNKNOWN_BROKER_ERROR if ok else ORDER_REJECTED
```
`ok == True` shipped with an error category.

**After:** `BrokerErrorCategory.NONE` is the success state; `submit_order()`
sets `NONE` on success and a meaningful category otherwise. The invariant is
frozen: `ok == True => error_category is NONE`.

**Verdict:** REPAIRED.

## Audit of other provider-specific values acting as universal defaults

| Value | Classification | Decision |
|---|---|---|
| 29-char comment limit | TB/OX_OBSERVED_BROKER_QUIRK | Moved into `MT5ExecutionProfile.max_comment_length`; generic default = no truncation (preserves ownership). |
| 12-hour clock plausibility | GENERIC_RUNTIME_POLICY | Unchanged (sanity bound, not broker truth). |
| retcode 0 success | TB/OX_OBSERVED_BROKER_QUIRK (0) / standard (10009) | Kept as a documented safe superset `{0, 10009}`. |
| fill code mapping (type_filling) | TB/OX_OBSERVED_BROKER_QUIRK | Replaced with module-derived standard mapping; Ox mapping via profile. |
| fill bits mapping (bit 4 → RETURN) | TB/OX_OBSERVED_BROKER_QUIRK | Standard default maps only FOK/IOC bits (bit 4 = BOC, unrepresentable); Ox bits via profile. |

See `QL_EXEC_R2_1_BROKER_QUIRK_AUDIT.csv` for the machine-readable table.
