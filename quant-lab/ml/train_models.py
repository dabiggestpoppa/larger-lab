"""Train XGBoost regime classifiers on all 18 assets. Fast version."""
import sys, numpy as np, pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "phase2_classifier"))
from regime_classifier import CerebusRegimeClassifier, FEATURE_NAMES

MODELS_DIR = Path(__file__).parent / "models"
FEATURES_DIR = Path(__file__).parent / "data" / "features"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def load_features(symbol):
    path = FEATURES_DIR / f"{symbol}_features.parquet"
    return pd.read_parquet(path) if path.exists() else None

def generate_labels(df):
    labels = np.zeros(len(df), dtype=int)
    if "vol_ratio" in df.columns and "hour_est" in df.columns:
        for i in range(len(df)):
            vol = df["vol_ratio"].iloc[i] if not pd.isna(df["vol_ratio"].iloc[i]) else 1.0
            hour = df["hour_est"].iloc[i] if not pd.isna(df["hour_est"].iloc[i]) else 6
            if vol > 1.2 and 5 <= hour <= 10: labels[i] = 0
            elif vol > 0.8 and 4 <= hour <= 11: labels[i] = 1
            elif vol < 0.5 or hour > 11: labels[i] = 3
            else: labels[i] = 2
    return labels

def train_symbol(symbol, df, labels):
    for f in FEATURE_NAMES:
        if f not in df.columns: df[f] = 0.0
    X = df[FEATURE_NAMES].values
    y = labels
    valid = ~np.isnan(X).any(axis=1)
    X, y = X[valid], y[valid]
    if len(X) < 100: return None
    n = len(X)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    val_valid = ~np.isnan(X_val).any(axis=1)
    X_val, y_val = X_val[val_valid], y_val[val_valid]
    test_valid = ~np.isnan(X_test).any(axis=1)
    X_test, y_test = X_test[test_valid], y_test[test_valid]
    clf = CerebusRegimeClassifier()
    clf.model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    clf.is_trained = True
    train_acc = clf.model.score(X_train, y_train)
    test_acc = clf.model.score(X_test, y_test) if len(X_test) > 0 else 0
    save_path = MODELS_DIR / f"regime_{symbol}.pkl"
    clf.save(save_path)
    print(f"  [{symbol}] Train={train_acc:.1%} | Test={test_acc:.1%} | N={len(X)}")
    return {"symbol": symbol, "train_accuracy": train_acc, "test_accuracy": test_acc, "samples": len(X)}

def main():
    print("=" * 60)
    print("TRAIN XGBoost Regime Classifiers")
    print("=" * 60)
    feature_files = sorted(FEATURES_DIR.glob("*_features.parquet"))
    symbols = [f.stem.replace("_features", "") for f in feature_files]
    print(f"Found {len(symbols)} symbols")
    results = []
    for symbol in symbols:
        df = load_features(symbol)
        if df is None or len(df) < 200: continue
        print(f"[{symbol}] Training...")
        labels = generate_labels(df)
        result = train_symbol(symbol, df, labels)
        if result: results.append(result)
    if results:
        avg_train = np.mean([r["train_accuracy"] for r in results])
        avg_test = np.mean([r["test_accuracy"] for r in results])
        print(f"\n=== COMPLETE: {len(results)}/{len(symbols)} trained ===")
        print(f"Avg Train: {avg_train:.1%} | Avg Test: {avg_test:.1%}")
        pd.DataFrame(results).to_csv(Path(__file__).parent / "data" / "phase2_results.csv", index=False)

if __name__ == "__main__":
    main()
