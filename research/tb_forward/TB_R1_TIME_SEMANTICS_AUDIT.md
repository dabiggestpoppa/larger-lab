# TB-R1 — TIME / SESSION SEMANTICS AUDIT

Canonical research uses **fixed UTC−5** for EST (no DST). The prior live stack uses the same
convention in two places, consistently.

| Layer | Transformation | UTC−5 fixed? |
|---|---|---|
| canonical engine `_est_hour` | `(ts.hour - 5) % 24` | ✅ yes |
| data feed `_est_hour` | `dt - timedelta(hours=5)` then `.hour` | ✅ yes |
| data feed `_mt5_time_to_datetime` | `datetime.utcfromtimestamp(raw_time)` | ✅ (UTC) |
| executor heartbeat | `datetime.utcnow().isoformat()` | ✅ (UTC) |

## Timestamp roles table

| Timestamp | Semantics |
|---|---|
| canonical research timestamp | naive UTC bar time, EST = hour−5 |
| broker timestamp | MT5 `raw.time` Unix epoch → `utcfromtimestamp` (UTC) |
| runtime timestamp | `datetime.utcnow()` (UTC) for heartbeat/log |
| session-classification timestamp | the M5 bar's UTC timestamp fed to `_est_hour` (UTC−5) |

## Verdict

**Consistent fixed UTC−5 across canonical and live paths** — no DST, no US/Eastern, no
broker-local, no naive-`datetime.now()` used for session classification. This is a known
**parity landmine that is currently NOT triggered**. Classification: **session_time_layer =
ADOPT_AS_IS**. R3/R8 must preserve fixed UTC−5 (do not "correct" DST in this program).
