import numpy as np
import pandas as pd
import pytest

from models.deep_learning import KINDS, fit_predict, make_windows
from models.multi_horizon import run_multi_horizon
from tests.test_features import synth
from features.feature_pipeline import build_model_table
from validation.importance import group_importance, permutation_importance_wf, summarise_importance
from validation.model_comparison import incremental_value, run_walk_forward
from validation.regime_analysis import improvement_by_regime, spike_regime, vol_regime

H = [1, 2, 3]


def _planted_table(n=700, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-01", periods=n, name="trading_day")
    s = rng.normal(0, 1, n)
    r = np.r_[0, 0.01 * s[:-1]] + rng.normal(0, 0.005, n)
    price = 100 * np.exp(np.cumsum(r))
    t = pd.DataFrame({"price": price, "px_noise1": rng.normal(size=n), "px_noise2": rng.normal(size=n),
                      "sn_signal": s, "px_vol_20": pd.Series(r).rolling(20).std().to_numpy(),
                      "sn_post_count_z": rng.normal(size=n)}, index=idx)
    lp = np.log(t["price"])
    for h in H:
        t[f"y_{h}"] = lp.shift(-h) - lp
    return t


def test_permutation_importance_ranks_planted_feature_first_and_is_oos():
    t = _planted_table()
    df = permutation_importance_wf(t, ["px_noise1", "px_noise2", "sn_signal"], "random_forest", 1, 400, 60, n_repeats=3)
    s = summarise_importance(df)
    assert s.index[0] == "sn_signal"
    assert s.loc["sn_signal", "frac_folds_positive"] >= 0.8
    assert s.loc["px_noise1", "mean_importance"] < 0.2 * s.loc["sn_signal", "mean_importance"]
    assert group_importance(s).index[0] == "sn"


def test_vol_regime_uses_only_past_information():
    t = _planted_table()
    r1 = vol_regime(t)
    t2 = t.copy()
    t2.loc[t2.index[500:], "px_vol_20"] *= 5                       # change the future only
    r2 = vol_regime(t2)
    assert r1.iloc[:500].equals(r2.iloc[:500]) or r1.iloc[:500].fillna("x").equals(r2.iloc[:500].fillna("x"))


def test_regime_improvement_table_runs():
    t = _planted_table()
    sets = {"A_price": ["px_noise1", "px_noise2"], "C_combined": ["px_noise1", "px_noise2", "sn_signal"]}
    p = run_walk_forward(t, sets, ["ridge"], [1], 300, 60, val_len=60)
    out = improvement_by_regime(p, vol_regime(t), "ridge", 1)
    assert set(out.regime) <= {"high_vol", "low_vol"} and (out.n > 0).all()
    assert (out.improvement_rmse_pct > 0).all()                     # planted signal helps in both regimes
    assert spike_regime(t).dropna().isin(["normal", "volume_spike"]).all()


def test_windows_use_only_past_rows():
    X = np.arange(20, dtype=float).reshape(-1, 1)
    w = make_windows(X, np.array([0, 5]), 3)
    assert w[1, :, 0].tolist() == [3, 4, 5] and w[0, :, 0].tolist() == [0, 0, 0]


@pytest.mark.parametrize("kind", KINDS)
def test_every_network_fits_and_predicts_valid_shapes(kind):
    t = _planted_table(400)
    X = t[["px_noise1", "px_noise2", "sn_signal"]].to_numpy(float).copy()
    X[::9, 0] = np.nan
    Y = t[[f"y_{h}" for h in H]].to_numpy(float)
    tr, te = np.arange(0, 300), np.arange(300, 340)
    p1 = fit_predict(kind, X, Y, tr, te, max_h=3, epochs=15)
    p2 = fit_predict(kind, X, Y, tr, te, max_h=3, epochs=15)
    assert p1.shape == (40, 3) and np.isfinite(p1).all()
    assert np.allclose(p1, p2, atol=1e-5)                           # seeded => reproducible


def test_multi_horizon_runner_matches_walk_forward_schema_and_finds_signal():
    t = _planted_table()
    sets = {"A_price": ["px_noise1", "px_noise2"], "C_combined": ["px_noise1", "px_noise2", "sn_signal"]}
    p = run_multi_horizon(t, sets, ["mo_ridge", "shared_mlp"], H, 400, 60)
    assert {"ts", "horizon", "model", "feature_set", "fold", "y_true", "y_pred", "pred_price"} <= set(p.columns)
    assert set(p.horizon) == set(H)
    inc = incremental_value(p, "mo_ridge")
    assert (inc.improvement_rmse_pct > 0).all()


def test_feature_target_correlations_find_planted_signal_and_keep_noise_insignificant():
    from validation.importance import feature_target_correlations
    t = _planted_table()
    out = feature_target_correlations(t, ["px_noise1", "px_noise2", "sn_signal"], [1])
    top = out.iloc[0]
    assert top.feature == "sn_signal" and top.spearman > 0.5 and top.blocks_same_sign == top.blocks
    assert (out[out.feature != "sn_signal"].p_holm_global > 0.05).all()


def test_power_analysis_helper_plants_signal_of_requested_strength():
    from scripts.power_analysis import one
    t = _planted_table(900)
    t = t.drop(columns=["sn_signal"])
    strong = one(t, ["px_noise1", "px_noise2"], 0.25, seed=1)
    none = one(t, ["px_noise1", "px_noise2"], 0.0, seed=1)
    assert strong["improvement_rmse_pct"] > 5 and strong["dm_p"] < 0.01
    assert none["improvement_rmse_pct"] < 2
