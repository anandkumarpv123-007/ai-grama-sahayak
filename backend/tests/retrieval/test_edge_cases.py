"""
Unit tests for edge cases, confidence thresholds, and error handling.
Verifies empty results for irrelevant queries, invalid assistant rejection,
and strict demo fixture isolation.
"""

import pytest
from app.services.retrieval import retrieve_context, RetrievalService
from app.services.retrieval.indexer import HybridMultilingualIndexer


def test_invalid_assistant_identifier():
    """
    Must raise ValueError when given an unsupported assistant identifier.
    """
    with pytest.raises(ValueError, match="Invalid assistant 'finance'"):
        retrieve_context(
            query="Tell me about loans",
            assistant="finance",
            language="en",
        )

    with pytest.raises(ValueError, match="Invalid assistant 'crypto'"):
        retrieve_context(
            query="Bitcoin price",
            assistant="crypto",
            language="en",
        )


def test_empty_or_whitespace_query():
    """
    Must return empty list for empty or whitespace-only queries.
    """
    assert retrieve_context(query="", assistant="agriculture", language="en") == []
    assert retrieve_context(query="   ", assistant="healthcare", language="en") == []
    assert retrieve_context(query="\n\t", assistant="education", language="te") == []


def test_irrelevant_query_returns_empty():
    """
    Must return empty list when no relevant official evidence exists.
    Prevents hallucination by avoiding returning random weakly-matching chunks.
    """
    # Irrelevant English queries
    results_crypto = retrieve_context(
        query="how to buy bitcoin cryptocurrency with credit card",
        assistant="schemes",
        language="en",
    )
    assert results_crypto == [], f"Expected [] for crypto query, got {len(results_crypto)} chunks"

    results_space = retrieve_context(
        query="NASA Apollo lunar landing trajectory calculations",
        assistant="agriculture",
        language="en",
    )
    assert results_space == [], f"Expected [] for space query, got {len(results_space)} chunks"

    # Irrelevant Telugu queries
    results_te_unrelated = retrieve_context(
        query="చంద్రుని పైకి రాకెట్ ఎలా ప్రయోగించాలి రోదసి యాత్ర",
        assistant="education",
        language="te",
    )
    assert results_te_unrelated == [], f"Expected [] for Telugu space query, got {len(results_te_unrelated)} chunks"


def test_demo_fixture_isolation_in_production():
    """
    Ensures synthetic test fixtures in knowledge_base/demo/ are never returned
    during normal production retrieval.
    """
    results = retrieve_context(
        query="Synthetic Demo Scheme Testing Fixture",
        assistant="schemes",
        language="en",
    )
    # None of the returned chunks should have status 'demo' or mention synthetic demo fixture
    for chunk in results:
        assert chunk["metadata"].get("status") != "demo"
        assert "synthetic" not in chunk["title"].lower()


def test_empty_indexer_behavior():
    """
    Ensures indexer functions safely even with an empty chunk collection.
    """
    empty_indexer = HybridMultilingualIndexer()
    empty_indexer.index_chunks([])

    results = empty_indexer.search(
        query="test query",
        assistant="agriculture",
        language="en",
    )
    assert results == []
