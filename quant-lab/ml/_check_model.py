import joblib
from pathlib import Path
import pandas as pd

p = Path('quant-lab/ml/models/regime_classifier_full.pkl')
if p.exists():
    art = joblib.load(p)
    print('Model version:', art.get('version'))
    print('Val accuracy:', art.get('val_accuracy'))
    print('CV scores:', art.get('cv_scores'))
    print('Features:', len(art.get('feature_names', [])))
    sp = Path('quant-lab/ml/shap/feature_importance_full.csv')
    if sp.exists():
        imp = pd.read_csv(sp)
        print('\nTop 10 SHAP:')
        for _, row in imp.head(10).iterrows():
            n = int(row['rank'])
            f = row['feature']
            v = row['mean_abs_shap']
            print(f'  #{n} {f}: {v:.4f}')
        r22 = imp[imp['feature'] == 'dist_to_132_pips']
        if len(r22) > 0:
            print(f'\ndist_to_132_pips rank: {int(r22.iloc[0]["rank"])}')
else:
    print('Model not found')
