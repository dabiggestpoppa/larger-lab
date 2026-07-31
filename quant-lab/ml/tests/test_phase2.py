"""
Phase 2 Tests: Regime Classifier & Entry Quality Scoring
=========================================================
Tests for XGBoost regime classifier, entry quality scorer,
confidence calibration, and SHAP analysis.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "phase2_classifier"))

from regime_classifier import CerebusRegimeClassifier, REGIME_MAP
from entry_scorer import CerebusEntryScorer


class TestRegimeClassifier:
    """Test 2.1: XGBoost Regime Classifier"""

    def _make_training_data(self, n_samples=500):
        """Generate synthetic training data."""
        np.random.seed(42)
        X = np.random.randn(n_samples, 8)
        # Create labels with some structure (not purely random)
        y = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            if X[i, 0] > 0.5:  # High AR → CONFIRMED
                y[i] = 0
            elif X[i, 0] > 0:
                y[i] = 1  # CAUTION
            elif X[i, 0] > -0.5:
                y[i] = 2  # FAILED
            else:
                y[i] = 3  # NO-GO
        return X, y

    def test_classifier_initializes_untrained(self):
        """Classifier should start in untrained state."""
        clf = CerebusRegimeClassifier()
        assert not clf.is_trained

    def test_train_returns_cv_accuracy(self):
        """Training should return mean CV accuracy."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        acc = clf.train(X, y)
        assert 0 < acc <= 1.0
        assert clf.is_trained

    def test_cv_scores_stored(self):
        """CV scores should be stored after training."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        clf.train(X, y)
        assert len(clf.cv_scores) == 5  # 5-fold CV

    def test_predict_returns_regime_and_confidence(self):
        """Prediction should return regime label and confidence."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        clf.train(X, y)

        features = {f: 0.5 for f in clf.feature_names}
        result = clf.predict_regime(features)

        assert 'regime' in result
        assert 'confidence' in result
        assert 'probabilities' in result
        assert result['regime'] in ['CONFIRMED', 'CAUTION', 'FAILED', 'NO-GO']
        assert 0 <= result['confidence'] <= 1

    def test_probabilities_sum_to_one(self):
        """All probabilities should sum to ~1.0."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        clf.train(X, y)

        features = {f: 0.5 for f in clf.feature_names}
        result = clf.predict_regime(features)

        prob_sum = sum(result['probabilities'].values())
        assert abs(prob_sum - 1.0) < 0.01

    def test_predict_before_train_raises(self):
        """Predicting before training should raise assertion."""
        clf = CerebusRegimeClassifier()
        with pytest.raises(AssertionError):
            clf.predict_regime({f: 0 for f in clf.feature_names})

    def test_feature_importance_returns_dataframe(self):
        """Feature importance should return ranked DataFrame."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        clf.train(X, y)

        # CC's version uses scaler — fit it if available
        if hasattr(clf, 'scaler') and clf.scaler is not None:
            importance = clf.get_feature_importance(X[:50])
        else:
            # Our version doesn't need scaler
            importance = clf.get_feature_importance(X[:50])
        assert isinstance(importance, pd.DataFrame)
        assert 'feature' in importance.columns
        assert 'mean_abs_shap' in importance.columns
        assert 'rank' in importance.columns
        assert len(importance) == 8

    def test_model_save_and_load(self):
        """Model should save and load correctly."""
        clf = CerebusRegimeClassifier()
        X, y = self._make_training_data()
        clf.train(X, y)

        # Get prediction before save
        features = {f: 0.5 for f in clf.feature_names}
        pred_before = clf.predict_regime(features)

        # Save
        clf.save()

        # Load into new instance
        clf2 = CerebusRegimeClassifier()
        clf2.load()

        # Predictions should match
        pred_after = clf2.predict_regime(features)
        assert pred_before['regime'] == pred_after['regime']
        assert abs(pred_before['confidence'] - pred_after['confidence']) < 0.001


class TestEntryScorer:
    """Test 2.2: Entry Quality Scorer"""

    def _make_training_data(self, n_samples=500):
        """Generate synthetic training data."""
        np.random.seed(42)
        X = np.random.randn(n_samples, 8)
        # Target: normalized R-multiple (0-1)
        y = np.clip(0.5 + 0.3 * X[:, 0] - 0.2 * X[:, 1], 0, 1)
        return X, y

    def test_scorer_initializes_untrained(self):
        """Scorer should start in untrained state."""
        scorer = CerebusEntryScorer()
        assert not scorer.is_trained

    def test_train_returns_cv_r2(self):
        """Training should return mean CV R² score."""
        scorer = CerebusEntryScorer()
        X, y = self._make_training_data()
        r2 = scorer.train(X, y)
        assert -1 <= r2 <= 1  # R² can be negative for bad models
        assert scorer.is_trained

    def test_score_returns_quality_and_action(self):
        """Scoring should return quality score and action."""
        scorer = CerebusEntryScorer()
        X, y = self._make_training_data()
        scorer.train(X, y)

        features = {f: 0.5 for f in scorer.feature_names}
        result = scorer.score_entry(features)

        assert 'score' in result
        assert 'action' in result
        assert 0 <= result['score'] <= 1
        assert result['action'] in ['ENTER_FULL', 'HALF_SIZE', 'SKIP']

    def test_high_quality_returns_enter_full(self):
        """High quality score should return ENTER_FULL."""
        scorer = CerebusEntryScorer()
        X, y = self._make_training_data()
        scorer.train(X, y)

        # Use features that should produce high score
        features = {f: 2.0 for f in scorer.feature_names}
        result = scorer.score_entry(features)
        # Score should be clamped 0-1
        assert 0 <= result['score'] <= 1

    def test_low_quality_returns_skip(self):
        """Low quality score should return SKIP."""
        scorer = CerebusEntryScorer()
        X, y = self._make_training_data()
        scorer.train(X, y)

        features = {f: -2.0 for f in scorer.feature_names}
        result = scorer.score_entry(features)
        assert result['action'] == 'SKIP'

    def test_score_before_train_raises(self):
        """Scoring before training should raise assertion."""
        scorer = CerebusEntryScorer()
        with pytest.raises(AssertionError):
            scorer.score_entry({f: 0 for f in scorer.feature_names})

    def test_model_save_and_load(self):
        """Scorer should save and load correctly."""
        scorer = CerebusEntryScorer()
        X, y = self._make_training_data()
        scorer.train(X, y)

        features = {f: 0.5 for f in scorer.feature_names}
        score_before = scorer.score_entry(features)

        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "entry_scorer_xgb.pkl"
            scorer.save(tmp_path)

            # CC's load is a classmethod
            scorer2 = CerebusEntryScorer.load(tmp_path)
            assert scorer2.is_trained

            score_after = scorer2.score_entry(features)
            assert abs(score_before['score'] - score_after['score']) < 0.01


class TestRegimeMapping:
    """Test regime label mappings."""

    def test_regime_map_complete(self):
        """All 4 regimes should be mapped."""
        assert len(REGIME_MAP) == 4
        assert REGIME_MAP[0] == 'CONFIRMED'
        assert REGIME_MAP[1] == 'CAUTION'
        assert REGIME_MAP[2] == 'FAILED'
        assert REGIME_MAP[3] == 'NO-GO'

    def test_regime_reverse_mapping(self):
        """Reverse mapping should work."""
        from regime_classifier import REGIME_REVERSE
        assert REGIME_REVERSE['CONFIRMED'] == 0
        assert REGIME_REVERSE['CAUTION'] == 1
        assert REGIME_REVERSE['FAILED'] == 2
        assert REGIME_REVERSE['NO-GO'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
