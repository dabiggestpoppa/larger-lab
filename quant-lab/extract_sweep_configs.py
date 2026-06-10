import json

sweep_files = [
    "reports/trigger_sweep_max_accuracy.json",
    "reports/trigger_sweep_forex_full.json",
    "reports/trigger_sweep_usd.json",
    "reports/trigger_sweep_gbp.json",
    "reports/trigger_sweep_chf.json",
    "reports/trigger_sweep_cad.json",
    "reports/trigger_sweep_nzd.json",
    "reports/trigger_sweep_remaining_eur.json",
    "reports/trigger_sweep_metals_indices.json",
    "reports/trigger_sweep_crypto.json",
]

all_configs = {}
for f in sweep_files:
    try:
        data = json.load(open(f))
        for pair, points in data.items():
            if isinstance(points, list) and len(points) > 0:
                floor = points[0]
                ceiling = None
                knee = None
                max_pf = 0
                for p in points:
                    if p.get("tr_per_day", 0) >= 0.5:
                        ceiling = p
                    if p.get("pf", 0) > max_pf:
                        max_pf = p.get("pf", 0)
                        knee = p
                if pair not in all_configs:
                    all_configs[pair] = {}
                all_configs[pair]["floor"] = floor
                all_configs[pair]["ceiling"] = ceiling
                all_configs[pair]["knee"] = knee
                all_configs[pair]["all_points"] = points
    except Exception as e:
        print(f"Error reading {f}: {e}")

print(f"Pairs with sweep configs: {len(all_configs)}")
for pair in sorted(all_configs.keys()):
    cfg = all_configs[pair]
    f = cfg.get("floor", {}) or {}
    c = cfg.get("ceiling", {}) or {}
    k = cfg.get("knee", {}) or {}
    n = len(cfg.get("all_points", []))
    f_trig = f.get("t1_trigger", 0)
    f_wr = f.get("wr", 0)
    c_trig = c.get("t1_trigger", 0) if c else 0
    c_wr = c.get("wr", 0) if c else 0
    k_trig = k.get("t1_trigger", 0) if k else 0
    k_pf = k.get("pf", 0) if k else 0
    print(f"  {pair}: {n} pts | Floor T1={f_trig:.1f} WR={f_wr:.1f}% | Ceiling T1={c_trig:.1f} WR={c_wr:.1f}% | Knee T1={k_trig:.1f} PF={k_pf:.2f}")

# Save structured config
output = {}
for pair, cfg in all_configs.items():
    output[pair] = {
        "floor": {
            "t1_trigger": cfg["floor"].get("t1_trigger"),
            "wr": cfg["floor"].get("wr"),
            "pf": cfg["floor"].get("pf"),
            "tr_per_day": cfg["floor"].get("tr_per_day"),
            "trades": cfg["floor"].get("trades"),
        },
        "ceiling": {
            "t1_trigger": cfg["ceiling"].get("t1_trigger") if cfg["ceiling"] else None,
            "wr": cfg["ceiling"].get("wr") if cfg["ceiling"] else None,
            "pf": cfg["ceiling"].get("pf") if cfg["ceiling"] else None,
            "tr_per_day": cfg["ceiling"].get("tr_per_day") if cfg["ceiling"] else None,
        },
        "knee": {
            "t1_trigger": cfg["knee"].get("t1_trigger") if cfg["knee"] else None,
            "wr": cfg["knee"].get("wr") if cfg["knee"] else None,
            "pf": cfg["knee"].get("pf") if cfg["knee"] else None,
            "tr_per_day": cfg["knee"].get("tr_per_day") if cfg["knee"] else None,
        },
        "sweep_points": len(cfg["all_points"]),
    }

with open("reports/sweep_floor_ceiling_knee_configs.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved to reports/sweep_floor_ceiling_knee_configs.json")
