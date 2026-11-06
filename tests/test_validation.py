import numpy as np
import pandas as pd

from validation.metrics import all_metrics, directional_metrics, regression_metrics, strategy_metrics
from validation.statistical_tests import (block_bootstrap_ci, diebold_mariano, directional_accuracy_test,
                                          holm_bonferroni)
from validation.walk_forward import split_validation, walk_forward_splits


def test_walk_forward_integrity_no_overlap_and_chronology():
    for h in (1, 3, 5):
        for mode, w in (("expanding", None), ("rolling", 150)):
            folds = list(walk_forward_splits(500, h, train_min=200, test_len=50, embargo=2, mode=mode, window=w))
            assert len(folds) >= 5
            for f in folds:
                assert f.train.max() < f.test.min()
                # no training target window (t, t+h] reaches the test period (+ embargo)
                assert (f.train + h + 2 < f.test.min()).all()
                assert set(f.train).isdisjoint(f.test)
            tests = np.concatenate([f.test for f in folds])
            assert len(tests) == len(set(tests))          # test sets never overlap each other
            assert (np.diff(tests) > 0).all()


def test_rolling_window_bounded():
    f = next(walk_forward_splits(500, 1, 200, 50, mode="rolling", window=100))
    assert len(f.train) <= 100


def test_validation_block_is_last_and_purged():
    train = np.arange(0, 200)
    fit, val = split_validation(train, 40, horizon=5)
    assert val.min() > fit.max() and (fit + 5 < val.min()).all()


def test_metrics_basic():
    y = np.array([0.01, -0.02, 0.03, -0.01])
    assert regression_metrics(y, y)["MAE"] == 0 and regression_metrics(y, y)["R2_oos"] == 1.0
    assert regression_metrics(y, np.zeros(4))["R2_oos"] == 0.0     # zero forecast == benchmark
    assert directional_metrics(y, y)["directional_accuracy"] == 1.0
    assert all_metrics(y, y)["IC"] > 0.999


def test_dm_detects_better_model_and_not_equal_models():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 1, 400)
    good, bad = y + rng.normal(0, 0.3, 400), y + rng.normal(0, 1.0, 400)
    r = diebold_mariano(y - good, y - bad, h=1)
    assert r["dm"] < 0 and r["p_value"] < 0.01
    same = diebold_mariano(y - good, y - (good + 1e-3 * rng.normal(size=400)), h=1)
    assert same["p_value"] > 0.05


def test_bootstrap_ci_contains_mean_and_holm():
    x = np.random.default_rng(1).normal(0.5, 1, 300)
    m, lo, hi = block_bootstrap_ci(x, block=5, n_boot=500)
    assert lo < m < hi
    adj = holm_bonferroni([0.01, 0.04, 0.03, np.nan])
    assert np.isclose(adj[0], 0.03) and adj[1] >= adj[2] >= adj[0] and np.isnan(adj[3])


def test_directional_test_uses_majority_baseline():
    y = np.ones(100)          # market always up
    p = np.ones(100)          # always predict up => hits 100% but base rate is 100% too
    assert directional_accuracy_test(y, p)["p_value"] >= 0.5


def test_strategy_has_no_same_day_lookahead_and_costs():
    idx = pd.bdate_range("2020-01-01", periods=6)
    ret = pd.Series([0.0, 0.01, 0.01, -0.02, 0.01, 0.01], index=idx)
    sig = pd.Series([1, 1, -1, -1, 1, 1], index=idx, dtype=float)
    m = strategy_metrics(sig, ret, cost_bps=0)
    # position sign(sig[t-1]) earns ret[t]: .01*1 + .01*1 + (-.02)*(-1) + .01*(-1) + .01*1 = 0.04
    assert np.isclose(m["gross_pnl"], 0.04)
    assert strategy_metrics(sig, ret, cost_bps=50)["net_pnl"] < m["net_pnl"]
