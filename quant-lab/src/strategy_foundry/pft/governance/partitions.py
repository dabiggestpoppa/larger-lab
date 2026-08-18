"""Data partition classes and the protected-access guard.

Partition classes per program constitution 7.5:
  DEVELOPMENT  - open to research
  CONFIRMATION - locked until explicit authorization
  HOLDOUT      - locked until explicit authorization
  METADATA_ONLY - always safe (file existence, coverage, integrity)

The guard fails CLOSED: any unknown partition class is treated as protected.
"""

from __future__ import annotations

PARTITION_CLASSES = {"DEVELOPMENT", "CONFIRMATION", "HOLDOUT", "METADATA_ONLY"}


class ProtectedPartitionError(RuntimeError):
    pass


class PartitionGuard:
    """Fail-closed gate over which partition classes may be touched."""

    def __init__(self, confirmation_authorized: bool = False, holdout_authorized: bool = False) -> None:
        self.confirmation_authorized = bool(confirmation_authorized)
        self.holdout_authorized = bool(holdout_authorized)

    def is_allowed(self, partition: str) -> bool:
        if partition not in PARTITION_CLASSES:
            return False  # unknown partition: fail closed
        if partition == "DEVELOPMENT":
            return True
        if partition == "METADATA_ONLY":
            return True
        if partition == "CONFIRMATION":
            return self.confirmation_authorized
        if partition == "HOLDOUT":
            return self.holdout_authorized
        return False

    def guard(self, partition: str) -> None:
        """Raise ProtectedPartitionError unless the partition is currently allowed."""
        if not self.is_allowed(partition):
            raise ProtectedPartitionError(
                f"partition {partition!r} is not authorized for access "
                f"(confirmation_authorized={self.confirmation_authorized}, "
                f"holdout_authorized={self.holdout_authorized})"
            )

    def state(self) -> dict:
        return {
            "confirmation_authorized": self.confirmation_authorized,
            "holdout_authorized": self.holdout_authorized,
        }
