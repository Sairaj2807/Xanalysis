"""Needs the cached ProsusAI/finbert weights (downloaded by scripts/score_sentiment.py). Skipped if unavailable."""
import numpy as np
import pytest

from sentiment.finbert_analyzer import FinBertAnalyzer

TEXTS = [
    "Apple reports record revenue and raises full-year guidance",
    "Company reported record losses and cut its outlook",
    "Apple scheduled to report earnings on Thursday after the close of the market and analysts expect",
    "ok",
]


@pytest.fixture(scope="module")
def analyzer():
    try:
        return FinBertAnalyzer(batch_size=2, fp16=False)
    except Exception as e:  # weights not cached / offline
        pytest.skip(f"finbert unavailable: {e}")


def test_probabilities_valid_and_label_mapping(analyzer):
    s = analyzer.score(TEXTS)
    p = np.stack([s["p_positive"], s["p_neutral"], s["p_negative"]], axis=1)
    assert np.allclose(p.sum(axis=1), 1, atol=1e-4)
    assert ((s["sentiment_score"] >= -1) & (s["sentiment_score"] <= 1)).all()
    assert s["sentiment_score"][0] > 0 > s["sentiment_score"][1]       # label order is not swapped


def test_batching_and_length_sorting_preserve_order(analyzer):
    batched = analyzer.score(TEXTS)
    for i, t in enumerate(TEXTS):
        single = analyzer.score([t])
        assert abs(single["sentiment_score"][0] - batched["sentiment_score"][i]) < 5e-3, f"order mismatch at {i}"
