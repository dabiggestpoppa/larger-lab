"""Phase 1.7.7 — Model Benchmarking Engine. Compares models continuously."""
from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.benchmark")


class ModelBenchmarkingEngine:
    """Compares models and routes to the best one per task."""

    def __init__(self):
        self._model_scores: Dict[str, Dict[str, float]] = {}
        self._latency: Dict[str, float] = {}

    def record_result(self, model: str, task_type: str, success: bool, latency_seconds: float, quality: float = 0.5):
        if model not in self._model_scores:
            self._model_scores[model] = {}
        key = f"{task_type}_score"
        current = self._model_scores[model].get(key, 0.5)
        self._model_scores[model][key] = 0.7 * current + 0.3 * quality
        self._latency[model] = latency_seconds

    def get_best_model(self, task_type: str = "general") -> str:
        """Get the best model for a task type."""
        best_model = "openrouter/owl-alpha"
        best_score = 0.0
        for model, scores in self._model_scores.items():
            score = scores.get(f"{task_type}_score", 0.0)
            if score > best_score:
                best_score = score
                best_model = model
        return best_model

    def get_stats(self) -> Dict[str, Any]:
        return {
            "model_scores": {k: dict(v) for k, v in self._model_scores.items()},
            "latency": dict(self._latency),
        }
