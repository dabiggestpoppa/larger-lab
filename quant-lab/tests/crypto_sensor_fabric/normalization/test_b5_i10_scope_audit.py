"""SENSOR-B5-I10E1 - scope audit for the trade-normalizer checkpoint.

A checkpoint that proves what it added has also to prove what it did not.
This is the I10 counterpart of the I01/I02/I03/I05/I08/I09 scope audits: the
``normalization/sensors/`` tree is exactly the three authorized modules, the
ratified 24-symbol I01 top-level API is unchanged (the sensor surface is reached
only through ``...normalization.sensors``), the sealed identity/terms/time/common
trees and the frozen plan are byte-identical to the I10 base, the six previously
disclosed scope-audit/producer extensions stay the only pre-existing edits, no
program gate is promoted, and the container an I10 artifact would occupy is not
invented.

The base commit is the directive-required starting HEAD.

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
_SENSORS = _PACKAGE / "sensors"
_EVIDENCE = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)
_I10_FIXTURES = _QUANT_LAB / "tests" / "crypto_sensor_fabric" / "fixtures" / "i10"

#: Directive-required starting HEAD == this checkpoint's custody base.
I10_BASE_HEAD = "8fc2ba00f849670e4975c843ffba815fe55e53f6"

#: DISCLOSED B5-I11 (SENSOR-B5-I11E1 directive section 07): the I11E1 pass adds
#: ``normalization/sensors/liquidation.py``, the authorized extension of the
#: ``sensors/`` namespace on the same precedent this audit already records.  The
#: set stays EXACT -- a fifth module is still an unapproved surface -- so this
#: amendment widens the membership by exactly one named file.
FROZEN_MODULES = [
    "__init__.py",
    "liquidation.py",
    "side_maps.py",
    "trade.py",
    # DISCLOSED SENSOR-B5-I09P2c: the full-record trusted verification surface
    # (trusted context, custody boundary, intraday PIT). It is named here by its
    # own entry; it is not a normalizer and mints no canonical value.
    "verification.py",
]

#: The frozen eight-member SensorFamily is untouched (R6).
FROZEN_SENSOR_FAMILIES = [
    "MECHANICAL_BASIS",
    "MECHANICAL_BOOK_METRIC",
    "MECHANICAL_BOOK_SNAPSHOT",
    "MECHANICAL_FUNDING",
    "MECHANICAL_LIQUIDATION",
    "MECHANICAL_OPEN_INTEREST",
    "MECHANICAL_POSITIONING",
    "MECHANICAL_TRADE",
]


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
        for path in sorted(_SENSORS.glob("*.py"))
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
# A10-03 -- approved module scope
# ---------------------------------------------------------------------------


def test_sensors_package_exists() -> None:
    assert _SENSORS.is_dir()


def test_sensors_package_is_exactly_the_four_authorized_modules() -> None:
    """The authorized modules, each a disclosed checkpoint surface."""
    files = sorted(entry.name for entry in _SENSORS.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_no_frozen_common_or_top_level_module_was_added() -> None:
    """A11/A12 constraint: I10 adds nothing to ``common/`` or the package root."""
    common = sorted(
        entry.name for entry in (_PACKAGE / "common").iterdir() if entry.suffix == ".py"
    )
    assert common == [
        "__init__.py",
        "comparability.py",
        "conversion.py",
        "methodologies.py",
        "numeric.py",
        "semantic_registry.py",
        "units.py",
    ]
    top = sorted(entry.name for entry in _PACKAGE.iterdir() if entry.suffix == ".py")
    assert top == ["__init__.py", "enums.py", "models.py"]


def test_no_competing_provider_mapping_registry_was_invented() -> None:
    """R1: no new semantic YAML, and no second registry module.

    DISCLOSED SENSOR-B5-I09P2A: the authorized approval manifest is one JSON file
    in exactly one new directory.  It approves ZERO artifacts, and a second
    semantic registry YAML is still refused -- the prohibition this test exists
    for is unchanged; only the directory it named is now the approved location.
    """
    semantics = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_semantics"
    assert not sorted(semantics.glob("*.yaml")), "a second semantic registry YAML appeared"
    assert sorted(entry.name for entry in semantics.iterdir()) == [
        "approval_manifest.json"
    ]
    for forbidden in ("side_maps.py", "trade.py", "sensors"):
        assert not (_QUANT_LAB / "config" / "crypto_sensor_fabric" / forbidden).exists()


def test_the_frozen_sensor_family_vocabulary_is_unchanged() -> None:
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    assert sorted(member.value for member in SensorFamily) == FROZEN_SENSOR_FAMILIES


def test_no_frozen_enum_was_duplicated_in_the_sensor_tree() -> None:
    """R3: existing frozen enums are reused, never re-declared."""
    for name, text in _sources().items():
        for forbidden in (
            "class AggressorSide(",
            "class SensorFamily(",
            "class AggregationType(",
            "class NormalizationStatus(",
            "class MissingnessReason(",
            "class NormalizationQualityFlag(",
            "class SemanticConfidence(",
        ):
            assert forbidden not in text, f"{name} re-declares {forbidden}"


def test_the_unfinished_composite_envelope_is_not_exported() -> None:
    import crypto_sensor_fabric.normalization.sensors as sensors

    assert "T1ObservationEnvelope" not in sensors.__all__
    assert not hasattr(sensors, "T1ObservationEnvelope")


# ---------------------------------------------------------------------------
# A10-20 -- ratified surfaces are untouched
# ---------------------------------------------------------------------------


def test_ratified_i01_top_level_api_is_unchanged() -> None:
    """A4/A5: the sensor surface never rides on the ratified root API."""
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in (
        "normalize_trade",
        "T1TradeRecord",
        "TradeObservationInput",
        "SideEvidence",
        "ProvisionalSideMapping",
    ):
        assert absent not in normalization.__all__, absent
        assert not hasattr(normalization, absent), absent


def test_sealed_trees_are_untouched_relative_to_the_i10_base() -> None:
    diff = _git(
        "diff",
        I10_BASE_HEAD,
        "--",
        "src/crypto_sensor_fabric/normalization/identity",
        "src/crypto_sensor_fabric/normalization/terms",
        "src/crypto_sensor_fabric/normalization/time",
        "src/crypto_sensor_fabric/normalization/common",
        "src/crypto_sensor_fabric/normalization/__init__.py",
        "src/crypto_sensor_fabric/normalization/enums.py",
        "src/crypto_sensor_fabric/normalization/models.py",
        "src/crypto_sensor_fabric/registry",
        "src/crypto_sensor_fabric/schemas",
        "config/crypto_sensor_fabric",
        # DISCLOSED SENSOR-B5-I09P2A: the authority loader and its manifest are
        # the checkpoint's authorized NEW surfaces, not edits to a sealed file.
        ":(exclude)src/crypto_sensor_fabric/normalization/common/authority.py",
        ":(exclude)config/crypto_sensor_fabric/provider_semantics",
    )
    assert diff == "", f"sealed tree changed:\n{diff}"


def test_the_frozen_plan_is_byte_identical_to_the_i10_base() -> None:
    diff = _git("diff", I10_BASE_HEAD, "--", "research/crypto_foundry/sensor_fabric/bloc_05")
    assert diff == "", diff


def test_no_ninth_evidence_artifact_was_added() -> None:
    """bloc_05/06 section 17's frozen artifact list contains no trade artifact.

    Machine-checked form: the set of generated ``bloc_05_*.json`` artifacts is
    identical to the base commit's.
    """
    before = {
        line.rsplit("/", 1)[-1]
        for line in _git(
            "ls-tree",
            "-r",
            "--name-only",
            I10_BASE_HEAD,
            "--",
            "research/crypto_foundry/sensor_fabric/evidence/bloc_05",
        ).splitlines()
        if line.strip()
    }
    after = {path.name for path in _EVIDENCE.iterdir()}
    added = {
        name
        for name in after - before
        if name.startswith("bloc_05_") and name.endswith(".json")
    }
    assert added == set(), f"invented evidence artifacts: {sorted(added)}"


def test_no_program_gate_is_promoted() -> None:
    matrix = json.loads(
        (_EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json").read_text(encoding="utf-8")
    )
    gates = matrix["bloc_05_blocking_gates"]
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate
    assert "PASS" not in json.dumps(gates)


# ---------------------------------------------------------------------------
# Dependency firewall and purity
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
        "yaml",
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


def test_no_duplicate_collapse_engine_exists() -> None:
    """R5: collapse belongs to I17; I10 must not ship a dedupe engine."""
    for name, text in _sources().items():
        for forbidden in (
            "def collapse",
            "def dedupe",
            "def deduplicate",
            "def fingerprint",
            "DUPLICATE_CONFIRMED =",
        ):
            assert forbidden not in text, f"{name} ships {forbidden}"


def test_the_side_map_never_reads_price() -> None:
    """F17 / OP-T10-A02: side is never inferred from price direction."""
    text = (_SENSORS / "side_maps.py").read_text(encoding="utf-8")
    assert "price" not in text.lower()


def test_no_program_gate_or_acceptance_language_in_the_new_package() -> None:
    for name, text in _sources().items():
        for forbidden in ("OPERATOR_ACCEPTED", "IMPLEMENTATION_PASS", "_GATE ="):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# A10-17/A10-20 -- deterministic, provenance-labeled fixtures
# ---------------------------------------------------------------------------


def test_the_two_authorized_fixtures_exist_and_are_provenance_labeled() -> None:
    expected = ["binance_aggtrades_side_cases.json", "trade_side_refusals.json"]
    files = sorted(entry.name for entry in _I10_FIXTURES.iterdir())
    assert files == expected
    for name in expected:
        payload = json.loads((_I10_FIXTURES / name).read_text(encoding="utf-8"))
        provenance = payload["provenance"]
        assert provenance["source"] in {"operator-frozen", "minimized-without-semantic-mutation"}
        assert provenance["authoritative_for"]
        assert provenance["not_authoritative_for"]
        assert "SYNTHETIC" in provenance["provenance_class"]


def test_no_fixture_claims_to_be_a_captured_provider_payload() -> None:
    for entry in _I10_FIXTURES.iterdir():
        text = entry.read_text(encoding="utf-8").lower()
        for forbidden in ("captured payload", "recorded response from", "live capture"):
            assert forbidden not in text, f"{entry.name} claims {forbidden}"


def test_fixtures_are_deterministic_on_disk() -> None:
    """Sorted keys and no authored timestamps keep the fixtures byte-stable."""
    for entry in _I10_FIXTURES.iterdir():
        text = entry.read_text(encoding="utf-8")
        payload = json.loads(text)
        assert payload == json.loads(json.dumps(payload, sort_keys=True))
        assert "\r" not in text


# ---------------------------------------------------------------------------
# A10-24 -- the governed commit surface
# ---------------------------------------------------------------------------


ALLOWED_PREFIXES = (
    "src/crypto_sensor_fabric/normalization/sensors/",
    # DISCLOSED SENSOR-B5-I09P2A: the loader module, the empty approval
    # manifest and the authority suite are this checkpoint's named surfaces.
    "src/crypto_sensor_fabric/normalization/authority/",
    "config/crypto_sensor_fabric/provider_semantics/",
    "tests/crypto_sensor_fabric/normalization/test_b5_i09p2a_",
    # DISCLOSED SENSOR-B5-I09P2b: the trusted-root/provenance security
    # suite is a distinct checkpoint file under the authority prefix
    # family, admitted by its own named entry.
    "tests/crypto_sensor_fabric/normalization/test_b5_i09p2b_",
    # DISCLOSED SENSOR-B5-I09P2c: the full-record verification, custody and
    # intraday-PIT security suite is a distinct checkpoint file under the
    # authority prefix family, admitted by its own named entry.
    "tests/crypto_sensor_fabric/normalization/test_b5_i09p2c_",
    # DISCLOSED SENSOR-B5-I09P2d: the custody-authority, scoped-verdict and
    # PIT-fail-closure security suite is a distinct checkpoint file under
    # the same authority prefix family, admitted by its own named entry.
    "tests/crypto_sensor_fabric/normalization/test_b5_i09p2d_",
    # DISCLOSED SENSOR-B5-I09P2e: the PIT entry-parity probe suite is a
    # distinct checkpoint file under the same authority prefix family, so it
    # is admitted by its own named entry rather than by widening a prefix.
    "tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_",
    "tests/crypto_sensor_fabric/normalization/test_b5_i10_",
    "tests/crypto_sensor_fabric/normalization/test_b5_i11_",
    # DISCLOSED B5-I11R1 (independent audit): the audit suite is a
    # distinct checkpoint file under the I11 prefix family, so it is
    # admitted by its own named entry rather than by widening the
    # I11E1 prefix.
    "tests/crypto_sensor_fabric/normalization/test_b5_i11r1_",
    # DISCLOSED B5-I11F1 (semantic-admission repair): the security suite is
    # a distinct checkpoint file under the I11 prefix family, so it is
    # admitted by its own named entry rather than by widening an I11 prefix.
    "tests/crypto_sensor_fabric/normalization/test_b5_i11f1_",
    "tests/crypto_sensor_fabric/fixtures/i10/",
    "tests/crypto_sensor_fabric/fixtures/i11/",
    "tests/crypto_sensor_fabric/normalization/test_b5_i01_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i08_scope_audit.py",
    "tests/crypto_sensor_fabric/normalization/test_b5_i09_scope_audit.py",
    # DISCLOSED SENSOR-B5-I09P2A: SEM-32 measures the Bloc 1 registry
    # surface by changed path rather than by total emptiness, because the
    # trust root adds one config file.  Named individually, not by prefix.
    "tests/crypto_sensor_fabric/normalization/test_b5_i09_semantics.py",
    # the I06 replay-safety suite re-pins its disclosed src prefix and its
    # inventory-carrying artifact pin for this checkpoint (section 9.5 A17)
    "tests/crypto_sensor_fabric/normalization/test_b5_i05_i06_replay_safety/",
    "research/crypto_foundry/sensor_fabric/scripts/",
    "research/crypto_foundry/sensor_fabric/evidence/bloc_05/",
    "research/crypto_foundry/sensor_fabric/evidence/bloc_04/"
    "BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json",
    "research/crypto_foundry/sensor_fabric/"
    + "SENSOR_FABRIC_"
    + "IMPLEMENTATION_PROGRESS.md",
    # annotations/ignore files are custody plumbing, not content
    ".gitignore",
    ".gitattributes",
)


#: DISCLOSED SENSOR-B5-P3-MASTER-BUILD-R1 (operator directive
#: SENSOR-B5-P3-PRODUCTION-CONSUMER-MASTER-BUILD-R1,
#: AUTHORIZE_P3_RUNGS_1_THROUGH_5_BOUNDED): the bounded production consumer,
#: admitted by EXACT FILE.  A ``consumer/`` prefix would authorize any module
#: dropped into the package under this grant -- including a later rung's module
#: -- so the grant is a set, not a prefix, and every historical prefix and named
#: exception above stays exactly as it was.
P3_MASTER_EXACT_PATHS = frozenset(
    {
        "src/crypto_sensor_fabric/normalization/consumer/__init__.py",
        "src/crypto_sensor_fabric/normalization/consumer/models.py",
        "src/crypto_sensor_fabric/normalization/consumer/policy.py",
        "src/crypto_sensor_fabric/normalization/consumer/custody_authority.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_policy.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_custody.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_rebinding.py",
        "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py",
        # A scope audit must be able to name its own amendment, or it can never
        # be amended at all.  Named individually for that reason only.
        "tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py",
    }
)

#: Historical admission samples: paths the pre-existing prefixes already admit.
#: The counterexample audit proves the amendment did not narrow them.
HISTORICAL_ADMISSION_SAMPLES = (
    "src/crypto_sensor_fabric/normalization/sensors/trade.py",
    "src/crypto_sensor_fabric/normalization/authority/__init__.py",
    "config/crypto_sensor_fabric/provider_semantics/approval_manifest.json",
    "tests/crypto_sensor_fabric/normalization/test_b5_i10_trade_semantics.py",
    "research/crypto_foundry/sensor_fabric/evidence/bloc_05/README.md",
)


def _authorized(path: str) -> bool:
    """The admission predicate: historical prefixes, or an exact P3 file.

    The disjunction is the whole point.  ``path in P3_MASTER_EXACT_PATHS`` is an
    equality test, so ``consumer/models.py.backup`` and ``consumer/rebinding.py``
    are refused even though they live in the authorized directory.
    """
    return path.startswith(ALLOWED_PREFIXES) or path in P3_MASTER_EXACT_PATHS



def test_only_the_i10_authorized_prefixes_carry_tracked_changes() -> None:
    """Directive section 14's authorized file list, as a tracked-path audit.

    The disclosed custody amendments of I10D1 section 9.5 are admitted through
    their own named entries; every other path is refused.
    """
    def _quant_lab_paths(*args: str) -> list[str]:
        return [
            line.removeprefix("quant-lab/")
            for line in _git(*args).splitlines()
            if line.strip()
        ]

    def _paths(*args: str) -> list[str]:
        return [
            line.removeprefix("quant-lab/")
            for line in _git(*args).splitlines()
            if line.strip()
        ]

    # STAGED is what a commit would ship, so every staged path must be authorized.
    for path in _paths("diff", "--cached", "--name-only", I10_BASE_HEAD, "--"):
        assert _authorized(path), f"unauthorized staged path: {path}"

    # UNSTAGED may carry the documented Bloc 04 evidence side effects the
    # whole-package suite leaves behind.  Those are restored to their committed
    # bytes and never staged, so they cannot reach a commit -- the same
    # SIDE_EFFECT_PREFIX precedent the I05 audit already records for this tree.
    side_effects = "research/crypto_foundry/sensor_fabric/evidence/bloc_04/"
    for path in _paths("diff", "--name-only", "--"):
        assert _authorized(path) or path.startswith(side_effects), (
            f"unauthorized worktree change: {path}"
        )

    for path in _quant_lab_paths("ls-files", "--others", "--exclude-standard"):
        assert _authorized(path), path

# ---------------------------------------------------------------------------
# A4 -- the exact-file predicate, as executed counterexamples
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, admitted",
    [
        # admitted: the exact authorized surface, one entry at a time
        ("src/crypto_sensor_fabric/normalization/consumer/__init__.py", True),
        ("src/crypto_sensor_fabric/normalization/consumer/models.py", True),
        ("src/crypto_sensor_fabric/normalization/consumer/policy.py", True),
        ("src/crypto_sensor_fabric/normalization/consumer/custody_authority.py", True),
        (
            "tests/crypto_sensor_fabric/normalization/"
            "test_b5_p3_consumer_contracts.py",
            True,
        ),
        ("tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_policy.py", True),
        (
            "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_custody.py",
            True,
        ),
        (
            "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_rebinding.py",
            True,
        ),
        (
            "tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py",
            True,
        ),
        # refused: a suffix is not the file
        ("src/crypto_sensor_fabric/normalization/consumer/models.py.backup", False),
        ("src/crypto_sensor_fabric/normalization/consumer/models.py.orig", False),
        # refused: a module this grant did not name
        ("src/crypto_sensor_fabric/normalization/consumer/unapproved.py", False),
        ("src/crypto_sensor_fabric/normalization/consumer/schemas.py", False),
        # refused: rebinding stays private inside policy.py, so a module for it
        # is not authorized even though the design once contemplated one
        ("src/crypto_sensor_fabric/normalization/consumer/rebinding.py", False),
        # refused: a consumer subdirectory is not the package's flat surface
        ("src/crypto_sensor_fabric/normalization/consumer/internal/helpers.py", False),
        # refused: an unapproved P3 test filename
        ("tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_e2e.py", False),
        ("tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer.py", False),
        # refused: unrelated normalization modules and unrelated project files
        ("src/crypto_sensor_fabric/normalization/writer.py", False),
        ("src/crypto_sensor_fabric/normalization/consumer.py", False),
        ("quant-lab/README.md", False),
        ("AGENTS.md", False),
    ],
)
def test_p3_master_admission_is_exact_file_only(path: str, admitted: bool) -> None:
    assert _authorized(path) is admitted, (path, admitted)


@pytest.mark.parametrize("path", HISTORICAL_ADMISSION_SAMPLES)
def test_historical_admission_is_unchanged_by_the_p3_amendment(path: str) -> None:
    """The amendment adds a disjunct; it must not have removed one."""
    assert _authorized(path) is True, path


def test_the_p3_grant_names_no_directory_prefix() -> None:
    """A prefix in the grant would be a prefix, whatever the comment says."""
    for path in P3_MASTER_EXACT_PATHS:
        assert not path.endswith("/"), path
        assert "*" not in path, path
