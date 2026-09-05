"""Resume / pagination protection (01 §15-§16 / 03 §5-§8, SENSOR-B3-I03).

`ResumeToken` (models.py) is the serialized, deterministic provider-native
checkpoint.  This module protects traversal against:

- repeated cursor (loop detection)          -> PaginationFailure
- page-number advance with identical content -> loop detection
- non-monotonic timestamps                   -> quality flag / failure
- ambiguous completion (short page != done)  -> explicit completion decision
- duplicate page edges                       -> annotated, never silently dropped

Raw evidence is never destructively deduplicated; duplicates are annotated.
"""

from __future__ import annotations

from datetime import datetime

from ...contracts.enums import SensorFamily
from .enums import DuplicateAnnotation
from .errors import PaginationFailure
from .models import ResumeToken


class CursorTracker:
    """Stateful protection for one paginated traversal (03 §8)."""

    def __init__(
        self,
        provider_id: str,
        sensor_family: SensorFamily = SensorFamily.MECHANICAL_TRADE,
    ) -> None:
        self._provider_id = provider_id
        self._sensor_family = sensor_family
        self._seen_cursors: list[str] = []
        self._seen_content_hashes: dict[int, str] = {}
        self._last_timestamp: datetime | None = None

    def observe_page(
        self,
        page_number: int,
        cursor: str | None,
        content_hash: str | None,
        last_timestamp: datetime | None,
        *,
        allow_timestamp_reversal_overlap: bool = False,
    ) -> list[DuplicateAnnotation] | None:
        """Record one page; returns duplicate annotations or raises.

        Raises `PaginationFailure` on a repeated cursor (same cursor seen more
        than once in a cycle) or on an impossible timestamp regression.
        """
        annotations: list[DuplicateAnnotation] = []

        if cursor is not None and cursor in self._seen_cursors:
            raise PaginationFailure(
                provider_id=self._provider_id,
                sensor_family=self._sensor_family,
                detail=f"repeated cursor {cursor!r} detected (loop)",
            )
        if cursor is not None:
            self._seen_cursors.append(cursor)

        if page_number > 0 and content_hash is not None:
            previous = self._seen_content_hashes.get(page_number - 1)
            if previous == content_hash:
                annotations.append(DuplicateAnnotation.REPEATED_PAGE)

        if content_hash is not None:
            self._seen_content_hashes[page_number] = content_hash

        if (
            self._last_timestamp is not None
            and last_timestamp is not None
            and last_timestamp < self._last_timestamp
        ):
            if allow_timestamp_reversal_overlap:
                annotations.append(DuplicateAnnotation.POSSIBLE_DUPLICATE)
            else:
                raise PaginationFailure(
                    provider_id=self._provider_id,
                    sensor_family=self._sensor_family,
                    detail=(
                        "non-monotonic timestamp pagination: "
                        f"{last_timestamp.isoformat()} < "
                        f"{self._last_timestamp.isoformat()}"
                    ),
                )

        if last_timestamp is not None:
            self._last_timestamp = last_timestamp

        return annotations or None


def resume_token_round_trip(token: ResumeToken) -> ResumeToken:
    """Deterministic round-trip: JSON dump -> load -> identical token."""
    rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
    if rebuilt != token:
        raise PaginationFailure(
            provider_id="unknown",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            detail="resume token failed deterministic round-trip (03 §8)",
        )
    return rebuilt


def completion_from_provider_semantics(
    *,
    page_size_hint: int,
    rows_returned: int,
    provider_says_more: bool | None,
    cursor_advances: bool,
) -> bool:
    """Completion decision from provider semantics, never short-page guessing.

    A short page is NOT completion by itself (01 §15); the provider's own
    pagination signal decides.
    """
    if provider_says_more is True:
        return False
    if provider_says_more is False:
        return True
    # provider silent: cursor advancing but no more signal -> not complete
    return not cursor_advances
