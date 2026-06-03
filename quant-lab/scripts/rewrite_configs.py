"""
Rewrite asset_configs.py cleanly with K-Means calibrated values.
"""
import json, subprocess
from pathlib import Path

REPO = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
KM_FILE = REPO / "reports" / "tier_discovery_all.json"
CFG_FILE = REPO / "configs" / "asset_configs.py"

with open(KM_FILE, encoding='utf-8') as f:
    km = json.load(f)

NEW_PAIRS = ['EURGBP','EURJPY','EURAUD','EURNZD','EURCHF','EURCAD',
             'USDCAD','AUDJPY','AUDNZD','AUDCHF','AUDCAD','NZDJPY',
             'NZDCHF','NZDCAD','CADJPY','CADCHF','GBPCAD']

with open(CFG_FILE, encoding='utf-8') as f:
    content = f.read()

# Find markers
new_marker = "# FOREX CROSSES (NEW"
idx_new = content.find(new_marker)
metals_marker = "# METALS"
idx_metals = content.find(metals_marker, idx_new)

print(f"NEW at {idx_new}, METALS at {idx_metals}")

header = content[:idx_new]

# Find start of METALS section (include the divider comment)
footer_start = idx_metals
while footer_start > 0 and content[footer_start-1:footer_start] != '\n':
    footer_start -= 1
# Include the divider before METALS
div_idx = content.rfind("# ────", 0, footer_start)
if div_idx > idx_new:
    footer_start = div_idx
footer = "\n" + content[footer_start:]

# Generate new blocks
blocks = []
for sym in NEW_PAIRS:
    d = km[sym]
    t1, t2, t3 = d['T1'], d['T2'], d['T3']
    pip = 0.01 if 'JPY' in sym else 0.0001
    block = (
        f'    "{sym}": {{\n'
        f'        "name": "{sym[:3]}/{sym[3:]}",\n'
        f'        "pip_value": {pip},\n'
        f'        "k_factor": 0.48,\n'
        f'        "sl_method": "OCC_EXACT",\n'
        f'        "tiers": {{\n'
        f'            "T1": {{"ar_max": {t1["range_max"]}, "au": {t1["au"]}, "trigger": {t1["trig"]}}},\n'
        f'            "T2": {{"ar_max": {t2["range_max"]}, "au": {t2["au"]}, "trigger": {t2["trig"]}}},\n'
        f'            "T3": {{"ar_max": {t3["range_min"]}, "au": {t3["au"]}, "trigger": {t3["trig"]}}},\n'
        f'        }},\n'
        f'        "gear_shifts": {{\n'
        f'            "T1": [({t1["trig"]}, "T2"), ({t2["trig"]}, "T3")],\n'
        f'            "T2": [({t2["trig"]}, "T3")],\n'
        f'        }},\n'
        f'        "p90_threshold": {round(t1["au"] * 0.48, 2)},\n'
        f'        "fixed_tp": {round(t1["au"] * 2.0, 1)},\n'
        f'    }},\n'
    )
    blocks.append(block)

new_content = header
new_content += "# ─────────────────────────────────────────────────────\n"
new_content += "# FOREX CROSSES (NEW — fetched 2026-06-03)\n"
new_content += "# K-Means calibrated with percentile capping (T1<p75, T3<p95)\n"
new_content += "# ─────────────────────────────────────────────────────\n"
for b in blocks:
    new_content += b
new_content += footer

with open(CFG_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verify syntax
result = subprocess.run(
    ['python', '-c', f'import ast; ast.parse(open(r"{CFG_FILE}", encoding="utf-8").read())'],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"OK: {len(NEW_PAIRS)} K-Means configs written. Syntax valid.")
else:
    print(f"SYNTAX ERROR: {result.stderr}")
