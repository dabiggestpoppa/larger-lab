"""Independence (G1 §6) — vector preserved, raw reviewers != effective lineages,
allocation origin observable, summary marked non-authoritative."""
from engine.independence import IndependenceRecord, INDEPENDENCE_DIMENSIONS


def test_correlated_swarm_raw_vs_lineages():
    rec = IndependenceRecord.make(
        seq=1, raw_reviewers=10, distinct_source_lineages=1, distinct_model_families=1,
        distinct_retrieval_bundles=1,
        overlaps={"source_overlap": "HIGH", "model_family_overlap": "HIGH",
                  "retrieval_overlap": "HIGH", "allocator_overlap": "HIGH"},
    )
    s = rec.summary
    assert s["RAW_REVIEWERS"] == 10
    assert s["DISTINCT_SOURCE_LINEAGES"] == 1
    assert s["DISTINCT_MODEL_FAMILIES"] == 1
    assert s["DISTINCT_RETRIEVAL_BUNDLES"] == 1
    # deliberately NOT a fabricated effective sample size
    assert s["effective_independence"] == "NOT_AUTHORITATIVE_UNKNOWN"


def test_vector_preserved_all_dimensions():
    rec = IndependenceRecord.make(seq=2, raw_reviewers=3, overlaps={"source_overlap": "LOW"})
    assert set(rec.overlaps) == set(INDEPENDENCE_DIMENSIONS)
    assert rec.overlaps["source_overlap"] == "LOW"
    assert rec.overlaps["allocator_overlap"] == "UNKNOWN"


def test_invalid_grade_rejected():
    try:
        IndependenceRecord.make(seq=3, overlaps={"source_overlap": "TOTALLY"})
        raise AssertionError("invalid independence grade must be rejected")
    except ValueError:
        pass


def test_allocator_origin_observable():
    rec = IndependenceRecord.make(seq=4, raw_reviewers=2)
    rec.add_reviewer("r1", producing_actor="A", assigning_actor="PO", source_lineage="S1")
    rec.add_reviewer("r2", producing_actor="B", assigning_actor="PO", source_lineage="S2")
    assert rec.allocator_concentration() == "SINGLE_ALLOCATOR"
    # provenance fields retained, not a validity verdict
    assert rec.reviewers[0]["assigning_actor"] == "PO"


def test_experimental_summary_non_authoritative():
    rec = IndependenceRecord.make(seq=5, raw_reviewers=10, distinct_source_lineages=5,
                                  distinct_model_families=2, distinct_retrieval_bundles=4,
                                  overlaps={"allocator_overlap": "HIGH"})
    # heuristic exists but is labeled; raw vector unchanged by calling it
    est = rec.experimental_effective_lineages()
    assert est >= 1.0
    assert rec.raw_reviewers == 10