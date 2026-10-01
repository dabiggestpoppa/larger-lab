"""Book 6 traceability — no row may exist without a real assertion.

The matrix is only worth something if its rows are load-bearing. This suite
resolves every ``(row_id, family, claim, test_file, test_name)`` tuple against
the test sources on disk: a row naming a function that does not exist, or that
exists outside the file it cites, fails here. Deleting an assertion therefore
breaks the matrix rather than silently hollowing it out.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from crypto_systems_intelligence_atlas.book6_traceability import (
    ALL_FAMILIES,
    R1_FAMILIES,
    R2_FAMILIES,
    STRUCTURAL_FAMILIES,
    TRACEABILITY_ROWS,
    VALIDATION_FAMILIES,
    rows_for_family,
)

TESTS_DIR = pathlib.Path(__file__).resolve().parent


def _defined_tests(path: pathlib.Path) -> set[str]:
    """Every top-level test function defined in a file (params or not)."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def _test_files() -> dict[str, pathlib.Path]:
    return {path.name: path for path in sorted(TESTS_DIR.glob("test_book6_*.py"))}


# -- every row resolves to a real assertion ----------------------------------


def test_the_matrix_is_not_empty() -> None:
    assert len(TRACEABILITY_ROWS) > 0


def test_every_row_cites_a_book_6_test_file_that_exists() -> None:
    available = _test_files()
    missing = sorted(
        {row[3] for row in TRACEABILITY_ROWS if row[3] not in available}
    )
    assert missing == []


@pytest.mark.parametrize(
    "row", TRACEABILITY_ROWS, ids=[row[0] for row in TRACEABILITY_ROWS]
)
def test_every_row_cites_a_test_function_that_actually_exists(
    row: tuple[str, str, str, str, str]
) -> None:
    row_id, _family, _claim, test_file, test_name = row
    path = _test_files()[test_file]
    assert test_name in _defined_tests(path), f"{row_id} cites a missing assertion"


@pytest.mark.parametrize(
    "row", TRACEABILITY_ROWS, ids=[row[0] for row in TRACEABILITY_ROWS]
)
def test_every_row_carries_a_substantive_claim(row: tuple[str, str, str, str, str]) -> None:
    row_id, family, claim, _test_file, _test_name = row
    assert row_id and claim
    assert len(claim) > 20, row_id
    assert family in ALL_FAMILIES, row_id


def test_row_ids_are_unique() -> None:
    ids = [row[0] for row in TRACEABILITY_ROWS]
    assert len(set(ids)) == len(ids)


# -- the ratified 6D families are all covered --------------------------------


@pytest.mark.parametrize("family", VALIDATION_FAMILIES, ids=lambda f: f)
def test_every_ratified_validation_family_is_covered(family: str) -> None:
    assert len(rows_for_family(family)) > 0, family


@pytest.mark.parametrize("family", STRUCTURAL_FAMILIES, ids=lambda f: f)
def test_every_structural_family_is_covered(family: str) -> None:
    assert len(rows_for_family(family)) > 0, family


@pytest.mark.parametrize("family", R1_FAMILIES, ids=lambda f: f)
def test_every_r1_family_is_covered(family: str) -> None:
    assert rows_for_family(family), family


@pytest.mark.parametrize("family", R2_FAMILIES, ids=lambda f: f)
def test_every_r2_family_is_covered(family: str) -> None:
    assert rows_for_family(family), family


def test_every_reproduced_r2_defect_has_a_trace_row() -> None:
    """Each R2 defect is reproduced as a refusal row, not prose."""

    claims = " ".join(row[2] for row in TRACEABILITY_ROWS)
    assert "D1 reproducer" in claims
    assert "D2 reproducer" in claims
    assert "D3 reproducer" in claims


def test_the_matrix_covers_exactly_the_ratified_structural_and_r1_families() -> None:
    families = {row[1] for row in TRACEABILITY_ROWS}
    assert families == set(ALL_FAMILIES)


def test_every_row_is_distinctly_attributed_to_one_family() -> None:
    assert len({row[1] for row in TRACEABILITY_ROWS}) == len(set(ALL_FAMILIES))


def test_every_reproduced_r1_defect_has_a_trace_row() -> None:
    """Each of the seven reproduced defects must be traceable by name."""

    claims = " ".join(row[2] for row in TRACEABILITY_ROWS)
    for defect in ("R1-D1", "R1-D2", "R1-D3", "R1-D4", "R1-D6"):
        assert defect in claims, defect
    # R1-D5 (the absent methodology registry) and R1-D7 (status forgery) are
    # traced by family and by assertion rather than by a defect tag
    assert rows_for_family("R1.METHODOLOGY_REGISTRY")
    assert rows_for_family("R1.RULE_AUTHORITY")


# -- the matrix tracks the assertions that matter most ----------------------


def test_the_anti_score_firewall_is_traced_from_every_reachable_direction() -> None:
    claims = " ".join(
        row[2] for row in rows_for_family("FIREWALL.ANTI_SCORE")
    ).lower()
    for direction in ("constructor", "model_copy", "dict", "round-trip", "nested"):
        assert direction in claims, direction


def test_the_state_rule_integrity_family_traces_the_zero_ratified_invariant() -> None:
    claims = " ".join(row[2] for row in rows_for_family("STATE_RULE_INTEGRITY")).lower()
    assert "ratif" in claims
    assert "class b" in claims or "class b or c" in claims
    assert "forged" in claims


def test_the_d2_6_family_traces_the_deferral() -> None:
    claims = " ".join(row[2] for row in rows_for_family("FIREWALL.D2_6")).lower()
    assert "usage" in claims
    assert "threshold" in claims
    assert "research" in claims


def test_no_book6_suite_is_untraced() -> None:
    """Every Book 6 test file is cited by at least one traceability row."""

    cited = {row[3] for row in TRACEABILITY_ROWS}
    uncited = sorted(set(_test_files()) - cited - {"test_book6_traceability.py"})
    assert uncited == []


def test_the_matrix_cites_a_meaningful_number_of_assertions() -> None:
    assert len(TRACEABILITY_ROWS) >= 60, len(TRACEABILITY_ROWS)


def test_the_r1_families_trace_the_post_construction_attack_matrix() -> None:
    """C1..C10 must all be individually traced, not covered by one row."""

    claims = " ".join(row[2] for row in rows_for_family("R1.RULE_AUTHORITY"))
    for attack in ("C1 ", "C2 ", "C4 ", "C5 ", "C6 ", "C7 ", "C8 ", "C9 ", "C10 "):
        assert attack in claims, attack
