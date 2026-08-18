# QL-EXEC-R4.1 — Resource Budget (explicit upper bounds)

Observability load must not degrade active execution. Bounds are set before
deployment and measured during the shadow canary.

| Resource | Upper bound (G1) | Enforcement |
|----------|------------------|-------------|
| CPU (sustained) | <= 5% of one core averaged over 60 s | shadowctl status + OS sampling |
| Memory (RSS) | <= 256 MB | process self-check + OS sampling |
| Disk writes | <= 10 MB/hour | log/sqlite growth counter |
| Log size | <= 5 MB (rotation x5, matching TB policy) | log rotation |
| Poll frequency | once per synchronized common bar (plus heartbeat cadence) | scheduler throttle |
| Broker read rate | bounded by export cadence (no tight MT5 polling in G1) | read throttle |
| Heartbeat cadence | configurable, default 10 s | config |

## Measurement requirement

- Measure before deployment (baseline for the active stack with shadow OFF)
  and during deployment (with shadow ON).
- If any bound is exceeded, the shadow throttles or stops; it never degrades
  the active stack.
