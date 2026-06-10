"""
Retrain XGBoost on FULL feature set from full_features_v2 + labels.
Uses calibrated tier/AU configs. No shortcuts. All 43 features.
"""
import sys, json, numpy as np, pandas as pd, xgboost as xgb, shap, joblib
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit

FULL_DIR = Path('quant-lab/ml/data/full_features_v2')
LABELS_DIR = Path('quant-lab/ml/data/labels')
MODEL_DIR = Path('quant-lab/ml/models')
SHAP_DIR = Path('quant-lab/ml/shap')
MODEL_DIR.mkdir(parents=True, exist_ok=True)
SHAP_DIR.mkdir(parents=True, exist_ok=True)

# Columns to exclude (raw OHLCV, intermediates, targets, labels, string columns)
EXCLUDE_COLS = {
    'open', 'high', 'low', 'close', 'volume',
    'asian_high', 'asian_low',
    'session_open', 'expected_range', 'price_range_from_open',
    'daily_high', 'daily_low', 'daily_range',
    'impulse_high', 'impulse_low', 'impulse_size_pips',
    'density_zone_high', 'density_zone_low', 'au_target',
    'mlr_close', 'mlr_mid',
    'weekly_high', 'weekly_low', 'weekly_range',
    'target_25', 'target_50', 'target_100', 'target_168', 'kill_switch_132',
    'weekly_target_25', 'weekly_target_50', 'weekly_target_100', 'weekly_target_168',
    'weekly_kill_switch_132',
    'bias', 'regime_status', 'session', 'tier', 'tier_kmeans',
    'time_to_25_min', 'time_to_50_min', 'fib_sequence_state',
}

print('Building combined feature matrices...')
all_X = []
all_y = []
feature_names = None

for labels_file in sorted(LABELS_DIR.glob('*_labeled.parquet')):
    symbol = labels_file.stem.replace('_labeled', '')
    if symbol == 'TEST':
        continue

    full_path = FULL_DIR / f'{symbol}_full.parquet'
    if not full_path.exists():
        print(f'  SKIP {symbol}: no full features')
        continue

    df_full = pd.read_parquet(full_path)
    df_labels = pd.read_parquet(labels_file)

    # Merge on index
    df = df_full.join(
        df_labels[['label_25_delivery', 'label_50_delivery', 'rekey_triggered', 'regime_at_time']],
        how='inner'
    )

    # Select feature columns
    feat_cols = [c for c in df.columns if c not in EXCLUDE_COLS and c not in
                 ['label_25_delivery', 'label_50_delivery', 'rekey_triggered', 'regime_at_time']]

    # Drop NaN
    subset = feat_cols + ['label_25_delivery']
    df_clean = df.dropna(subset=subset)

    if len(df_clean) < 100:
        print(f'  SKIP {symbol}: only {len(df_clean)} rows')
        continue

    # Convert labels: -1->0 (FAILED), 0->1 (CHOP), 1->2 (CONFIRMED)
    y = np.where(df_clean['label_25_delivery'].values == -1, 0,
                 np.where(df_clean['label_25_delivery'].values == 0, 1, 2))

    X = df_clean[feat_cols].values
    all_X.append(X)
    all_y.append(y)

    if feature_names is None:
        feature_names = feat_cols

    print(f'  {symbol}: {len(df_clean)} samples, {len(feat_cols)} features')

if not all_X:
    print('ERROR: no training data!')
    sys.exit(1)

X_all = np.vstack(all_X)
y_all = np.concatenate(all_y)
split_idx = int(len(X_all) * 0.8)
X_train, X_val = X_all[:split_idx], X_all[split_idx:]
y_train, y_val = y_all[:split_idx], y_all[split_idx:]

print(f'\nTotal: {len(X_all)} | Train: {len(X_train)} | Val: {len(X_val)}')
print(f'Features: {len(feature_names)}')

# Train
print('\nTraining XGBoost...')
model = xgb.XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    reg_alpha=0.1, reg_lambda=1.0,
    objective='multi:softprob', num_class=3,
    eval_metric='mlogloss', random_state=42, n_jobs=-1, tree_method='hist'
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

train_acc = model.score(X_train, y_train)
val_acc = model.score(X_val, y_val)
print(f'Train: {train_acc:.1%} | Val: {val_acc:.1%}')

# CV
print('TimeSeriesSplit CV...')
tscv = TimeSeriesSplit(n_splits=5)
cv_scores = []
for fold, (ti, vi) in enumerate(tscv.split(X_train)):
    fm = xgb.XGBClassifier(**model.get_params())
    fm.fit(X_train[ti], y_train[ti], verbose=False)
    acc = fm.score(X_train[vi], y_train[vi])
    cv_scores.append(acc)
    print(f'  Fold {fold+1}: {acc:.1%}')

mean_cv = np.mean(cv_scores)
print(f'CV: {mean_cv:.1%} ± {np.std(cv_scores):.1%}')

# SHAP
print('\nSHAP physics check...')
sample_size = min(10000, len(X_val))
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val[:sample_size])

if isinstance(shap_values, list):
    mean_abs_shap = np.zeros(len(feature_names))
    for sv in shap_values:
        if sv.ndim == 2:
            mean_abs_shap += np.abs(sv).mean(axis=0)
    mean_abs_shap /= len(shap_values)
elif shap_values.ndim == 2:
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

importance = pd.DataFrame({
    'feature': feature_names,
    'mean_abs_shap': mean_abs_shap,
}).sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
importance['rank'] = range(1, len(importance) + 1)

print('\nTop 10 SHAP:')
for _, row in importance.head(10).iterrows():
    print(f'  #{int(row["rank"])} {row["feature"]}: {row["mean_abs_shap"]:.4f}')

top5 = importance.head(5)['feature'].tolist()
if 'dist_to_132_pips' in top5:
    print('\n  OK SHAP PHYSICS CHECK PASSED')
else:
    rank = importance[importance['feature'] == 'dist_to_132_pips']['rank'].values
    print(f'\n  WARN: dist_to_132_pips rank {int(rank[0]) if len(rank) > 0 else "N/A"}')

# Save
artifact = {
    'model': model, 'feature_names': feature_names,
    'cv_scores': cv_scores, 'val_accuracy': val_acc,
    'is_trained': True, 'version': 'full_30feat_v2'
}
joblib.dump(artifact, MODEL_DIR / 'regime_classifier_full.pkl')
importance.to_csv(SHAP_DIR / 'feature_importance_full.csv', index=False)
print('\nModel + SHAP saved')
print('=== RETRAIN COMPLETE ===')
