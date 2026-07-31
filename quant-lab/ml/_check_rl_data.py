"""Check RL's latest data additions."""
import json
from pathlib import Path

# Check sweep configs
with open('quant-lab/data/holy_grail_extracted/sweep_configs_all.json') as f:
    configs = json.load(f)
print(f'Sweep configs: {len(configs)} assets')
for k in list(configs.keys())[:5]:
    v = configs[k]
    print(f'  {k}: {json.dumps(v)[:100]}')

# Check Markov chain model
markov_path = Path('quant-lab/ml/phase2_classifier/markov_chain_model.py')
if markov_path.exists():
    content = markov_path.read_text()
    print(f'\nMarkov chain model: {len(content)} lines')
    # Count classes/functions
    classes = [l.strip() for l in content.split('\n') if l.strip().startswith('class ')]
    funcs = [l.strip() for l in content.split('\n') if l.strip().startswith('def ')]
    print(f'  Classes: {len(classes)}')
    print(f'  Functions: {len(funcs)}')
    for c in classes[:5]:
        print(f'    {c}')

# Check training data files
train_dir = Path('quant-lab/ml/data/training')
files = sorted(train_dir.glob('*_training.parquet'))
print(f'\nTraining files: {len(files)}')
for f in files[:3]:
    import pandas as pd
    df = pd.read_parquet(f)
    print(f'  {f.stem}: {df.shape}')
