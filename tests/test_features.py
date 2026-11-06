import numpy as np
import pandas as pd

from features.feature_pipeline import build_model_table
from features.leakage_checks import check_feature_sets_exclude_targets, check_future_invariance, check_targets_are_future_only
from features.price_features import forward_targets, price_features

H = [1, 2, 3, 4, 5]


def synth(n=300, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2018-01-01", periods=n, name="trading_day")
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    px = pd.DataFrame({"open": close * 0.999, "high": close * 1.01, "low": close * 0.99, "close": close}, index=idx)
    pc = rng.integers(0, 50, n)
    agg = pd.DataFrame({
        "trading_day": idx, "post_count": pc.astype(float),
        "positive_count": pc // 3, "negative_count": pc // 4, "neutral_count": pc // 2,
        "mean_sentiment": np.where(pc > 0, rng.normal(0, 0.3, n), np.nan),
        "median_sentiment": rng.normal(0, 0.3, n), "sentiment_std": rng.uniform(0.1, 0.5, n),
        "sent_engagement_w": rng.normal(0, 0.3, n), "sent_author_w": rng.normal(0, 0.3, n),
        "sent_confidence_w": rng.normal(0, 0.3, n), "engagement_total": rng.integers(0, 100, n).astype(float),
        "unique_authors": pc // 2, "sentiment_confidence": rng.uniform(0.5, 1, n),
        "had_posts": pc > 0,
        "positive_ratio": rng.uniform(0, 1, n), "negative_ratio": rng.uniform(0, 1, n),
        "sentiment_change": rng.normal(0, 0.1, n)})
    return px, agg


def test_target_generation_and_reconstruction():
    px, _ = synth()
    y = forward_targets(px, H)
    t = 50
    assert np.isclose(y.loc[px.index[t], "y_3"], np.log(px.close.iloc[t + 3] / px.close.iloc[t]))
    # price reconstruction  P_hat = P_t * exp(y)
    assert np.isclose(px.close.iloc[t] * np.exp(y.iloc[t]["y_5"]), px.close.iloc[t + 5])
    assert y["y_5"].iloc[-5:].isna().all()


def test_feature_generation_shapes_and_sets():
    px, agg = synth()
    table, sets = build_model_table(px, agg, H)
    assert set(sets) == {"A_price", "B_sentiment", "C_combined"}
    assert set(sets["A_price"]).isdisjoint(sets["B_sentiment"])
    assert set(sets["C_combined"]) >= set(sets["A_price"]) | set(sets["B_sentiment"])
    check_feature_sets_exclude_targets(sets)
    check_targets_are_future_only(table, H)
    # leaky engagement features are off by default
    assert not any("engagement" in c for c in sets["C_combined"])


def test_no_future_leakage_in_price_features():
    px, _ = synth()
    assert check_future_invariance(price_features, px, cut=150) == []


def test_no_future_leakage_in_full_feature_table():
    px, agg = synth()

    def build(p):
        t, s = build_model_table(p, agg, H)   # sentiment rows fixed; only prices scrambled after cut
        return t[s["A_price"]]
    assert check_future_invariance(build, px, cut=150) == []


def test_leakage_detector_catches_a_leaky_feature():
    px, _ = synth()

    def leaky(p):
        return pd.DataFrame({"x": p["close"].shift(-1)}, index=p.index)  # peeks at tomorrow
    assert check_future_invariance(leaky, px, cut=150) == ["x"]
