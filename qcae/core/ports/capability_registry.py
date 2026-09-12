"""CapabilityRegistry port (P1-R1 §4).

Durable, append-oriented storage for the P0 capability domain objects:

- CapabilityContract (versioned: contract_version is part of the key)
- CapabilityAtom (versioned: atom_version is part of the key)
- CompositeCapability (versioned by contract_version)
- Candidate (implementation/revision objects; not versioned — a new revision
  is a new candidate record)

Identity law (§5): capability identity and implementation identity stay
distinct objects. The registry never treats a repository/product coordinate
as a capability ID, and multiple candidates per atom are the norm.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from qcae.core.capabilities.atom import CapabilityAtom
from qcae.core.capabilities.candidate import Candidate
from qcae.core.capabilities.composite import CompositeCapability
from qcae.core.contracts.contract import CapabilityContract

__all__ = ["CapabilityRegistryPort"]


class CapabilityRegistryPort(ABC):
    """Durable storage/retrieval for capability domain records."""

    # -- CapabilityContract -------------------------------------------------

    @abstractmethod
    def add_contract(self, contract: CapabilityContract) -> str:
        """Persist a contract version (capability_id + contract_version key)."""

    @abstractmethod
    def get_contract(self, capability_id: str, contract_version: int) -> Optional[CapabilityContract]:
        """Fetch one exact contract version (digest-verified)."""

    @abstractmethod
    def list_contract_versions(self, capability_id: str) -> List[CapabilityContract]:
        """All versions of one capability's contract, ascending."""

    @abstractmethod
    def latest_contract(self, capability_id: str) -> Optional[CapabilityContract]:
        """Highest contract_version for the capability."""

    @abstractmethod
    def contract_supersession_chain(self, capability_id: str) -> List[CapabilityContract]:
        """Versions linked via supersedes_contract, oldest first."""

    # -- CapabilityAtom -------------------------------------------------------

    @abstractmethod
    def add_atom(self, atom: CapabilityAtom) -> str:
        """Persist an atom version (atom_id + atom_version key)."""

    @abstractmethod
    def get_atom(self, atom_id: str, atom_version: Optional[int] = None) -> Optional[CapabilityAtom]:
        """Fetch exact atom version, or the highest when None."""

    @abstractmethod
    def list_atoms_for_capability(self, capability_id: str) -> List[CapabilityAtom]:
        """Atoms whose parent_capabilities include ``capability_id``."""

    @abstractmethod
    def list_atoms_by_status(self, status) -> List[CapabilityAtom]:
        """Atoms at one AtomStatus."""

    @abstractmethod
    def list_atoms_by_domain(self, domain: str) -> List[CapabilityAtom]:
        """Atoms in one domain."""

    # -- CompositeCapability --------------------------------------------------

    @abstractmethod
    def add_composite(self, composite: CompositeCapability) -> str:
        """Persist a composite version."""

    @abstractmethod
    def get_composite(self, capability_id: str, contract_version: int) -> Optional[CompositeCapability]:
        """Fetch one composite version (digest-verified)."""

    @abstractmethod
    def member_atoms(self, capability_id: str, contract_version: int) -> List[CapabilityAtom]:
        """Resolve a composite's members to their stored atom records."""

    # -- Candidate ------------------------------------------------------------

    @abstractmethod
    def add_candidate(self, candidate: Candidate) -> str:
        """Persist a candidate (append-only; new revision = new record)."""

    @abstractmethod
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Fetch by candidate_id (digest-verified)."""

    @abstractmethod
    def list_candidates_for_atom(self, atom_id: str) -> List[Candidate]:
        """Candidates claiming the atom (multiple implementations are the norm)."""

    @abstractmethod
    def list_candidates_by_source(self, source_ref: str, revision: str = "") -> List[Candidate]:
        """Candidates from one source identity, optionally pinned revision."""
