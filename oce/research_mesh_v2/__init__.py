"""OCE Research Mesh V2.

Standalone-first institutional research substrate.
No automatic OCE wiring is performed from this package.
"""

from .models import EvidenceRecord, ResearchResult, SourceStatus
from .service import ResearchMesh

__all__ = ["EvidenceRecord", "ResearchResult", "SourceStatus", "ResearchMesh"]
