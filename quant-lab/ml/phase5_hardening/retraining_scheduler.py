"""
Phase 5.4: Retraining Scheduler
=================================
Manages quarterly retraining cadence and drift-triggered early retraining.

Rules:
  - Retrain quarterly (every 3 months) on latest 6 months of data
  - Trigger early if PSI drift > 0.20 on any feature
  - New model must pass shadow mode before deployment
  - One-click rollback to previous model
  - Auto-rollback if WR drops > 5% in 48h
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


@dataclass
class RetrainingConfig:
    """Retraining schedule configuration."""
    cadence_days: int = 90           # Quarterly
    lookback_days: int = 180         # 6 months of data
    psi_drift_threshold: float = 0.20
    wr_drop_threshold: float = 5.0   # Auto-rollback if WR drops 5% in 48h
    shadow_duration_days: int = 14
    max_model_versions: int = 5      # Keep last 5 model versions


@dataclass
class ModelVersion:
    """A saved model version."""
    version: str
    created_at: str
    cv_accuracy: float
    training_data_hash: str
    path: str
    is_active: bool = False
    shadow_passed: bool = False


class RetrainingScheduler:
    """
    Manages model retraining cadence and versioning.
    """

    def __init__(
        self,
        model_dir: Path,
        config: RetrainingConfig | None = None,
    ):
        self.model_dir = Path(model_dir)
        self.config = config or RetrainingConfig()
        self.versions: list[ModelVersion] = []
        self.active_version: str | None = None
        self._load_registry()

    def _registry_path(self) -> Path:
        return self.model_dir / "model_registry.json"

    def _load_registry(self) -> None:
        """Load model registry from disk."""
        path = self._registry_path()
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            self.versions = [ModelVersion(**v) for v in data.get("versions", [])]
            self.active_version = data.get("active_version")

    def _save_registry(self) -> None:
        """Save model registry to disk."""
        data = {
            "versions": [
                {
                    "version": v.version,
                    "created_at": v.created_at,
                    "cv_accuracy": v.cv_accuracy,
                    "training_data_hash": v.training_data_hash,
                    "path": v.path,
                    "is_active": v.is_active,
                    "shadow_passed": v.shadow_passed,
                }
                for v in self.versions
            ],
            "active_version": self.active_version,
        }
        with open(self._registry_path(), "w") as f:
            json.dump(data, f, indent=2)

    def should_retrain(self, last_train_date: str | None = None) -> tuple[bool, str]:
        """
        Check if retraining is due based on cadence.

        Returns
        -------
        (should_retrain, reason)
        """
        if last_train_date is None:
            if self.versions:
                last_train_date = self.versions[-1].created_at
            else:
                return True, "No previous model — initial training needed"

        last = datetime.fromisoformat(last_train_date)
        now = datetime.now(timezone.utc)
        days_since = (now - last).days

        if days_since >= self.config.cadence_days:
            return True, f"Quarterly retraining due ({days_since}d since last train)"

        return False, f"Next retrain in {self.config.cadence_days - days_since}d"

    def check_drift_trigger(self, psi_values: dict[str, float]) -> tuple[bool, list[str]]:
        """
        Check if PSI drift triggers early retraining.

        Returns
        -------
        (should_retrain, reasons)
        """
        reasons = []
        for feature, psi in psi_values.items():
            if psi >= self.config.psi_drift_threshold:
                reasons.append(f"PSI drift on {feature}: {psi:.3f} >= {self.config.psi_drift_threshold}")

        return len(reasons) > 0, reasons

    def register_model(
        self,
        version: str,
        cv_accuracy: float,
        data_hash: str,
        model_path: Path,
    ) -> ModelVersion:
        """Register a new model version."""
        # Deactivate current active
        for v in self.versions:
            v.is_active = False

        mv = ModelVersion(
            version=version,
            created_at=datetime.now(timezone.utc).isoformat(),
            cv_accuracy=cv_accuracy,
            training_data_hash=data_hash,
            path=str(model_path),
            is_active=False,  # Not active until shadow passes
            shadow_passed=False,
        )
        self.versions.append(mv)

        # Prune old versions
        if len(self.versions) > self.config.max_model_versions:
            old = self.versions.pop(0)
            old_path = Path(old.path)
            if old_path.exists():
                old_path.unlink()

        self._save_registry()
        return mv

    def promote_model(self, version: str) -> bool:
        """Promote a model version to active (after shadow passes)."""
        for v in self.versions:
            if v.version == version:
                # Deactivate all
                for vv in self.versions:
                    vv.is_active = False
                v.is_active = True
                v.shadow_passed = True
                self.active_version = version
                self._save_registry()
                print(f"✅ Model {version} promoted to active")
                return True

        print(f"❌ Model version {version} not found")
        return False

    def rollback(self) -> str | None:
        """
        Rollback to previous model version.
        Returns the version rolled back to, or None if no previous version.
        """
        if len(self.versions) < 2:
            print("❌ No previous version to rollback to")
            return None

        # Deactivate current
        current = self.versions[-1]
        current.is_active = False

        # Activate previous
        previous = self.versions[-2]
        previous.is_active = True
        self.active_version = previous.version

        self._save_registry()
        print(f"⏪ Rolled back from {current.version} to {previous.version}")
        return previous.version

    def get_active_model_path(self) -> Path | None:
        """Get path to the currently active model."""
        for v in self.versions:
            if v.is_active:
                return Path(v.path)
        return None

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "active_version": self.active_version,
            "total_versions": len(self.versions),
            "versions": [
                {
                    "version": v.version,
                    "created_at": v.created_at,
                    "cv_accuracy": v.cv_accuracy,
                    "is_active": v.is_active,
                    "shadow_passed": v.shadow_passed,
                }
                for v in self.versions
            ],
        }


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        scheduler = RetrainingScheduler(Path(tmpdir))

        # Check if retrain needed
        should, reason = scheduler.should_retrain()
        print(f"Should retrain: {should} — {reason}")

        # Register a model
        model_path = Path(tmpdir) / "regime_v1.pkl"
        model_path.touch()
        scheduler.register_model("v1", cv_accuracy=0.91, data_hash="abc123", model_path=model_path)

        # Check drift
        drifted, reasons = scheduler.check_drift_trigger({"asian_range_pips": 0.25})
        print(f"Drift trigger: {drifted} — {reasons}")

        # Promote
        scheduler.promote_model("v1")
        print(f"Status: {scheduler.get_status()}")
