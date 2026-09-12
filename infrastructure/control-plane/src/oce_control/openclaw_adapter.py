"""OpenClaw deprecation adapter.

OpenClaw is no longer part of the target architecture. Where Book 2
encounters an existing OpenClaw-facing boundary:
- isolate it behind an adapter
- mark it deprecated
- implement a provider-neutral interface
- prepare Hermes as the future supplemental adapter
- preserve rollback until replacement validation passes

Remaining OpenClaw references and their scheduled removal book are recorded.
"""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class OpenClawReference:
    path: str
    reference_type: str  # import, config, script, documentation
    description: str
    scheduled_removal_book: str = "B4"
    deprecated: bool = True
    adapter: str = "OpenClawAdapter"


class OpenClawAdapter:
    """Provider-neutral adapter isolating OpenClaw-facing boundaries.

    All OpenClaw-facing code is isolated behind this adapter. The adapter
    implements a provider-neutral interface so Hermes can later replace it
    without affecting the control plane.
    """

    def __init__(self):
        self._references: list[OpenClawReference] = []
        self._scan_repository()

    def _scan_repository(self) -> None:
        """Record known OpenClaw references."""
        known_refs = [
            OpenClawReference(
                path=".openclaw-2/",
                reference_type="config",
                description="OpenClaw configuration directory (agent skills)",
                scheduled_removal_book="B4",
            ),
            OpenClawReference(
                path=".openclaw-2/.openclaw/skills/srra-oph-build/SKILL.md",
                reference_type="documentation",
                description="SRRA-OPH build skill documentation",
                scheduled_removal_book="B4",
            ),
            OpenClawReference(
                path=".openclaw-2/skills/srra-oph-build/SKILL.md",
                reference_type="documentation",
                description="Duplicate SRRA-OPH build skill",
                scheduled_removal_book="B4",
            ),
        ]
        self._references = known_refs

    @property
    def references(self) -> list:
        return list(self._references)

    @property
    def is_deprecated(self) -> bool:
        return True

    @property
    def removal_scheduled(self) -> bool:
        return True

    def provider_neutral_interface(self) -> dict:
        """Return the provider-neutral interface contract."""
        return {
            "interface": "supplemental_assistant",
            "current_provider": "openclaw",
            "future_provider": "hermes",
            "deprecation_status": "deprecated",
            "removal_book": "B4",
            "rollback_preserved": True,
        }
