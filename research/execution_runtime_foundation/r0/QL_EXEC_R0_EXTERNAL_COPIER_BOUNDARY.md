# QL_EXEC_R0_EXTERNAL_COPIER_BOUNDARY

---

## 1. Boundary

Larger Lab does NOT build a copy-trading engine. Follower replication is outside current execution authority.

The registry may store `copier_role = MASTER` or `FOLLOWER` for observability only. Larger Lab may directly control a COPIER MASTER (e.g. TB master account → external copier → funded follower accounts); the external copier itself remains outside the authority boundary.

---

## 2. What is in scope

- Observability of the master account (normal runtime telemetry, PnL ownership).
- Recording that an account is a master for an external copier.

## 3. What is out of scope

- Replicating follower orders.
- Validating follower fills or positions.
- Claiming follower PnL.
- Managing follower risk.

---

## 4. Follower risk is NOT master risk

Follower accounts are not economically identical. Differences may include equity, leverage, minimum quantity, spread, commission, broker, latency, symbol naming, and market availability.

Therefore: **MASTER execution validation != FOLLOWER risk validation**. A clean master fill does not imply a safe follower fill. This distinction is recorded here and must never be collapsed in later checkpoints.
