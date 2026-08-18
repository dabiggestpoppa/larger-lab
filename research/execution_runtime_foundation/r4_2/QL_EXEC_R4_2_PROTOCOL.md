# QL-EXEC-R4.2 — TB Generic Runtime Live Shadow Canary — Protocol

Base: 62e6d0402a780d171a8b81c2070567045e341be7
Parent: QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN (PASS)

## Purpose

Implement and launch the FIRST LIVE-MARKET generic TB shadow canary:
consume live/read-only TB market observations (Option B export), produce
PRIMARY + CONTROL decisions, compare against legacy, persist isolated state,
survive restart, observe market close/reopen, emit parity telemetry — with
broker write calls == 0.

## Absolute rule

The generic path is INCAPABLE of broker writes. Four independent barriers;
any single configuration mistake cannot enable orders. A reachable write-
capable method => STOP, status BLOCKED_R4_2_ORDER_AUTHORITY_EXPOSED.

## What this checkpoint delivered

1. `ShadowRuntimeAuthority` (SHADOW_OBSERVE_ONLY; can_submit_new_risk=false)
2. `ReadOnlyBrokerSession` (write surface absent; denylist raises
   ShadowWriteForbiddenError)
3. `ShadowExecutionPlan` (hypothetical; never an executable OrderIntent)
4. Legacy export writer (additive; worker hook documented, NOT wired)
5. Shadow feed consumer (hash / seq / gap / corrupt / partial-line safe)
6. Frozen-tolerance live parity comparator (12 mismatch classes)
7. Isolated SQLite/WAL shadow store (shadow_state/tb-generic-shadow-g1/)
8. `tb_generic_shadow.py` process + `shadowctl`
9. Offline drill evidence (205 bars, 3280 EXACT verdicts, 0 mismatches,
   0 broker writes, restart + market-close drills)
10. Offline test gate: 380/380 pass (355 prior + 25 R4.2)

## Status: RUNNING_SHADOW_WAITING_EVIDENCE

Live observation has NOT accumulated: the live canary requires (a) operator
enablement of the legacy exporter hook and (b) manual `shadowctl start`
against the live export. Live counters are truthfully 0; the frozen evidence
rule (1000 bars / 5 days / drills / natural signals) is NOT satisfied. This
checkpoint does NOT claim PASS.
