import pickle
from pathlib import Path

model_dir = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\ml\models')
pkl_files = sorted(model_dir.glob("regime_*.pkl"))

for f in pkl_files:
    m = pickle.load(open(f, 'rb'))
    t = type(m).__name__
    has_predict = hasattr(m, 'predict')
    has_model = hasattr(m, 'model')
    symbol = f.stem.replace('regime_', '')
    
    if isinstance(m, dict):
        keys = list(m.keys())[:5]
        print(f"{symbol:10s} | dict | keys={keys}")
    elif has_predict:
        print(f"{symbol:10s} | {t} | predict=YES | model={has_model}")
    else:
        print(f"{symbol:10s} | {t} | predict=NO | model={has_model}")
