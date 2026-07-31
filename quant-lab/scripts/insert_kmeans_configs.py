"""Insert K-Means calibrated configs into asset_configs.py"""
import json, subprocess
from pathlib import Path

REPO = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
KM_FILE = REPO / "reports" / "tier_discovery_all.json"
CFG_FILE = REPO / "configs" / "asset_configs.py"

with open(KM_FILE, encoding='utf-8') as f:
    km = json.load(f)

with open(CFG_FILE, encoding='utf-8') as f:
    lines = f.readlines()

# Find METALS section
metals_idx = None
for i, line in enumerate(lines):
    if "# METALS" in line:
        metals_idx = i
        break

if metals_idx is None:
    print("ERROR: METALS section not found")
    exit(1)

# Find divider before METALS
div_idx = metals_idx
while div_idx > 0 and "----" not in lines[div_idx - 1]:
    div_idx -= 1

print(f"METALS at line {metals_idx}, divider at {div_idx}")

NEW_PAIRS = ['EURGBP','EURJPY','EURAUD','EURNZD','EURCHF','EURCAD',
             'USDCAD','AUDJPY','AUDNZD','AUDCHF','AUDCAD','NZDJPY',
             'NZDCHF','NZDCAD','CADJPY','CADCHF','GBPCAD']

insert_lines = [
    "    # ─────────────────────────────────────────────────────\n",
    "    # FOREX CROSSES (NEW — fetched 2026-06-03)\n",
    "    # K-Means calibrated with percentile capping (T1<p75, T3<p95)\n",
    "    # ─────────────────────────────────────────────────────\n",
]

for sym in NEW_PAIRS:
    d = km[sym]
    t1, t2, t3 = d['T1'], d['T2'], d['T3']
    pip = 0.01 if 'JPY' in sym else 0.0001
    insert_lines += [
        f'    "{sym}": {{\n',
        f'        "name": "{sym[:3]}/{sym[3:]}",\n',
        f'        "pip_value": {pip},\n',
        f'        "k_factor": 0.48,\n',
        f'        "sl_method": "OCC_EXACT",\n',
        f'        "tiers": {{\n',
        f'            "T1": {{"ar_max": {t1["range_max"]}, "au": {t1["au"]}, "trigger": {t1["trig"]}}},\n',
        f'            "T2": {{"ar_max": {t2["range_max"]}, "au": {t2["au"]}, "trigger": {t2["trig"]}}},\n',
        f'            "T3": {{"ar_max": {t3["range_min"]}, "au": {t3["au"]}, "trigger": {t3["trig"]}}},\n',
        f'        }},\n',
        f'        "gear_shifts": {{\n',
        f'            "T1": [({t1["trig"]}, "T2"), ({t2["trig"]}, "T3")],\n',
        f'            "T2": [({t2["trig"]}, "T3")],\n',
        f'        }},\n',
        f'        "p90_threshold": {round(t1["au"] * 0.48, 2)},\n',
        f'        "fixed_tp": {round(t1["au"] * 2.0, 1)},\n',
        f'    }},\n',
    ]

new_lines = lines[:div_idx] + insert_lines + lines[div_idx:]

with open(CFG_FILE, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Verify syntax
result = subprocess.run(
    ['python', '-c', f'import ast; ast.parse(open(r"{CFG_FILE}", encoding="utf-8").read())'],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"OK: {len(NEW_PAIRS)} K-Means configs inserted. Total lines: {len(new_lines)}. Syntax valid.")
    for sym in NEW_PAIRS:
        d = km[sym]
        print(f"  {sym}: T1<{d['T1']['range_max']} | T2<{d['T2']['range_max']} | T3>{d['T3']['range_min']}")
else:
    print(f"SYNTAX ERROR: {result.stderr}")
