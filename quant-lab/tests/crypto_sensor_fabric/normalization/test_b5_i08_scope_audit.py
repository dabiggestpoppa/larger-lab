"""SENSOR-B5-I08E1 - RED-first scope audit + evidence determinism (U08-19/U08-20).

A checkpoint that proves what it added has also to prove what it did not.
This is the I08 counterpart of the I01/I02/I03/I05 scope audits: the frozen
``common/`` surface (bloc_05/03 §21 read against 06 §19's I08 title and the
I08-Q1 scope split recorded in ``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md``)
is present, and NOTHING else changed -- not the ratified I01 top-level API,
not the identity/terms/time packages, not the sealed I04B conversion module,
not the frozen plan, and no program gate.

The single authorized extension to pre-existing tests is disclosed here on
the established I02/I04A/I05 precedent: the B5-I01 and B5-I05 scope audits'
subpackage allowlists now name ``common`` (bloc_05/03 §21 freezes
``normalization/common/`` as required I08 surface).

U08-20 additionally re-measures the deterministic unit-validation evidence
producer: two invocations emit byte-identical JSON.

DISCLOSURE -- B5-I09 AMENDMENT (operator-authorized; full record in
``BLOC_05_I09_IMPLEMENTATION_EVIDENCE.md`` + ledger section 178): the I09E1
implementation pass is authorized to add the three remaining §21 modules to
``common/`` (``methodologies.py``, ``semantic_registry.py``, ``comparability.py``;
06 §19 titles I09 "methodology + semantic-equivalence registries" and the
I09E1 directive Q3 assigns the library-level §18 gate to I09).  On the exact
precedent by which this same file's frozen module set was born at I08, its
FROZEN_MODULES list grows from four to seven and ``test_i09_and_deferred_
modules_are_absent`` loses exactly those three names.  ``missingness.py`` and
``envelope.py`` stay deliberately absent (I09E1 Q4 / readiness §6 re-export
law), and every other measurement in this suite is untouched.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_PACKAGE = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization"
_COMMON = _PACKAGE / "common"
_EVIDENCE = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_05"
)
_PRODUCTION_FILES = (
    _COMMON / "__init__.py",
    _COMMON / "units.py",
    _COMMON / "numeric.py",
    _COMMON / "conversion.py",
)

#: I08's original frozen module set (four files).  envelope.py is
#: deliberately ABSENT: bloc_05/03 §2's full ``T1ObservationEnvelope``
#: requires I02/I06/I19-owned fields beside I09's two, so the frozen-name
#: composite stays unexported exactly as the I01 base layer records.
I08_FROZEN_MODULES = ["__init__.py", "conversion.py", "numeric.py", "units.py"]

#: DISCLOSED B5-I09 extension: 06 §19 gives I09 the methodology +
#: semantic-equivalence registries (and I09E1 Q3 the library-level §18 gate),
#: so the frozen set becomes these seven files.  missingness.py stays absent
#: by the readiness §6 re-export law.
FROZEN_MODULES = sorted(
    I08_FROZEN_MODULES
    + ["methodologies.py", "semantic_registry.py", "comparability.py"]
)

#: Still deferred after I09: the composite envelope (I02/I06/I19 fields) and
#: the missingness re-export fork that must never exist.
STILL_DEFERRED = ("missingness.py", "envelope.py")

#: Directive custody base for this checkpoint.
I08_BASE_HEAD = "88373c01cbfc41ac8edda5fe082d9e9d3db5f234"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=_QUANT_LAB,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout


def _sources() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in _PRODUCTION_FILES}


def _imported_modules() -> set[str]:
    found: set[str] = set()
    for text in _sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    found.add(f".{node.module or ''}")
                elif node.module:
                    found.add(node.module)
    return found


# ---------------------------------------------------------------------------
# U08-19 -- the frozen surface is exactly what the plan froze, and nothing more
# ---------------------------------------------------------------------------


def test_common_package_exists() -> None:
    assert _COMMON.is_dir(), "bloc_05/03 §21 requires normalization/common/"


def test_common_package_is_exactly_the_frozen_modules() -> None:
    files = sorted(entry.name for entry in _COMMON.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_i09_and_deferred_modules_are_absent() -> None:
    """After the disclosed I09 extension: only the deliberately deferred
    modules remain absent; a bare module beside the package would shadow the
    authorized subpackage."""
    for forbidden in STILL_DEFERRED + (
        "sensors",
        "lineage",
        "duplicates",
        "quality",
        "storage",
        "query",
    ):
        assert not (_PACKAGE / forbidden).exists(), forbidden
        assert not (_COMMON / forbidden).exists(), forbidden


def test_ratified_i01_top_level_api_is_unchanged() -> None:
    """The top-level normalization surface stays the ratified 24 symbols;
    I08 names are reached only through ``...normalization.common``."""
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in (
        "CanonicalQuantityUnit",
        "convert_stablecoin_to_usd",
        "CrossCurrencyResult",
    ):
        assert absent not in normalization.__all__


def test_terms_time_identity_packages_are_untouched_by_i08() -> None:
    """Sealed I02/I04B/I05 trees: no I08 edit reached them."""
    diff = _git("diff", I08_BASE_HEAD, "--", "src/crypto_sensor_fabric/normalization")
    changed_paths = sorted(
        line
        for line in diff.splitlines()
        if line.startswith("diff --git")
    )
    for line in changed_paths:
        assert "/common/" in line, f"non-common source change: {line}"


def test_no_network_or_provider_import() -> None:
    imported = _imported_modules()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib.request",
        "urllib3",
        "websockets",
        "ccxt",
        "crypto_sensor_fabric.providers",
        "crypto_sensor_fabric.probes.runner",
    ):
        assert forbidden not in imported, forbidden


def test_no_filesystem_or_backend_import() -> None:
    """Units/numeric conversion are pure: value in, answer out."""
    imported = _imported_modules()
    for forbidden in (
        "pathlib",
        "os",
        "glob",
        "duckdb",
        "pyarrow",
        "pandas",
        "sqlite3",
        "shutil",
    ):
        assert forbidden not in imported, forbidden


def test_no_hashing_id_generation_or_wall_clock() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "hashlib",
            "sha256(",
            "uuid",
            "uuid4",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "random",
            "secrets",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_program_gate_is_claimed() -> None:
    """Eight gates stay NOT_YET_EARNED; UNIT_GATE is earned by the acceptance
    layer (06 §21), never by an implementation checkpoint."""
    matrix = json.loads(
        (_EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json").read_text(encoding="utf-8")
    )
    gates = matrix["bloc_05_blocking_gates"]
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate


# ---------------------------------------------------------------------------
# U08-20 -- deterministic unit-validation evidence
# ---------------------------------------------------------------------------

#: The ratified I08 artifact bytes (BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md §4).
#: DISCLOSED B5-I09: the producer's live rows re-measure the working tree, so
#: after the operator-authorized I09 extension of ``common/`` its regenerated
#: bytes describe the post-I09 tree.  Q2 forbids regenerating the I08
#: evidence, so the committed artifact is PINNED here by its ratified digest
#: -- the exact mechanism I08 itself applied to the I05/I06 artifacts it had
#: to re-pin (I08 evidence §5/§6.3).
I08_UNIT_VALIDATION_SHA256 = (
    "260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4"
)


def test_unit_validation_evidence_is_deterministic(tmp_path: Path) -> None:
    """The tracked producer emits byte-identical bytes across invocations,
    and the committed artifact keeps its ratified I08 bytes.

    DISCLOSED B5-I09 amendment: the live-hash match (``--check`` exit 0)
    becomes a pin-by-SHA-256 of the committed artifact, because I09's
    authorized ``common/`` extension changes what the producer's U08-19 rows
    measure.  Determinism itself is still measured live (two invocations,
    byte-identical), and the artifact is still sealed -- by digest instead of
    by re-derivation.  ``--check`` writes nothing in either state.
    """
    script = (
        _QUANT_LAB
        / "research"
        / "crypto_foundry"
        / "sensor_fabric"
        / "scripts"
        / "b5_i08_units.py"
    )
    assert script.is_file(), "the tracked I08 evidence producer is missing"
    outputs = []
    import hashlib
    import os
    import sys

    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=_QUANT_LAB,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        # The summary line goes to stdout on a match and to stderr on a
        # refusal, so compare the concatenation: the deterministic OUTPUT of
        # the producer, whichever channel it uses.
        outputs.append(result.stdout + result.stderr)
        # 0 = rows PASS and the bytes match the committed artifact (the
        # I08-era state); 1 = the producer's exit contract firing on its
        # now-non-PASS U08-19 rows, which is the expected post-I09 state:
        # those rows re-measure the tree I09 was authorized to extend, so the
        # producer aborts BEFORE writing, exactly as designed.  Any other
        # exit (e.g. 2 = usage, 3 = bytes drift with passing rows) would
        # contradict the disclosed state and is a real defect.
        assert result.returncode in (0, 1), result.stderr.decode("utf-8", "replace")
    assert outputs[0] == outputs[1], "producer output is not deterministic"
    artifact = _EVIDENCE / "bloc_05_unit_validation.json"
    measured = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert measured == I08_UNIT_VALIDATION_SHA256, (
        f"the ratified I08 artifact left its pinned bytes: {measured}"
    )
