"""Head-to-head regression test for basic vs rich feature-engine equivalence.

Both engines feed the same ``FEATURE_COLUMNS`` model vector, so they must be
decision-equivalent. This test pins that invariant on a deterministic,
labeled customer corpus so any divergence in the mapping or feature
computation surfaces as a failure. See ``compare_modes.py`` for the full
argument about why equivalence justifies keeping ``basic`` as the default.
"""

from __future__ import annotations

from veripay_analyst_api.compare_modes import evaluate, generate_timelines


def test_modes_are_model_input_equivalent() -> None:
    rows = generate_timelines(n_customers=120, seed=7)
    comparison = evaluate(rows, threshold=50)

    # The two engines must produce byte-identical model vectors on every row.
    assert comparison.vectors_identical
    assert comparison.vector_mismatches == 0

    # Because the vectors are identical, decisions cannot diverge.
    assert comparison.decisions_differ == 0
    assert comparison.basic_fpr == comparison.rich_fpr
    assert comparison.basic_catch == comparison.rich_catch


def test_corpus_is_informative() -> None:
    """The generated corpus must contain both classes so FPR/catch are real."""
    rows = generate_timelines(n_customers=120, seed=7)
    comparison = evaluate(rows, threshold=50)

    assert comparison.fraud > 0
    assert comparison.total - comparison.fraud > 0
    assert 0.0 < comparison.basic_fpr < 1.0
    assert 0.0 < comparison.basic_catch < 1.0
