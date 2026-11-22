"""
Unit test executing the evaluation benchmark on the curated evaluation dataset.
Asserts quality thresholds on Hit Rate@1, Hit Rate@3, MRR, and domain isolation.
"""

import pytest
from app.services.retrieval.evaluator import RetrievalEvaluator


def test_evaluation_benchmark():
    evaluator = RetrievalEvaluator()
    summary = evaluator.run_evaluation()

    assert summary["total_queries"] > 0
    assert summary["positive_queries"] > 0
    assert summary["negative_queries"] > 0

    # Strict domain isolation check across all queries
    assert summary["domain_leakage_violations"] == 0, (
        f"Domain leakage occurred in {summary['domain_leakage_violations']} instances!"
    )

    # Negative query rejection should be 100%
    assert summary["negative_rejection_accuracy"] == 1.0, (
        f"Negative queries leaked evidence: {summary['negative_rejection_accuracy']}"
    )

    # Retrieval quality checks
    assert summary["hit_rate_at_1"] >= 0.80, (
        f"Hit Rate@1 is below threshold: {summary['hit_rate_at_1']:.2f}"
    )
    assert summary["hit_rate_at_3"] >= 0.85, (
        f"Hit Rate@3 is below threshold: {summary['hit_rate_at_3']:.2f}"
    )
    assert summary["mean_reciprocal_rank"] >= 0.80, (
        f"MRR is below threshold: {summary['mean_reciprocal_rank']:.2f}"
    )
