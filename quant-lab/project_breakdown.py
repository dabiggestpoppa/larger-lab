import pandas as pd, json
from pathlib import Path

print("=" * 70)
print("CEREBUS NEURO-SYMBOLIC SCANNER — FULL PROJECT BREAKDOWN")
print("=" * 70)

# 1. DATA FILES
print("\n\n=== 1. DATA FILES ===")
data_dirs = {
    "Raw OHLCV (clean)": "quant-lab/ml/data/clean",
    "Labels": "quant-lab/ml/data/labels",
    "Macro Features": "quant-lab/ml/data/macro_features",
    "Full Features v2": "quant-lab/ml/data/full_features_v2",
    "Holy Grail Raw": "quant-lab/data/holy_grail_extracted/raw_data",
    "Holy Grail Stats": "quant-lab/data/holy_grail_extracted/stats",
    "Unified Feature Store": "quant-lab/data/holy_grail_extracted/unified",
}
for name, d in data_dirs.items():
    p = Path(d)
    if p.exists():
        files = list(p.glob("*.parquet")) + list(p.glob("*.csv")) + list(p.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files) / 1024 / 1024
        print(f"\n  {name}: {d}")
        print(f"    Files: {len(files)}")
        print(f"    Size: {total_size:.1f} MB")
        for f in sorted(files)[:5]:
            print(f"      {f.name} ({f.stat().st_size/1024:.0f} KB)")
        if len(files) > 5:
            print(f"      ... and {len(files)-5} more")

# 2. ML MODELS
print("\n\n=== 2. ML MODELS ===")
model_dir = Path("quant-lab/ml/models")
if model_dir.exists():
    for f in model_dir.glob("*.pkl"):
        size = f.stat().st_size / 1024 / 1024
        print(f"  {f.name}: {size:.1f} MB")
    for f in model_dir.glob("*.json"):
        meta = json.load(open(f))
        print(f"  {f.name}:")
        for k, v in meta.items():
            if k != "model":
                print(f"    {k}: {v}")

# 3. SHAP IMPORTANCE
print("\n\n=== 3. SHAP FEATURE IMPORTANCE ===")
shap_dir = Path("quant-lab/ml/shap")
if shap_dir.exists():
    for f in shap_dir.glob("*.csv"):
        df = pd.read_csv(f)
        print(f"\n  {f.name}: {len(df)} features")
        print("  Top 10:")
        for _, row in df.head(10).iterrows():
            rank = int(row.get("rank", 0))
            feat = row["feature"]
            val = row["mean_abs_shap"]
            print(f"    #{rank} {feat}: {val:.4f}")

# 4. TESTS
print("\n\n=== 4. TEST SUITE ===")
test_dir = Path("quant-lab/ml/tests")
if test_dir.exists():
    test_files = list(test_dir.glob("test_*.py"))
    print(f"  Test files: {len(test_files)}")
    for f in sorted(test_files):
        lines = len(open(f).readlines())
        print(f"    {f.name}: {lines} lines")

# 5. DECISION TREES
print("\n\n=== 5. DECISION TREES & PLAYBOOKS ===")
dt_path = Path("quant-lab/data/holy_grail_extracted/all_decision_trees.json")
if dt_path.exists():
    dt = json.load(open(dt_path))
    print(f"  Sections: {len(dt)}")
    for key in dt:
        if isinstance(dt[key], dict) and "rows" in dt[key]:
            print(f"    {key}: {len(dt[key]['rows'])} rows")

# 6. FAILURE PATTERNS
print("\n\n=== 6. FAILURE PATTERN DATABASE ===")
fp_path = Path("quant-lab/ml/data/holy_grail_extracted/failure_pattern_database.csv")
if fp_path.exists():
    df = pd.read_csv(fp_path)
    print(f"  Total events: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Pattern types:")
    for k, v in df["Pattern_Type"].value_counts().items():
        print(f"    {k}: {v}")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Rekey rate: {df['Rekey_Occurred'].mean():.1%}")

# 7. MLR RESULTS
print("\n\n=== 7. MLR DIRECTIONAL BIAS RESULTS ===")
mlr_path = Path("quant-lab/mlr_validation/results/mlr_directional_bias_intraday.json")
if mlr_path.exists():
    mlr = json.load(open(mlr_path))
    print(f"  Pairs tested: {len(mlr)}")
    for pair in ["EURUSD", "USDCHF"]:
        if pair in mlr:
            r = mlr[pair]
            print(f"\n  {pair} (N={r['total']}, B={r['bias']['Bullish']}/S={r['bias']['Bearish']}):")
            for lvl in ["ext_25", "ext_50", "ext_100", "rekey"]:
                label = {"ext_25": "-25%", "ext_50": "-50%", "ext_100": "-100%", "rekey": "132% rekey"}[lvl]
                print(f"    {label}: {r[lvl]['rate']:.1f}% ({r[lvl]['hits']}/{r[lvl]['total']})")

# 8. CODE FILES
print("\n\n=== 8. CODE FILES ===")
code_dirs = {
    "Phase 1 (Data)": "quant-lab/ml/phase1_data",
    "Phase 2 (Models)": "quant-lab/ml/phase2_classifier",
    "Phase 4 (Integration)": "quant-lab/ml/phase4_integration",
    "Phase 5 (Hardening)": "quant-lab/ml/phase5_hardening",
    "ML Tests": "quant-lab/ml/tests",
    "Data Extraction": "quant-lab/data_extraction",
}
for name, d in code_dirs.items():
    p = Path(d)
    if p.exists():
        files = list(p.glob("**/*.py"))
        lines = sum(len(open(f).readlines()) for f in files)
        print(f"  {name}: {len(files)} files, {lines:,} lines")

print("\n\n=== END OF BREAKDOWN ===")
