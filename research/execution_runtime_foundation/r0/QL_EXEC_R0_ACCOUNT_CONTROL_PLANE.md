# QL_EXEC_R0_ACCOUNT_CONTROL_PLANE

The major architectural addition beyond TB Forward: explicit account objects and a control plane that binds strategies and capital policy to accounts before any execution translation.

```
                 OCE / QUANT LAB
                        │
                        ▼
               ACCOUNT CONTROL PLANE
                        │
         ┌──────────────┴──────────────┐
         │                             │
   STRATEGY REGISTRY             ACCOUNT REGISTRY
         │                             │
         └──────────────┬──────────────┘
                        ▼
                   CAPITAL POLICY
                        │
                        ▼
                    ACCOUNT ROUTER
                        │
                        ▼
                  RUNTIME INSTANCE
```

---

## 1. Design principles

1. **A config row is not trading authority.** The registry distinguishes configured / reachable / authenticated / identity-matched / execution-enabled. Only an identity-matched, execution-enabled account may receive risk.
2. **No plaintext credentials.** The registry stores secret references, never broker passwords, API secrets, tokens, or private keys.
3. **Binding precedes notional.** `account_id` and account equity are known before any dollar/notional translation.
4. **One runtime process per directly controlled broker account** is the preferred default (crash/connection/account-state isolation, simple reconciliation, clear credential scope).
5. **Ownership and resource truth are separate.** Foreign/manual positions may consume margin/equity but are never claimed as strategy PnL, and ambiguous foreign positions block new risk.

---

## 2. AccountRegistry

Logical store of execution accounts. Fields per `QL_EXEC_R0_ACCOUNT_REGISTRY_SCHEMA.json`. Truth states are modeled explicitly:

- `CONFIGURED` — row exists; nothing proven.
- `CONNECTING` — broker connection in progress.
- `CONNECTED` — transport connected.
- `IDENTITY_MISMATCH` / `AUTH_FAILED` — identity gate failed; EXECUTION BLOCKED.
- `WAITING_FOR_BROKER` — terminal/session not available.
- `MARKET_CLOSED` — connected but no market.
- `RECONCILING` — broker vs ledger reconciliation in progress.
- `READY` — identity matched, reconciled, execution-enabled.
- `BLOCKED` / `DEGRADED` / `STOPPED` — fail-closed or operator-stopped.

`CONNECTED` is never conflated with `READY`. Identity gate (broker/provider, server, login/account id, environment, account currency, account mode) must pass before broker authority is enabled; any mismatch → EXECUTION BLOCKED.

---

## 3. Account roles (conceptually frozen; not one-strategy-one-account)

- **EXCLUSIVE_STRATEGY_MASTER** — one strategy owns one execution account (TB master, Rekey master, P90 master). Isolation, simple reconciliation, copier-master use.
- **PORTFOLIO_MASTER** — multiple explicitly approved strategies share one account under ONE capital routing policy (the Capital Routing A/B motivating case). Requires one authoritative shared heat ledger.
- **FOLLOWER / MIRROR** — account receives trades from an external copier. Out of current execution authority; observability only (`copier_role = FOLLOWER`).

---

## 4. PortfolioGroup

Describes strategies sharing one capital policy/account. Prevents account structure from silently changing Capital Routing science. Fields per `QL_EXEC_R0_PORTFOLIO_GROUP_SCHEMA.json`. For a PORTFOLIO_MASTER, either one runtime hosts multiple strategy adapters under one portfolio authority, or multiple strategy producers feed one account-runtime/capital-router service. R0 recommends the **single account-runtime hosting multiple strategy adapters under one portfolio authority** as the simplest truthful design (one shared heat ledger, one account-state snapshot, no cross-process heat race).

---

## 5. StrategyAccountBinding

The authority for where and how a strategy executes. Replaces hardcoded per-worker constants. Fields per `QL_EXEC_R0_STRATEGY_ACCOUNT_BINDING_SCHEMA.json`. A binding is only `enabled` when its account is identity-matched and execution-enabled, its strategy is approved, and its portfolio group admits heat.

---

## 6. RuntimeProfile

Distinguishes MACHINE PROFILE (local_windows / windows_vps) from RUNTIME PROFILE (runtime_id, strategy adapter, account binding, broker profile, capital policy, state/log/ledger paths, telemetry identity, generation, ownership namespace, execution mode). One generic worker is launchable as many runtime instances. Fields per `QL_EXEC_R0_RUNTIME_PROFILE_SCHEMA.json`.

---

## 7. Account routing vs execution routing vs capital routing (three layers)

- **ACCOUNT ROUTING** answers: WHERE should this approved event run? (account_id, role validation, account-state snapshot, equity)
- **CAPITAL ROUTING** answers: HOW MUCH portfolio heat may this event receive? (family, f_total, allocation weight, requested_f, H1 admission)
- **BROKER EXECUTION** answers: HOW do I submit this order to that provider? (BrokerSession)

The execution substrate consumes an approved capital decision; it never recomputes A/B family, weights, f_total, or H1.

---

## 8. MT5 terminal / session identity

Multi-account support must model terminal path/identity, login/session, broker server, account identity, and process binding explicitly. Multiple MT5 accounts may not safely share one implicit global terminal state; account/terminal matching fails closed.
