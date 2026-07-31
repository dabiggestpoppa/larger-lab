"""Apply K-Means calibrated tier configs to asset_configs.py"""
import json, re
from pathlib import Path

REPO = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
KM_FILE = REPO / "reports" / "tier_discovery_all.json"
CFG_FILE = REPO / "configs" / "asset_configs.py"

with open(KM_FILE) as f:
    km = json.load(f)

with open(CFG_FILE) as f:
    content = f.read()

pairs = ['EURGBP','EURJPY','EURAUD','EURNZD','EURCHF','EURCAD',
         'USDCAD','AUDJPY','AUDNZD','AUDCHF','AUDCAD','NZDJPY',
         'NZDCHF','NZDCAD','CADJPY','CADCHF','GBPCAD']

ok = 0
for sym in pairs:
    d = km[sym]
    t1, t2, t3 = d['T1'], d['T2'], d['T3']
    pip = 0.01 if 'JPY' in sym else 0.0001

    block = f'''    "{sym}": {{
        "name": "{sym[:3]}/{sym[3:]}",
        "pip_value": {pip},
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {{
            "T1": {{"ar_max": {t1['range_max']}, "au": {t1['au']}, "trigger": {t1['trig']}}},
            "T2": {{"ar_max": {t2['range_max']}, "au": {t2['au']}, "trigger": {t2['trig']}}},
            "T3": {{"ar_max": {t3['range_min']}, "au": {t3['au']}, "trigger": {t3['trig']}}},
        }},
        "gear_shifts": {{
            "T1": [({t1['trig']}, "T2"), ({t2['trig']}, "T3")],
            "T2": [({t2['trig']}, "T3")],
        }},
        "p90_threshold": {round(t1['au'] * 0.48, 2)},
        "fixed_tp": {round(t1['au'] * 2.0, 1)},
    }},'''

    pat = f'    "{sym}"\\s*:\\s*\\{{.*?^\\s*\\}},'
    m = re.search(pat, content, re.DOTALL | re.MULTILINE)
    if m:
        content = content.replace(m.group(0), block)
        print(f"OK  {sym}: T1<{t1['range_max']} | T2<{t2['range_max']} | T3>{t3['range_min']}")
        ok += 1
    else:
        print(f"FAIL {sym}: placeholder not found")

with open(CFG_FILE, 'w') as f:
    f.write(content)

print(f"\nUpdated {ok}/{len(pairs)} configs in {CFG_FILE}")
