#!/usr/bin/env python
"""Generate 02_EVENT_COHORT_RECONCILIATION.csv for MECH-5."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
M4_OUT = ROOT.parent / "mech_4"

sys.path.insert(0, str(M4_OUT / "scripts"))
import alt_mech_4_analysis as M4

inp, tl = M4._cache_step("inputs", M4.load)
daily, d, bm = M4._cache_step("daily", lambda: M4.build_daily(inp))
rc = M4._cache_step("reconcile", lambda: M4.ws_reconcile(daily))
entries, exits = rc["recount"]["entries"], rc["recount"]["exits"]
rA = M4._cache_step("A", lambda: M4.ws_a(daily, entries, exits))
ledger = rA["ledger"]

ALT_FAMILY = M4.ALT_FAMILY
SUCCESS = {"BROAD_RISK_EXPANSION"} | ALT_FAMILY
FAILURE = {"BTC_CONCENTRATION", "MIXED_NO_CLEAR_ROUTE"}

dest_counts = ledger.first_destination.value_counts()
fm = pd.read_csv(M4_OUT / "33_FIRST_MOVE_TRUE_DELIVERY.csv")
fm_map = dict(zip(fm.event_id, fm.classification))
ledger["first_move_class"] = ledger.event_id.map(fm_map).fillna("NOT_ASSIGNED")

rows = []
for dest, cnt in dest_counts.items():
    family = ("SUCCESS" if dest in SUCCESS else "FAILURE" if dest in FAILURE else "OTHER")
    rows.append({"cohort": "canonical_destination", "label": dest, "count": int(cnt), "family": family})
rows.append({"cohort": "family", "label": "SUCCESS", "count": int(ledger.first_destination.isin(SUCCESS).sum()), "family": "SUCCESS"})
rows.append({"cohort": "family", "label": "FAILURE", "count": int(ledger.first_destination.isin(FAILURE).sum()), "family": "FAILURE"})
rows.append({"cohort": "family", "label": "OTHER", "count": int((~ledger.first_destination.isin(SUCCESS | FAILURE)).sum()), "family": "OTHER"})
for cls, cnt in ledger.first_move_class.value_counts().items():
    rows.append({"cohort": "first_move_class", "label": cls, "count": int(cnt), "family": "FIRST_MOVE"})
rows.append({"cohort": "total", "label": "ALL_EVENTS", "count": len(ledger), "family": "ALL"})

out = pd.DataFrame(rows)
out.to_csv(ROOT / "02_EVENT_COHORT_RECONCILIATION.csv", index=False)
print(out.to_string(index=False))
