#!/usr/bin/env python
"""MECH-5 plots: failure anatomy, divergence timing, hazards, motifs."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

def fig():
    plt.figure(figsize=(8, 5))

# 1. First divergence timing
fig()
s = pd.read_csv(ROOT / "04_FIRST_DIVERGENCE_SUMMARY.csv")
labels = [l.replace("top500_", "").replace("_30d", "30").replace("_7d", "7")[:22] for l in s.variable]
rstat = s.rank_biserial_r
plt.barh(range(len(rstat)), rstat, color="steelblue")
plt.yticks(range(len(rstat)), labels)
plt.xlabel("rank-biserial r (success vs failure)")
plt.title("MECH-5: Earliest Divergence Variables (first significant horizon)")
plt.tight_layout(); plt.savefig(PLOTS / "01_first_divergence_r.png", dpi=110); plt.close()

# 2. Incremental model AUC
fig()
m = pd.read_csv(ROOT / "05_SUCCESS_FAILURE_INCREMENTAL_MAP.csv")
plt.plot(range(len(m)), m.cv_auc, "o-", color="darkorange")
plt.xticks(range(len(m)), [x.replace("M6_chain_sector","M6").replace("M5_timing","M5").replace("M4_conc_btc_eth","M4").replace("M3_rank_participation","M3").replace("M2_volatility","M2").replace("M1_breadth","M1").replace("M0_current_state","M0") for x in m.model], rotation=30)
plt.ylabel("5-fold CV AUC"); plt.xlabel("incremental model block")
plt.title("MECH-5: Success vs Failure Incremental Weight Map")
plt.grid(alpha=0.3); plt.tight_layout(); plt.savefig(PLOTS / "02_incremental_auc.png", dpi=110); plt.close()

# 3. Escape / propagation / failure hazards
e = pd.read_csv(ROOT / "08_ESCAPE_HAZARD.csv")
p = pd.read_csv(ROOT / "09_PROPAGATION_HAZARD.csv")
f = pd.read_csv(ROOT / "10_FAILURE_HAZARD.csv")
fig()
plt.plot(e.horizon_d, e.p_escape, "o-", label="escape P(not reentry)")
plt.plot(p.horizon_d, p.p_sustained_within_h, "o-", label="propagation P(sustained)")
plt.plot(f.horizon_d, f.p_reentry_within_h, "s--", label="failure P(reentry)")
plt.xlabel("horizon (days)"); plt.ylabel("cumulative probability")
plt.title("MECH-5: Two-Clock Escape/Propagation/Failure Hazards")
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout(); plt.savefig(PLOTS / "03_two_clock_hazards.png", dpi=110); plt.close()

# 4. Failure motifs
fig()
mf = pd.read_csv(ROOT / "16_FAILURE_MOTIF_AUDIT.csv").sort_values("count", ascending=False)
plt.bar(mf.motif, mf["count"], color="crimson")
plt.xticks(rotation=35, ha="right")
plt.ylabel("episodes"); plt.title("MECH-5: Failure Motif Distribution (n=125)")
plt.tight_layout(); plt.savefig(PLOTS / "04_failure_motifs.png", dpi=110); plt.close()

# 5. Conditional rescue
fig()
r = pd.read_csv(ROOT / "17_CONDITIONAL_RESCUE_AUDIT.csv")
plt.bar(r.condition, r.p_success * 100, color="seagreen")
plt.axhline(r.p_success_overall.iloc[0] * 100, color="black", ls="--", label="overall")
plt.xticks(rotation=45, ha="right")
plt.ylabel("success %"); plt.title("MECH-5: Success Rate by Regime State (bars) vs overall (dashed)")
plt.legend(); plt.tight_layout(); plt.savefig(PLOTS / "05_conditional_rescue.png", dpi=110); plt.close()

# 6. Signals to termination latency
fig()
lat = pd.read_csv(ROOT / "14_SIGNAL_TO_TERMINATION_LATENCY.csv")
plt.barh(lat.variable, lat.median_latency_d, color="rebeccapurple")
plt.xlabel("median days before termination that decline starts")
plt.title("MECH-5: Signal-to-Termination Latency")
plt.tight_layout(); plt.savefig(PLOTS / "06_termination_latency.png", dpi=110); plt.close()

print("plots written to", PLOTS)
print(sorted(p.name for p in PLOTS.glob("*.png")))
