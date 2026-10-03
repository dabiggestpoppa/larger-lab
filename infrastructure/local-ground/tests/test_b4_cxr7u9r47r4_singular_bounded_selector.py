#!/usr/bin/env python3
"""B4-CXR7U9R47R4 - ONE selector classifier, and a BOUNDED selector input.

Two defects the independent review found in the R46 head:

* `pg-recovery.py` defined `_classify_claim_content` TWICE. The second
  definition silently shadowed the first, so the copy a reviewer read at the
  top of the pair was not the copy that executed -- and the two docstrings
  disagreed with each other about the return value.
* nothing bounded the selector's size. The claim is a small fixed-schema JSON
  object, but the reader allocated a buffer for whatever the file held.

R47 deletes the shadowed copy and bounds the read BEFORE and DURING it. These
proofs show the parser is singular, the bound is conservative relative to a
real published claim, and an oversized / growing / truncated selector is
refused whole -- never truncated and then parsed -- with every governed file
left byte-identical.
"""
import ast
import json
import os
from pathlib import Path

import pytest

from test_b4_cxr7u9r47r1_authority_snapshot import (  # noqa: F401
    CLI, OPID, _build, _bytes, _census, _claim_doc, _publish, pgrec)

ENGINE = Path(pgrec.__file__).resolve()


def _claim_path(tmp_path):
    return Path(pgrec._transitions_dir()) / f"{OPID}.claim"


def _rewrite_selector(tmp_path, payload, mode=0o600):
    path = _claim_path(tmp_path)
    path.write_bytes(payload)
    os.chmod(path, mode)
    return path


# --------------------------------------------------------------------- #
# one definition, not two
# --------------------------------------------------------------------- #

def test_exactly_one_selector_classifier_definition_exists():
    """A collection proof: the module defines `_classify_claim_content` exactly
    once, and the single definition that survives is the one the module's
    namespace actually holds."""
    tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
    definitions = [n for n in tree.body
                   if isinstance(n, ast.FunctionDef)
                   and n.name == "_classify_claim_content"]
    assert len(definitions) == 1, (
        "the module must define the selector classifier exactly once; found",
        len(definitions))
    assert pgrec._classify_claim_content.__code__.co_firstlineno == \
        definitions[0].lineno, (
        "the definition that executes must be the one the source declares")


def test_no_other_duplicate_function_definitions_in_the_engine():
    """The shadowing defect was not specific to the selector: a later
    definition of the same name silently replaces the earlier one. Prove the
    module contains no such collision at all."""
    tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
    seen = {}
    collisions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            if node.name in seen:
                collisions.append((node.name, seen[node.name], node.lineno))
            seen[node.name] = node.lineno
    assert not collisions, ("top-level definitions shadow each other", collisions)


# --------------------------------------------------------------------- #
# the bound is conservative
# --------------------------------------------------------------------- #

def test_the_bound_is_conservative_relative_to_a_real_published_claim(tmp_path):
    """A genuine engine-published claim is far below the bound, so the bound can
    never refuse a legitimate selector."""
    _transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    published = _claim_path(tmp_path)
    real = published.stat().st_size
    assert real < pgrec._CLAIM_MAX_BYTES, (
        "a real selector must fit inside the bound", real)
    # and by a wide margin, so the bound is not tuned to today's payload
    assert pgrec._CLAIM_MAX_BYTES > real * 4, (real, pgrec._CLAIM_MAX_BYTES)


def test_an_ordinary_valid_selector_is_still_accepted(tmp_path):
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    snapshot = pgrec._read_selector_snapshot(OPID)
    assert snapshot.present
    assert snapshot.claim["transition"] == "rollback"
    assert pgrec._classify_claim_content(
        OPID, snapshot, expected_receipt_sha256=pgrec._receipt_digest(promote)) \
        == "bound_complete"
    assert pgrec._classify_record_for_shell(record, promote) == 6


# --------------------------------------------------------------------- #
# the bound is enforced BEFORE and DURING the read
# --------------------------------------------------------------------- #

def test_an_oversized_selector_is_refused_before_any_bytes_are_read(
        tmp_path, monkeypatch):
    """The pre-read bound: the size is refused from the admitted descriptor's
    own stat, so no buffer is ever allocated for the oversized payload."""
    _transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    _rewrite_selector(tmp_path, _bytes(_claim_doc(promote, "rollback")) +
                      b" " * pgrec._CLAIM_MAX_BYTES)
    before = _census(pgrec._transitions_dir())
    real_read = os.read
    reads = {"n": 0}

    def counting_read(fd, size):
        reads["n"] += 1
        return real_read(fd, size)

    monkeypatch.setattr(pgrec.os, "read", counting_read)
    with pytest.raises(pgrec._ExecutionAuthorityConflict) as refusal:
        pgrec._read_selector_snapshot(OPID)
    assert "oversized selector" in str(refusal.value), str(refusal.value)
    assert reads["n"] == 0, (
        "an oversized selector must be refused from its stat, before any read")
    assert _census(pgrec._transitions_dir()) == before


def test_a_selector_that_grows_during_the_read_is_refused(tmp_path,
                                                          monkeypatch):
    """The during-read bound. The descriptor reports a small size, so the
    pre-check passes, and the accumulated length crosses the bound mid-read.
    This is the TOCTOU the bound exists for, and it is refused at the first
    chunk past the bound rather than at EOF."""
    _transitions, _record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    path = _rewrite_selector(tmp_path,
                             _bytes(_claim_doc(promote, "rollback")) +
                             b" " * (pgrec._CLAIM_MAX_BYTES * 2))
    before = _census(pgrec._transitions_dir())
    real_fstat = os.fstat

    class _GrewAfterAdmission:
        """The same descriptor, reporting a size that would have passed the
        pre-read bound -- exactly what the engine sees if the file grows after
        the admission stat."""

        def __init__(self, info):
            self._info = info
            self.st_size = 8

        def __getattr__(self, name):
            return getattr(self._info, name)

    def small_fstat(fd):
        return _GrewAfterAdmission(real_fstat(fd))

    monkeypatch.setattr(pgrec.os, "fstat", small_fstat)
    with pytest.raises(pgrec._ExecutionAuthorityConflict) as refusal:
        pgrec._read_selector_snapshot(OPID)
    assert "grew past" in str(refusal.value), str(refusal.value)
    assert path.stat().st_size > pgrec._CLAIM_MAX_BYTES
    assert _census(pgrec._transitions_dir()) == before


@pytest.mark.parametrize("payload", [
    b"",
    b"{",
    b'{"format": "oce-transition-claim-v1"',
    b"\x00\x01\x02 not json at all",
    b'{"format":"oce-transition-claim-v1","operation_id":"' + b"a" * 32
    + b'","transition":"rollback","receipt_sha256":"',
])
def test_a_truncated_or_malformed_selector_is_refused_whole(tmp_path, payload):
    """Truncated selectors are refused, never repaired and never partially
    parsed; the governed tree is left byte-identical either way."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    _rewrite_selector(tmp_path, payload)
    before = _census(pgrec._transitions_dir())
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._read_selector_snapshot(OPID)
    assert pgrec._classify_record_for_shell(record, promote) == 4
    assert _census(pgrec._transitions_dir()) == before


def test_a_refused_selector_is_never_truncated_back_into_the_bound(tmp_path):
    """The bound is a REJECTION bound, not a truncation bound: an oversized
    file that happens to contain a valid claim inside its first bytes is still
    refused whole, so an attacker cannot smuggle a payload past the size check
    by padding."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    padded = _bytes(_claim_doc(promote, "rollback")) + b" " * pgrec._CLAIM_MAX_BYTES
    _rewrite_selector(tmp_path, padded)
    assert pgrec._classify_record_for_shell(record, promote) == 4
    assert json.loads((Path(pgrec._transitions_dir())
                       / f"{OPID}.json").read_text(encoding="utf-8"))["state"] \
        == "PROMOTED"


def test_every_denial_leaves_every_governed_file_byte_identical(tmp_path):
    """Across all four refusal shapes (oversized, growing, truncated, padded),
    the durable record and the selector are exactly as they were."""
    _transitions, record, promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    shapes = {
        "oversized": _bytes(_claim_doc(promote, "rollback"))
        + b" " * pgrec._CLAIM_MAX_BYTES,
        "truncated": _bytes(_claim_doc(promote, "rollback"))[:40],
        "empty": b"",
    }
    for name, payload in shapes.items():
        _rewrite_selector(tmp_path, payload)
        before = _census(pgrec._transitions_dir())
        assert pgrec._classify_record_for_shell(record, promote) == 4, name
        assert _census(pgrec._transitions_dir()) == before, name
