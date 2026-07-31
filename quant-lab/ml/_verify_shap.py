import pandas as pd
df = pd.read_csv('quant-lab/ml/shap/feature_importance_fixed.csv')
print('Top 10 SHAP (KernelExplainer):')
for _, row in df.head(10).iterrows():
    print(f'  #{int(row["rank"])} {row["feature"]}: {row["mean_abs_shap"]:.4f}')
print()
r = df[df['feature']=='dist_to_132_pips']['rank'].values
print(f'dist_to_132_pips rank: {int(r[0]) if len(r)>0 else "N/A"}')
