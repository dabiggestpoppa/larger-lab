# B1-I2 Purchase-Hold Review Packet

**Date:** 2026-08-29
**Branch:** `oce-program-build` (long-lived implementation branch, created this session)
**Starting SHA:** `028fcdddd90f25c44996510426bd0c0e68bc54f5` (exact ratified planning head)
**Recommendation:** BLOCKED — awaiting operator purchase + sanitized host identity

---

## 1. What this packet is

The master program authorization (`AUTHORIZED_PROGRAM=OCE_FULL_PROGRAM_BUILD`) directs
resume-from-truthful-state. The truthful state is:

- B1-I1: RATIFIED / CHECKPOINTED (CI run 33010802229, evidence commit `3ee31b2a6`).
- B1-I0: decision research complete, purchase decision packet published.
- B1-I2: `AUTHORIZED_STAGE=B1-I2` received (netcup RS 4000 G12, monthly,
  first-month ≤ $100, monthly ≤ $60). Acceptance contract, schema, fixtures,
  host-baseline policy, execution runbook, and 19 host-free regressions are
  committed and pushed. **The host has not been purchased. No host identity
  has been supplied. Provisioning has not started.**

B2–B10 are LOCKED behind the B1-I9 block gate
(`OCE_FULL_PROGRAM_BUILD_ROADMAP_v1.0.md` §3: "B2 … LOCKED — dependency promoted
by B1 stable audit environment"; planning a downstream block does not promote
its dependency or authorize its build).

## 2. The exact hold

`runbooks/B1-I2-execution.md` §"Status: PURCHASE HOLD - do not provision yet":

> The host has not yet been purchased. Until the operator completes the purchase
> and supplies the sanitized host identity below, the agent must stop at the
> purchase hold and return these verified checkout requirements.

The master authorization's own hold-point list ("purchases" require explicit
operator approval; "A planning document or this master program authorization
does not satisfy those hold points") confirms: no agent action can clear this.
Purchasing is an operator-only action.

## 3. What the operator must do to unblock B1-I2

1. Purchase netcup RS 4000 G12 (monthly term, no add-ons) — checkout guards in
   the runbook §"Checkout guard checks (before buying)".
2. Reply with the ten sanitized, non-secret facts from the runbook §"Verified
   checkout requirements": provider, product, region, invoice total (no card
   numbers), term, server id, OS confirmation, public IP/hostname, MFA-on
   confirmation, SSH-public-key-registered confirmation.
3. Do **not** send: card details, passwords, MFA codes, recovery codes, private
   SSH keys, Tailscale reusable keys, or cloud API secrets.

Once those arrive, B1-I2 provisioning (ansible playbooks, host-free regressions
re-run, evidence pack) can proceed under the already-frozen acceptance contract.

## 4. What was done this session (no authority expanded)

- Verified preflight: repository `dabiggestpoppa/larger-lab`; planning head
  `028fcdd…` present on `origin/oce-full-program-planning-books-2-10`; `main`
  untouched at `7e7ef7222c4ecdea568b34583fd81406165cc9b6`; remote ref matches
  the ratified SHA exactly.
- Created `oce-program-build` from exactly `028fcdddd90f25c44996510426bd0c0e68bc54f5`
  in a sibling worktree (`../larger-lab-oce-build`), leaving the main checkout's
  unrelated uncommitted work (another thread's B1-I2 refinements + personal
  files) untouched.
- Reconciled the planning head vs. main-checkout divergence: `028fcdd` contains
  the B1-I1 implementation plus the B2–B10 planning dossiers; the main
  checkout's uncommitted B1-I2 file set is a superset with later refinements
  (extra gate-path regression, typography). Nothing was discarded; nothing was
  cherry-picked ahead of the hold.
- Read the ledger and checkpoint registry from the planning head; confirmed
  B1-I2 = BUILDING at purchase hold, B1-I3…I9 = LOCKED, Block 1 = IN PROGRESS.

## 5. Cost and cloud mutations to date

- Cloud mutations: 0
- Recurring cost: $0 (nothing purchased; the approved ceiling is ≤ $100 first
  month / ≤ $60 monthly, untouched)

## 6. What can safely continue in parallel (local-only, non-blocking)

Nothing in B2–B10 may start (dependency-gated). Local-only B1-I2 preparation
beyond what is already committed would either duplicate ratified work or
front-run provisioning; both are prohibited by the master authorization's
"do not repeat already ratified work merely to create new commits" and by the
purchase hold itself. The correct next action is the operator's.

## 7. Recommendation

**BLOCKED** — B1-I2 provisioning is ready to execute the moment the operator
completes the purchase and returns the sanitized host identity. No further
agent-side work is authorized or useful until then.

---

## 8. Disposition after OPERATOR DECISION `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED` (A-003)

This packet is preserved as **historical truth**. Its disposition is updated by
Amendment A-003 (2026-08-29):

| Fact | Value |
|---|---|
| purchase decision | researched |
| selected target | netcup RS 4000 G12 |
| purchase | **deferred by operator** |
| cost incurred | $0 |
| cloud mutations | 0 |
| future cloud activation | available through the gated activation contract (`oce-ctl deploy validate/plan/apply`, apply fails closed) |

Block 1 is reclassified into **B1-LOCAL** (active, default local runtime) and
**B1-CLOUD-ACTIVATION** (deferred, `DEFERRED_BY_OPERATOR`, not required for
B2–B10 local development). This hold no longer blocks local OCE development.
