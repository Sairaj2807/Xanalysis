import numpy as np
import pandas as pd

from features.feature_pipeline import build_model_table
from models.model_registry import make_model
from tests.test_features import synth
from validation.model_comparison import incremental_value, metrics_table, run_walk_forward

H = [1, 2]


def _table():
    px, agg = synth(450)
    return build_model_table(px, agg, H)


def test_baselines_and_ridge_run_walk_forward_and_reconstruct_prices():
    table, sets = _table()
    p = run_walk_forward(table, sets, ["zero_return", "hist_mean", "ridge"], H, train_min=200, test_len=50, val_len=60)
    assert set(p["model"]) == {"zero_return", "hist_mean", "ridge"}
    z = p[p.model == "zero_return"]
    assert (z.y_pred == 0).all() and np.allclose(z.pred_price, z.price)         # persistence identity
    assert np.allclose(p.pred_price, p.price * np.exp(p.y_pred))
    assert np.allclose(p.actual_price, p.price * np.exp(p.y_true))
    # OOS predictions exist only after the initial training window
    assert p.ts.min() >= table.index[200]


def test_walk_forward_is_reproducible():
    table, sets = _table()
    a = run_walk_forward(table, sets, ["ridge"], [1], 200, 50, val_len=60)
    b = run_walk_forward(table, sets, ["ridge"], [1], 200, 50, val_len=60)
    pd.testing.assert_frame_equal(a, b)


def test_tree_model_reproducible():
    table, sets = _table()
    cols = sets["C_combined"]
    d = table.dropna(subset=cols[:3] + ["y_1"])
    X, y = d[cols].to_numpy(float), d["y_1"].to_numpy()
    p1 = make_model("random_forest").fit(X, y).predict(X)
    p2 = make_model("random_forest").fit(X, y).predict(X)
    assert np.allclose(p1, p2)


def test_noise_sentiment_gives_no_significant_improvement():
    table, sets = _table()                                    # sentiment is pure noise by construction
    p = run_walk_forward(table, sets, ["ridge"], H, 200, 50, val_len=60)
    inc = incremental_value(p, "ridge")
    assert len(inc) == 2 and (inc["dm_p_holm"].fillna(1) > 0.01).all()
    assert len(metrics_table(p)) > 0


def test_planted_signal_is_detected():
    px, agg = _planted()
    table, sets = build_model_table(px, agg, [1])
    p = run_walk_forward(table, sets, ["ridge"], [1], 200, 60, val_len=60)
    inc = incremental_value(p, "ridge")
    assert inc.loc[0, "improvement_rmse_pct"] > 0 and inc.loc[0, "dm_p"] < 0.05


def _planted():
    """Next-day return depends on today's sentiment => sentiment must add out-of-sample value."""
    rng = np.random.default_rng(3)
    n = 700
    idx = pd.bdate_range("2016-01-01", periods=n, name="trading_day")
    s = rng.normal(0, 1, n)
    r = np.r_[0, 0.01 * s[:-1]] + rng.normal(0, 0.005, n)
    close = 100 * np.exp(np.cumsum(r))
    px = pd.DataFrame({"open": close, "high": close * 1.002, "low": close * 0.998, "close": close}, index=idx)
    agg = pd.DataFrame({"trading_day": idx, "post_count": 20.0, "positive_count": 7, "negative_count": 7,
                        "neutral_count": 6, "mean_sentiment": s, "median_sentiment": s, "sentiment_std": 0.2,
                        "sent_engagement_w": s, "sent_author_w": s, "sent_confidence_w": s, "engagement_total": 5.0,
                        "unique_authors": 10, "sentiment_confidence": 0.8, "had_posts": True,
                        "positive_ratio": 0.35, "negative_ratio": 0.35, "sentiment_change": 0.0})
    return px, agg


import pytest  # noqa: E402

from models.model_registry import REGISTRY, grid_points  # noqa: E402


@pytest.mark.parametrize("name", [n for n in REGISTRY if n not in ("zero_return", "hist_mean")])
def test_every_registry_model_fits_predicts_and_handles_nan(name):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(150, 6))
    X[::7, 2] = np.nan                                   # missing sentiment-like values
    y = 0.01 * X[:, 0].copy()
    y = np.nan_to_num(y) + rng.normal(0, 0.002, 150)
    for params in grid_points(name):
        m = make_model(name, **params).fit(X, y)
        p = m.predict(X)
        assert p.shape == (150,) and np.isfinite(p).all()
    # the signal in column 0 should be learned by every real model
    assert np.corrcoef(p, y)[0, 1] > 0.3


def test_global_correction_is_stricter_than_per_model():
    from validation.model_comparison import add_global_correction
    inc = pd.DataFrame({"dm_p": [0.004, 0.2, 0.5, np.nan], "dm_p_holm": [0.004, 0.4, 1.0, np.nan]})
    g = add_global_correction(inc)
    assert g["n_tests_global"].iloc[0] == 3
    assert np.isclose(g.loc[0, "dm_p_holm_global"], 0.012) and np.isnan(g.loc[3, "dm_p_holm_global"])


def test_strategy_table_buy_and_hold_and_signal_timing():
    from validation.model_comparison import strategy_table
    idx = pd.bdate_range("2020-01-01", periods=8)
    price = pd.Series([100, 101, 103, 102, 104, 103, 105, 106.0], index=idx)
    ret = price.pct_change()
    preds = pd.DataFrame({"ts": list(idx[1:]) * 2, "horizon": 1, "model": ["m"] * 7 + ["zero_return"] * 7,
                          "feature_set": "A_price", "y_pred": [0.01] * 7 + [0.0] * 7})
    t = strategy_table(preds, price, cost_bps=0).set_index("model")
    # always-long model earns the next-day returns from the 2nd prediction onward == buy and hold on same window
    assert np.isclose(t.loc["m", "gross_pnl"], ret.iloc[2:].sum())
    assert t.loc["zero_return", "gross_pnl"] == 0.0           # sign(0) = flat
    assert "buy_and_hold" in t.index


def test_versus_persistence_detects_real_skill_and_not_noise():
    from validation.model_comparison import versus_persistence
    rng = np.random.default_rng(0)
    n = 400
    ts = pd.bdate_range("2018-01-01", periods=n)
    y = rng.normal(0, 0.01, n)
    base = pd.DataFrame({"ts": ts, "horizon": 1, "model": "zero_return", "feature_set": "none", "fold": 0, "price": 1.0,
                         "y_true": y, "y_pred": 0.0})
    good = base.assign(model="good", feature_set="A", y_pred=y + rng.normal(0, 0.003, n))      # strong skill
    noise = base.assign(model="noise", feature_set="A", y_pred=rng.normal(0, 0.002, n))        # no skill
    out = versus_persistence(pd.concat([base, good, noise], ignore_index=True)).set_index("model")
    assert out.loc["good", "improvement_rmse_pct_vs_persistence"] > 30 and out.loc["good", "dm_p_holm_global"] < 0.01
    assert out.loc["noise", "dm_p_holm_global"] > 0.05 and out.loc["good", "n_tests_global"] == 2
