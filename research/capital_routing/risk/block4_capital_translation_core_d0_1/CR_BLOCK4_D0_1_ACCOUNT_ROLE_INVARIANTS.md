# CR-BLOCK4-D0.1 -- Account-Role / Portfolio Topology Invariants

## Canonical A+B book requires ONE shared portfolio capital authority
The sealed A+B portfolio (A1_70_30 + H1-1.00-REJ) was scientifically
validated with shared A/B allocation, shared H1 gross simultaneous heat, and
ONE portfolio capital authority. Representing A events on one independent
account + B events on another independent account would CHANGE the portfolio
science (independent heat ledgers are NOT equivalent to the sealed shared-H1
portfolio).

## Gate (science R1.1, canonical A/B universe)
- account_role must be **PORTFOLIO_MASTER** (required role)
- portfolio_group_id must be non-empty (the shared portfolio binding)
- EXCLUSIVE_STRATEGY_MASTER / FOLLOWER / MIRROR / unknown role -> rejected
  (PortfolioAuthorityMismatchError / InvalidAccountRoleError)

The core validates the SUPPLIED AccountBindingReference only. The account
control plane (execution-runtime-foundation) decides WHICH group; D0.1
verifies that a shared portfolio binding exists and is authoritative.
Splitting the H1 ledger across independent workers is explicitly NOT
equivalent to the sealed portfolio.
