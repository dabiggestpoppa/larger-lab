import sys; sys.path.insert(0, 'quant-lab/ml')
import tempfile
from pathlib import Path
import numpy as np
from phase2_classifier.entry_scorer import CerebusEntryScorer

scorer = CerebusEntryScorer()
np.random.seed(42)
X = np.random.randn(200, 8)
y = np.random.rand(200)
scorer.train(X, y)

with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
    tmp_path = Path(f.name)

scorer.save(tmp_path)
print(f'Saved to: {tmp_path}')
print(f'JSON exists: {tmp_path.with_suffix(".json").exists()}')
print(f'Scaler exists: {tmp_path.with_suffix(".scaler.pkl").exists()}')
print(f'Model exists: {tmp_path.exists()}')

scorer2 = CerebusEntryScorer()
scorer2.load(tmp_path)
print(f'is_trained: {scorer2.is_trained}')

features = {f: 0.5 for f in scorer2.feature_names}
result = scorer2.score_entry(features)
print(f'Score: {result}')
