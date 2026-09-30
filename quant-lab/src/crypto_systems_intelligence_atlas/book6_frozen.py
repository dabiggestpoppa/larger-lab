"""The shared Book 6 frozen record base.

Every Book 6 record is immutable and declares ``extra="forbid"``. Pydantic v2's
``model_copy(update=...)`` bypasses BOTH: it does not re-run validators and it
writes unknown keys straight into the instance ``__dict__``, so a caller can
forge ``observation.score = 0.9`` on a record whose schema has no score field.
That is exactly the constructor-only security the ratified plan forbids
(plan v0.2 §30): the anti-score firewall has to hold against ``model_copy``, not
merely against the constructor.

The base closes that hole by re-validating the requested update against the
model's own fields, so an unknown key is a refusal rather than a smuggled
attribute. It changes no ratified field, adds none, and never weakens a
validator: ``model_copy`` here is strictly a subset of what the constructor
accepts.
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict


class Book6FrozenModel(BaseModel):
    """An immutable Book 6 record whose ``model_copy`` cannot widen its schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool = False,
    ) -> "Book6FrozenModel":
        """Copy with a validated update — unknown keys are refused, not smuggled.

        A legitimate update (a field the model declares, holding a value the
        model would accept) behaves exactly as before. An unknown key raises
        rather than attaching an attribute that no reader should ever consult.
        """

        if update is not None:
            unknown = sorted(set(update) - set(type(self).model_fields))
            if unknown:
                raise ValueError(
                    f"{type(self).__name__} does not accept {unknown}; Book 6 "
                    f"records may not acquire fields outside their ratified "
                    f"schema (extra='forbid')"
                )
        return super().model_copy(update=dict(update) if update is not None else None, deep=deep)


__all__ = ["Book6FrozenModel"]
