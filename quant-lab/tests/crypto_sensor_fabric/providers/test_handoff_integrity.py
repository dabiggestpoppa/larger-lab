"""SENSOR-B3-I11 — handoff package integrity test (OFFLINE).

Proves:
1. every file path referenced by `BLOC_03_HANDOFF_INDEX.md` exists;
2. every evidence ref inside `PROVIDER_CAPABILITY_RUNTIME.json` resolves to a
   committed bloc_02 artifact.

A broken handoff reference is a FAIL — the handoff package is a reproducible
contract, not a pile of files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent
REPO_QUANT_LAB = TEST_ROOT.parents[2]

EVID = (
    REPO_QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_03"
)
INDEX = EVID / "BLOC_03_HANDOFF_INDEX.md"
CAPABILITY_RUNTIME = EVID / "PROVIDER_CAPABILITY_RUNTIME.json"
BLOC_02 = EVID.parent / "bloc_02"


def _referenced_paths() -> list[tuple[str, Path]]:
    """Extract (label, absolute path) pairs from the handoff index tables."""
    text = INDEX.read_text(encoding="utf-8")
    found: list[tuple[str, Path]] = []
    # Table cells and inline code paths containing a filename or relative path.
    for match in re.findall(r"`([^`]+\.(?:csv|json|md|yaml|py))`", text):
        rel = match.strip()
        # Relative to the index directory; resolve and verify containment.
        candidate = (EVID / rel).resolve()
        found.append((rel, candidate))
    # De-duplicate by absolute path.
    seen: set[Path] = set()
    out: list[tuple[str, Path]] = []
    for label, path in found:
        if path not in seen:
            seen.add(path)
            out.append((label, path))
    return out


def _evidence_ids_present(search_root: Path) -> set[str]:
    """Reuse the committed-evidence token scan (same heuristic as readiness)."""
    found: set[str] = set()
    for path in search_root.iterdir():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            tokens = line.replace(",", " ").replace('"', " ").split()
            for token in tokens:
                if ("_" in token or "-" in token) and (
                    "2021" in token
                    or "2022" in token
                    or "2024" in token
                    or "2026" in token
                    or "RECENT_CONTROL" in token
                    or "book_snapshot" in token
                    or "raw_event" in token
                    or "1h" in token
                ):
                    found.add(token.strip())
    return found


class TestHandoffPackageIntegrity:
    def test_index_exists(self) -> None:
        assert INDEX.is_file(), f"handoff index missing: {INDEX}"

    def test_every_index_referenced_file_exists(self) -> None:
        missing = [label for label, path in _referenced_paths() if not path.exists()]
        assert not missing, f"handoff index references missing files: {missing}"

    def test_index_references_are_within_quant_lab(self) -> None:
        root = REPO_QUANT_LAB.resolve()
        outside = [
            label
            for label, path in _referenced_paths()
            if root not in path.parents and path != root
        ]
        assert not outside, f"handoff index escapes quant-lab: {outside}"

    def test_core_artifacts_referenced(self) -> None:
        referenced = {path.name for _, path in _referenced_paths()}
        for core in (
            "FINAL_ADAPTER_READINESS_MATRIX.csv",
            "FINAL_ADAPTER_READINESS_MATRIX.json",
            "PROVIDER_CAPABILITY_RUNTIME.json",
            "PROVIDER_IMPLEMENTATION_REPORT.md",
            "KNOWN_FAILURES.md",
            "ACCESS_CLASS_REPORT.md",
            "OFFLINE_TEST_REPORT.json",
            "NETWORK_SMOKE_EVIDENCE_INDEX.md",
            "BLOC_04_INPUT_MANIFEST.md",
            "FIXTURE_COVERAGE_REPORT.json",
            "BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json",
            "PRODUCTION_ADAPTER_MATRIX.csv",
        ):
            assert core in referenced, f"handoff index missing core artifact {core}"

    def test_capability_runtime_evidence_refs_resolve(self) -> None:
        payload = json.loads(CAPABILITY_RUNTIME.read_text(encoding="utf-8"))
        assert "paths" in payload and payload["paths"]
        resolved = _evidence_ids_present(BLOC_02)
        unresolved: list[str] = []
        for row in payload["paths"]:
            for ref in row.get("evidence_refs", []):
                if ref not in resolved:
                    unresolved.append(
                        f"{row['provider_id']}/{row['sensor_family']}: {ref!r}"
                    )
        assert not unresolved, (
            "PROVIDER_CAPABILITY_RUNTIME evidence refs do not resolve to "
            f"committed bloc_02 artifacts: {unresolved}"
        )

    def test_capability_runtime_has_exactly_17_paths(self) -> None:
        payload = json.loads(CAPABILITY_RUNTIME.read_text(encoding="utf-8"))
        rows = payload["paths"]
        assert len(rows) == 17
        keys = {(r["provider_id"], r["sensor_family"]) for r in rows}
        assert len(keys) == 17, "duplicate provider x sensor in capability runtime"

    def test_final_matrix_rows_match_runtime_overlay(self) -> None:
        import csv as _csv

        matrix_rows = list(
            _csv.DictReader((EVID / "FINAL_ADAPTER_READINESS_MATRIX.csv").open(encoding="utf-8", newline=""))
        )
        overlay = json.loads(
            (EVID / "BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json").read_text(encoding="utf-8")
        )
        matrix_set = {(r["provider_id"], r["sensor_family"]) for r in matrix_rows}
        overlay_set = {(p["provider_id"], p["sensor_family"]) for p in overlay["paths"]}
        assert len(matrix_rows) == 17
        assert matrix_set == overlay_set == {  # exact-set across final surfaces
            (p["provider_id"], p["sensor_family"]) for p in overlay["paths"]
        }
        assert len(matrix_set) == 17
        assert len(overlay_set) == 17


# ---------------------------------------------------------------------------
# I11R1 — cross-surface SEMANTIC consistency (machine truth -> handoff).
#
# For every provider x sensor key, the authoritative fields must agree across
# the surfaces that describe the SAME epoch.  Fields that intentionally differ
# by epoch (I09 keeps adapter v1 for Gate/Kraken and network_smoke NOT_RUN;
# current surfaces carry v2 / PASS) are asserted for the EXPECTED value on
# each surface instead of naive equality — chronology is provenance, not drift.
# ---------------------------------------------------------------------------


def _load_final_matrix_json() -> list[dict[str, object]]:
    payload = json.loads((EVID / "FINAL_ADAPTER_READINESS_MATRIX.json").read_text(encoding="utf-8"))
    return list(payload["rows"])


def _load_capability_runtime() -> list[dict[str, object]]:
    payload = json.loads(CAPABILITY_RUNTIME.read_text(encoding="utf-8"))
    return list(payload["paths"])


def _load_overlay() -> list[dict[str, object]]:
    payload = json.loads((EVID / "BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json").read_text(encoding="utf-8"))
    return list(payload["paths"])


def _load_i09_matrix() -> list[dict[str, str]]:
    import csv as _csv

    return list(
        _csv.DictReader((EVID / "PRODUCTION_ADAPTER_MATRIX.csv").open(encoding="utf-8", newline=""))
    )


def _load_i14() -> list[dict[str, object]]:
    from crypto_sensor_fabric.providers.base.capabilities import load_promotion_candidates

    return load_promotion_candidates()


_SHORT_TO_FULL = {
    "BASIS": "MECHANICAL_BASIS",
    "BOOK_METRIC": "MECHANICAL_BOOK_METRIC",
    "BOOK_SNAPSHOT": "MECHANICAL_BOOK_SNAPSHOT",
    "FUNDING": "MECHANICAL_FUNDING",
    "LIQUIDATION": "MECHANICAL_LIQUIDATION",
    "OPEN_INTEREST": "MECHANICAL_OPEN_INTEREST",
    "POSITIONING": "MECHANICAL_POSITIONING",
    "TRADE": "MECHANICAL_TRADE",
}


class TestHandoffSemanticConsistency:
    """SENSOR-B3-I11R1: semantic equality across the handoff authority chain."""

    def _surfaces(self):
        # Build key -> row maps per surface.
        maps: dict[str, dict[tuple[str, str], dict[str, object]]] = {}

        def index(name: str, rows: list[dict[str, object]], pid_k: str, sensor_k: str) -> None:
            maps[name] = {}
            for row in rows:
                key = (str(row[pid_k]), str(row[sensor_k]))
                maps[name][key] = row

        index("i14", _load_i14(), "provider", "sensor")
        index("i09", _load_i09_matrix(), "provider_id", "sensor_family")
        index("capability", _load_capability_runtime(), "provider_id", "sensor_family")
        index("overlay", _load_overlay(), "provider_id", "sensor_family")
        index("final", _load_final_matrix_json(), "provider_id", "sensor_family")

        keys = set(maps["i14"])
        for name, m in maps.items():
            assert set(m) == keys, f"{name} surface key set != I14: {set(m) ^ keys}"
        assert len(keys) == 17
        return maps

    def test_exact_set_17_across_all_five_surfaces(self) -> None:
        maps = self._surfaces()
        keys = set(maps["i14"])
        assert len(keys) == 17
        providers = {p for p, _ in keys}
        assert providers == {"KRAKEN_FUTURES", "GATE_FUTURES", "OKX_SWAP", "DERIBIT"}
        assert len(providers) == 4, "fifth provider leaked into the handoff set"

    def test_role_equality_across_surfaces(self) -> None:
        """FINAL role == capability role == I09 role == I14 allowed_role (17 rows)."""
        maps = self._surfaces()
        for key in maps["i14"]:
            i14_role = str(maps["i14"][key].get("allowed_role", ""))
            assert i14_role, f"{key}: I14 allowed_role missing"
            for name in ("i09", "capability", "final"):
                got = str(maps[name][key].get("role", ""))
                assert got == i14_role, (
                    f"{key}: {name} role {got!r} != I14 allowed_role {i14_role!r}"
                )

    def test_okx_role_adversarial(self) -> None:
        """OKX: BOOK_SNAPSHOT=CURRENT_ONLY, FUNDING=PRIMARY, TRADE=PRIMARY."""
        maps = self._surfaces()
        expected = {
            "MECHANICAL_BOOK_SNAPSHOT": "CURRENT_ONLY",
            "MECHANICAL_FUNDING": "PRIMARY",
            "MECHANICAL_TRADE": "PRIMARY",
        }
        for sensor, role in expected.items():
            for name in ("i14", "i09", "capability", "final"):
                row = maps[name][("OKX_SWAP", sensor)]
                field = "allowed_role" if name == "i14" else "role"
                assert str(row.get(field, "")) == role, (
                    f"OKX_SWAP/{sensor}: {name} {field} != {role}"
                )

    def test_symbol_scope_equality(self) -> None:
        """production_symbol_scope equal across i09/capability/final (normalized sets)."""
        maps = self._surfaces()

        def norm(value: object) -> frozenset[str]:
            if isinstance(value, list):
                return frozenset(str(v) for v in value)
            return frozenset(str(value).split("|")) if value else frozenset()

        for key in maps["i14"]:
            base = norm(maps["capability"][key].get("production_symbol_scope"))
            assert base, f"{key}: empty capability symbol scope"
            for name in ("i09", "final"):
                got = norm(maps[name][key].get("production_symbol_scope"))
                assert got == base, (
                    f"{key}: {name} symbol scope {sorted(got)} != capability {sorted(base)}"
                )

    def test_history_scope_equality(self) -> None:
        """history_scope equal across i14/i09/capability/overlay/final."""
        maps = self._surfaces()
        for key in maps["i14"]:
            base = str(maps["i14"][key].get("history_mode", ""))
            assert base, f"{key}: I14 history_mode missing"
            for name in ("i09", "capability", "overlay", "final"):
                got = str(maps[name][key].get("history_scope", ""))
                assert got == base, (
                    f"{key}: {name} history_scope {got!r} != I14 history_mode {base!r}"
                )

    def test_resume_completion_equality(self) -> None:
        """resume/completion equal across i09/capability/overlay/final."""
        maps = self._surfaces()
        for key in maps["i14"]:
            base_r = str(maps["i09"][key].get("resume_status", ""))
            base_c = str(maps["i09"][key].get("completion_status", ""))
            for name in ("capability", "overlay", "final"):
                assert str(maps[name][key].get("resume_status", "")) == base_r, (
                    f"{key}: {name} resume_status != I09 {base_r!r}"
                )
                assert str(maps[name][key].get("completion_status", "")) == base_c, (
                    f"{key}: {name} completion_status != I09 {base_c!r}"
                )

    def test_pit_and_methodology_equality(self) -> None:
        """pit_readiness + methodology_pin equal across i14/i09/capability/final."""
        maps = self._surfaces()
        for key in maps["i14"]:
            base_pit = str(maps["i14"][key].get("PIT_requirement", ""))
            base_pin = str(maps["i14"][key].get("methodology_pin", ""))
            for name in ("i09", "capability", "final"):
                assert str(maps[name][key].get("pit_readiness", "")) == base_pit, (
                    f"{key}: {name} pit_readiness != I14 {base_pit!r}"
                )
                assert str(maps[name][key].get("methodology_pin", "")) == base_pin, (
                    f"{key}: {name} methodology_pin != I14 {base_pin!r}"
                )

    def test_current_adapter_version_equality(self) -> None:
        """Current surfaces (capability/overlay/final) agree on adapter_version."""
        maps = self._surfaces()
        expected = {
            "GATE_FUTURES": "gate-adapter-v2",
            "KRAKEN_FUTURES": "kraken-adapter-v2",
            "OKX_SWAP": "okx-adapter-v1",
            "DERIBIT": "deribit-adapter-v1",
        }
        for key in maps["i14"]:
            pid = key[0]
            base = maps["capability"][key].get("adapter_version")
            assert base == expected[pid], f"{key}: capability version {base!r}"
            for name in ("overlay", "final"):
                got = maps[name][key].get("adapter_version")
                assert got == base, f"{key}: {name} adapter_version {got!r} != {base!r}"

    def test_i09_keeps_v1_provenance(self) -> None:
        """Chronology: I09 keeps v1 for repaired Gate/Kraken; current = v2."""
        maps = self._surfaces()
        for sensor in ("MECHANICAL_FUNDING", "MECHANICAL_LIQUIDATION",
                       "MECHANICAL_OPEN_INTEREST", "MECHANICAL_POSITIONING"):
            i09_v = maps["i09"][("GATE_FUTURES", sensor)].get("adapter_version")
            assert str(i09_v) == "gate-adapter-v1", f"I09 Gate {sensor} version {i09_v!r}"
        for sensor in ("MECHANICAL_BASIS", "MECHANICAL_BOOK_METRIC",
                       "MECHANICAL_FUNDING", "MECHANICAL_LIQUIDATION",
                       "MECHANICAL_OPEN_INTEREST", "MECHANICAL_POSITIONING"):
            i09_v = maps["i09"][("KRAKEN_FUTURES", sensor)].get("adapter_version")
            assert str(i09_v) == "kraken-adapter-v1", f"I09 Kraken {sensor} version {i09_v!r}"
        for pid, v in (("OKX_SWAP", "okx-adapter-v1"), ("DERIBIT", "deribit-adapter-v1")):
            for sensor, row in maps["i09"].items():
                if sensor[0] == pid:
                    assert str(row.get("adapter_version")) == v, f"I09 {pid} {sensor} version"

    def test_network_validation_state(self) -> None:
        """Current surfaces: PASS; I09: NOT_RUN (chronology preserved)."""
        maps = self._surfaces()
        for key in maps["i14"]:
            assert str(maps["capability"][key].get("live_validation_status", "")) == "PASS"
            assert str(maps["overlay"][key].get("live_validation_status", "")) == "PASS"
            assert str(maps["final"][key].get("network_validation_status", "")) == "PASS"
            assert str(maps["i09"][key].get("network_smoke_status", "")) == "NOT_RUN"

    def test_deribit_limitations_are_path_specific(self) -> None:
        """No cross-sensor Deribit prose: funding must not carry trade/liq text."""
        maps = self._surfaces()
        for name in ("overlay", "final"):
            funding = str(maps[name][("DERIBIT", "MECHANICAL_FUNDING")].get("limitations", ""))
            assert "liquidation" not in funding.lower(), f"{name}: funding carries liq prose"
            assert "trade-event" not in funding.lower(), f"{name}: funding carries trade prose"
            liq = str(maps[name][("DERIBIT", "MECHANICAL_LIQUIDATION")].get("limitations", ""))
            assert "forced-liquidation" in liq.lower(), f"{name}: liq limitation missing microscope"
            trade = str(maps[name][("DERIBIT", "MECHANICAL_TRADE")].get("limitations", ""))
            assert "trade-event" in trade.lower(), f"{name}: trade limitation missing surface"

    def test_provider_report_role_table_matches_machine_truth(self) -> None:
        """Human report role table == final machine matrix (no second truth)."""
        report = (EVID / "PROVIDER_IMPLEMENTATION_REPORT.md").read_text(encoding="utf-8")
        missing: list[str] = []
        for row in _load_final_matrix_json():
            sensor = str(row["sensor_family"])
            short = sensor.replace("MECHANICAL_", "")
            token = f"{short}({row['role']})"
            if token not in report:
                missing.append(f"{row['provider_id']} {token}")
        assert not missing, (
            "PROVIDER_IMPLEMENTATION_REPORT role table diverges from final machine "
            f"matrix: {missing}"
        )
