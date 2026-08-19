"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR (SIDE SERVICE)
===========================================================

Independent end-of-week verification sidecar: given the COMPLETE M5 market
record for a week, what signals should the canonical TB engine have
generated, and did the live runtime account for every one?

Modules:
  tb_audit_core     frozen constants, outcome classes, deterministic ids
  tb_audit_data     raw-bar acquisition + completeness gates (fail closed)
  tb_audit_replay   TBWeeklyReplayEngine (independent canonical replay)
  tb_audit_live     read-only runtime readers, matching, data parity
  tb_audit_stats    historical weekly/monthly cadence + rolling activity
  tb_audit_report   artifact writer (JSON/MD/CSV/history)
  tb_weekly_audit   CLI: --week latest|YYYY-MM-DD, --month YYYY-MM
  tb_weekly_audit_tests  30-check deterministic suite

AUTHORITY:
  READ ONLY · DIAGNOSTIC ONLY · NO EXECUTION AUTHORITY · NO CAPITAL
  AUTHORITY · NO STRATEGY-MODIFICATION AUTHORITY.

It may reuse pure canonical science (engines.triangular_basis_live +
engines.tb_forward_config) but can never influence execution: no broker
calls, no runtime DB writes, no parameter changes.
"""
