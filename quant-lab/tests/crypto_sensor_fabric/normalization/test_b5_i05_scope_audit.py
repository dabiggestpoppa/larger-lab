"""SENSOR-B5-I05 - negative scope audit for the time-semantics subpackage.

A checkpoint that proves what it added has also to prove what it did not.
This audit is the I05 counterpart of the I01/I02/I03 scope audits: the frozen
seven-module surface (bloc_05/02 s17) and the two frozen configurations are
present, and NOTHING else changed -- not the ratified I01 top-level API, not
the I02/I03 identity package, not the I04 terms package, and no program gate.

The single authorized extension to a pre-existing test is disclosed here: the
B5-I01 scope audit's subpackage allowlist now names ``time`` (on the exact
precedent it already documents for ``identity`` at B5-I02 and ``terms`` at
B5-I04A), because bloc_05/02 s17 freezes ``normalization/time/`` as required
I05 surface.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_REPO_ROOT = _QUANT_LAB.parent
_PACKAGE = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization"
_TIME = _PACKAGE / "time"
_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric"

#: The directive's required starting HEAD, and therefore the I05 base line.
I05_BASE_HEAD = "745b3797bfc3f69a1df4e8bc7171436c98996490"

FROZEN_MODULES = [
    "__init__.py",
    "availability.py",
    "enums.py",
    "intervals.py",
    "models.py",
    "replay_gate.py",
    "revision_policy.py",
    "semantics_registry.py",
]

FROZEN_CONFIGS = ["provider_time_semantics.yaml", "revision_policies.yaml"]

#: Quant-lab-relative path of the one pre-existing artifact this checkpoint
#: is authorized to rewrite, and only mechanically: directive section 07
#: re-counts tracked Python files after the authorized I05 additions are
#: staged and republishes the I11R2 governance binding audit through its
#: established ``UPDATE_I11R2_EVIDENCE=1`` mechanism.
I11R2_AUDIT = (
    "research/crypto_foundry/sensor_fabric/evidence/bloc_04/"
    "BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json"
)

#: Where a previously run test suite may leave regenerable dirt on HISTORICAL
#: evidence.  Section 07 of the directive names this hazard explicitly: prior
#: tests may dirty Bloc 4 JSON evidence.  Such dirt is tolerated only while it
#: is unstaged worktree state, and it is restored and re-verified before the
#: checkpoint is committed -- a staged edit here would ship a rewrite of
#: protected history.
SIDE_EFFECT_PREFIX = "research/crypto_foundry/sensor_fabric/evidence/bloc_04/"


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
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_TIME.glob("*.py"))
    }


def _imported_modules() -> set[str]:
    found: set[str] = set()
    for text in _sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    found.add("." * node.level + (node.module or ""))
                elif node.module:
                    found.add(node.module)
    return found


# ---------------------------------------------------------------------------
# The frozen surface is exactly what the plan froze, and nothing more
# ---------------------------------------------------------------------------


def test_time_package_exists() -> None:
    assert _TIME.is_dir(), "bloc_05/02 s17 requires normalization/time/"


def test_time_package_is_exactly_the_frozen_seven_modules() -> None:
    files = sorted(entry.name for entry in _TIME.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


@pytest.mark.parametrize(
    "forbidden",
    [
        # "common" was operator-authorized at B5-I08 (SENSOR-B5-I08E1
        # directive, bloc_05/03 §21: normalization/common/ is required I08
        # surface) -- disclosed removal on the same precedent by which the
        # B5-I01 audit's allowlist grew "identity" (I02), "terms" (I04A)
        # and "time" (I05).  Every other subpackage stays forbidden.
        "sensors",
        "lineage",
        "duplicates",
        "quality",
        "storage",
        "query",
        "registry",
        "provider_semantics",
    ],
)
def test_no_unauthorized_normalization_subpackage_exists(forbidden: str) -> None:
    assert not (_PACKAGE / forbidden).exists(), forbidden


@pytest.mark.parametrize(
    "forbidden",
    ["availability.py", "intervals.py", "revision_policy.py", "replay_gate.py",
     "semantics_registry.py", "writer.py", "query.py"],
)
def test_frozen_modules_stay_inside_the_time_subpackage(forbidden: str) -> None:
    """The I01 top-level module layout is unchanged; only time/ was added."""
    assert not (_PACKAGE / forbidden).exists(), forbidden


def test_the_two_frozen_configurations_exist() -> None:
    for name in FROZEN_CONFIGS:
        assert (_CONFIG / name).is_file(), name


# ---------------------------------------------------------------------------
# Dependency firewall for the new package
# ---------------------------------------------------------------------------


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
    """Resolution and derivation are pure: text in, answer out."""
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
        "json",
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
            "date.today",
            "random",
            "secrets",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_program_gate_or_acceptance_language_in_the_new_package() -> None:
    """Implementation must never claim an acceptance or a gate."""
    for name, text in _sources().items():
        for forbidden in ("OPERATOR_ACCEPTED", "IMPLEMENTATION_PASS", "_GATE ="):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# Noninterference: ratified surfaces are untouched
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "protected",
    [
        "src/crypto_sensor_fabric/normalization/__init__.py",
        "src/crypto_sensor_fabric/normalization/enums.py",
        "src/crypto_sensor_fabric/normalization/models.py",
        "src/crypto_sensor_fabric/normalization/identity",
        "src/crypto_sensor_fabric/normalization/terms",
    ],
)
def test_ratified_i01_to_i04_sources_are_unchanged_since_the_i05_base(protected: str) -> None:
    diff = _git("diff", "--name-only", I05_BASE_HEAD, "--", protected)
    assert diff.strip() == "", f"{protected} changed: {diff.strip()}"


def test_the_i01_top_level_api_does_not_reexport_time_symbols() -> None:
    """bloc_05/06 s19/§20: the ratified I01 public surface is not expanded."""
    import crypto_sensor_fabric.normalization as normalization

    time_names = {name for name in _sources()} | {
        "CanonicalTimestamp",
        "AvailabilityResolution",
        "ReplayEligibility",
        "derive_market_available_at",
        "assess_replay_eligibility",
        "TimestampRole",
    }
    assert not (set(normalization.__all__) & time_names)
    assert not hasattr(normalization, "derive_market_available_at")
    assert not hasattr(normalization, "assess_replay_eligibility")


def test_the_time_package_is_importable_without_side_effects() -> None:
    import crypto_sensor_fabric.normalization.time as time_package

    assert time_package.__all__
    assert len(set(time_package.__all__)) == len(time_package.__all__)
    for name in time_package.__all__:
        assert hasattr(time_package, name), name
    assert not [name for name in time_package.__all__ if name.startswith("_")]


def _quant_lab_paths(*args: str) -> list[str]:
    """Run ``git`` from ``quant-lab`` and return quant-lab-relative paths.

    ``git diff`` prints repo-root-relative paths while ``git ls-files``
    prints cwd-relative ones, so both are normalised by stripping the
    ``quant-lab/`` prefix that the former carries.
    """
    return [
        line.removeprefix("quant-lab/")
        for line in _git(*args).splitlines()
        if line.strip()
    ]


def _repo_git(*args: str) -> str:
    """Run ``git`` from the repository root.

    Used only for the tracked-Python count, which must reproduce the I11R2
    governance binding audit's own scan exactly: that test runs ``git ls-files
    '*.py'`` from the repository root, so a quant-lab cwd would count only the
    sub-tree and disagree with the artifact it is checking.
    """
    result = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout


def test_only_the_authorized_paths_were_added_since_the_i05_base() -> None:
    """Protected-file diff audit: every path this checkpoint touches is I05-legal.

    Three custody views are audited separately because they answer different
    questions:

    DISCLOSED B5-I08 EXTENSION (SENSOR-B5-I08E1 directive): the staged-view
    allowlist adds the two paths the I08E1 directive authorizes staging --
    ``normalization/common/`` (bloc_05/03 §21 required surface) and the
    ``test_b5_i08_`` suites -- on the exact precedent by which this same
    list already grew ``normalization/time/`` and ``test_b5_i05_`` at I05.
    No other prefix is touched.

    DISCLOSED B5-I09 EXTENSION (SENSOR-B5-I09E1 directive; full record in
    ``BLOC_05_I09_IMPLEMENTATION_EVIDENCE.md`` + ledger section 178): the
    staged-view allowlist adds exactly one prefix, the ``test_b5_i09`` suites,
    on the same precedent by which it grew ``test_b5_i02_``/``test_b5_i04_``/
    ``test_b5_i05_``/``test_b5_i08``.  The ``normalization/common/`` prefix
    already covers I09's three new modules and the ``research/.../scripts/``
    and ``research/.../evidence/bloc_05/`` prefixes already cover the I09
    producer and its artifact.  No other prefix is touched.

    * STAGED (index vs the I05 base) is what a commit would ship, so it must
      fall inside the I05-authorized prefixes, plus exactly one disclosed
      exception: the mechanically republished I11R2 governance audit
      (directive section 07), whose own change is pinned by
      :func:`test_the_governance_audit_republish_is_mechanical_only`.
    * UNSTAGED (worktree vs index) may additionally carry regenerable dirt
      that earlier suites leave on historical Bloc 04 evidence -- the exact
      hazard section 07 names.  It must stay inside that evidence tree and
      never reach the index.
    * UNTRACKED must already be an I05-authorized path.
    """
    allowed_prefixes = (
        "src/crypto_sensor_fabric/normalization/time/",
        "src/crypto_sensor_fabric/normalization/common/",
        "tests/crypto_sensor_fabric/normalization/test_b5_i05_",
        "tests/crypto_sensor_fabric/normalization/test_b5_i08",
        "tests/crypto_sensor_fabric/normalization/test_b5_i09",
        "tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py",
        "config/crypto_sensor_fabric/provider_time_semantics.yaml",
        "config/crypto_sensor_fabric/revision_policies.yaml",
        "research/crypto_foundry/sensor_fabric/scripts/",
        "research/crypto_foundry/sensor_fabric/evidence/bloc_05/",
        "research/crypto_foundry/sensor_fabric/SENSOR_FABRIC_"
        "IMPLEMENTATION_PROGRESS.md",
    )

    def _authorized(path: str) -> bool:
        return path.startswith(allowed_prefixes)

    staged = _quant_lab_paths("diff", "--cached", "--name-only", I05_BASE_HEAD)
    unstaged = _quant_lab_paths("diff", "--name-only")
    untracked = _quant_lab_paths("ls-files", "--others", "--exclude-standard")

    unauthorized_staged = [
        path
        for path in sorted(set(staged))
        if not (_authorized(path) or path == I11R2_AUDIT)
    ]
    assert unauthorized_staged == [], (
        f"unauthorized changes staged for commit: {unauthorized_staged}"
    )

    unauthorized_unstaged = [
        path
        for path in sorted(set(unstaged))
        if not (
            _authorized(path) or path.startswith(SIDE_EFFECT_PREFIX)
        )
    ]
    assert unauthorized_unstaged == [], (
        f"unauthorized worktree changes: {unauthorized_unstaged}"
    )

    unauthorized_untracked = [
        path for path in sorted(set(untracked)) if not _authorized(path)
    ]
    assert unauthorized_untracked == [], (
        f"unauthorized untracked paths: {unauthorized_untracked}"
    )


def test_the_governance_audit_republish_is_mechanical_only() -> None:
    """The one allowed historical rewrite is exactly the tracked-Python count.

    Directive section 07 authorizes recalculation of the tracked-Python
    baseline "after staging authorized additions" through the established
    mechanical republish mechanism only.  So the I11R2 audit may differ from
    the I05 base in NOTHING but its ``python_files_scanned`` line, and that
    line must equal the number of Python files the index actually tracks.
    """
    # NOTE the pathspec is quant-lab-relative: ``_git`` already runs from
    # ``quant-lab``, and unlike diff OUTPUT (repo-root-relative) a pathspec
    # argument is resolved against the subprocess cwd.
    diff = _git("diff", "--cached", I05_BASE_HEAD, "--", I11R2_AUDIT)
    changed = [
        line
        for line in diff.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    assert len(changed) == 2, f"non-mechanical I11R2 rewrite: {changed}"
    removed, added = changed
    assert removed.startswith("-") and added.startswith("+")
    assert "python_files_scanned" in removed, changed
    assert "python_files_scanned" in added, changed

    payload = json.loads((_QUANT_LAB / I11R2_AUDIT).read_text(encoding="utf-8"))
    tracked_python = [
        line for line in _repo_git("ls-files", "*.py").splitlines() if line.strip()
    ]
    assert payload["python_files_scanned"] == len(tracked_python)
