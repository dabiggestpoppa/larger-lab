import pickle
import numpy as np

m = pickle.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\ml\models\regime_EURUSD.pkl', 'rb'))
print(f"Type: {type(m)}")
print(f"Keys: {list(m.keys())}")
print(f"is_trained: {m.get('is_trained')}")
print(f"feature_names: {m.get('feature_names', [])[:3]}...")
print(f"cv_scores: {m.get('cv_scores', {})}")

# Test prediction
xgb_model = m['model']
print(f"\nXGB model type: {type(xgb_model).__name__}")
print(f"Has predict: {hasattr(xgb_model, 'predict')}")

# Dummy input
n_features = len(m['feature_names'])
X = np.zeros((1, n_features))
pred = xgb_model.predict(X)
print(f"Prediction for zeros: {pred}")

prob = xgb_model.predict_proba(X)
print(f"Probabilities: {prob}")
print(f"Classes: {xgb_model.classes_}")
