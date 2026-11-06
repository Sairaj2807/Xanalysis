"""Walk-forward experiment runner and model comparison (A price vs B sentiment vs C combined)."""
from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
import pandas as pd

from models.model_registry import NO_FEATURE_MODELS, grid_points, make_model
from validation.metrics import all_metrics
from validation.statistical_tests import (block_bootstrap_ci, diebold_mariano, directional_accuracy_test,
                                          holm_bonferroni)
from validation.walk_forward import split_validation, walk_forward_splits

log = logging.getLogger(__name__)


def _tune(name: str, X: np.ndarray, y: np.ndarray, train: np.ndarray, h: int, val_len: int, embargo: int) -> dict:
    """Pick hyperparameters on a chronological validation block inside the training window only."""
    pts = grid_points(name)
    if len(pts) == 1 or len(train) < 3 * val_len:
        return pts[0]
    fit, val = split_validation(train, val_len, h, embargo)
    ok_f, ok_v = fit[~np.isnan(y[fit])], val[~np.isnan(y[val])]
    best, best_err = pts[0], np.inf
    for p in pts:
        m = make_model(name, **p).fit(X[ok_f], y[ok_f])
        err = np.mean((y[ok_v] - m.predict(X[ok_v])) ** 2)
        if err < best_err:
            best, best_err = p, err
    return best


def run_walk_forward(table: pd.DataFrame, feature_sets: dict[str, list[str]], models: Iterable[str],
                     horizons: list[int], train_min: int, test_len: int, embargo: int = 1,
                     mode: str = "expanding", window: int | None = None, val_len: int = 120) -> pd.DataFrame:
    """Returns long-format OOS predictions. Each prediction is made by a model fitted only on data whose
    target window ended before the test block (purged + embargoed)."""
    rows = []
    n = len(table)
    for h in horizons:
        y = table[f"y_{h}"].to_numpy(float)
        for fs_name, cols in feature_sets.items():
            X = table[cols].to_numpy(float)
            for name in models:
                if name in NO_FEATURE_MODELS and fs_name != next(iter(feature_sets)):
                    continue   # feature-free baselines are fitted once, labelled with the first set
                for fold in walk_forward_splits(n, h, train_min, test_len, embargo=embargo, mode=mode, window=window):
                    tr = fold.train[~np.isnan(y[fold.train])]
                    te = fold.test[~np.isnan(y[fold.test])]
                    if len(tr) < 50 or len(te) == 0:
                        continue
                    params = _tune(name, X, y, fold.train, h, val_len, embargo)
                    m = make_model(name, **params).fit(X[tr], y[tr])
                    pred = m.predict(X[te])
                    rows.append(pd.DataFrame({
                        "ts": table.index[te], "horizon": h, "model": name,
                        "feature_set": "none" if name in NO_FEATURE_MODELS else fs_name, "fold": fold.fold_id,
                        "price": table["price"].to_numpy()[te], "y_true": y[te], "y_pred": pred,
                        "params": str(params)}))
    out = pd.concat(rows, ignore_index=True)
    out["pred_price"] = out["price"] * np.exp(out["y_pred"])
    out["actual_price"] = out["price"] * np.exp(out["y_true"])
    return out


def metrics_table(preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, fs, h), g in preds.groupby(["model", "feature_set", "horizon"]):
        rows.append({"model": model, "feature_set": fs, "horizon": h, **all_metrics(g["y_true"].to_numpy(), g["y_pred"].to_numpy())})
    return pd.DataFrame(rows)


def incremental_value(preds: pd.DataFrame, model: str, base_set: str = "A_price", new_set: str = "C_combined",
                      block: int = 5) -> pd.DataFrame:
    """Price-only vs price+sentiment for one model family, per horizon, with DM test, bootstrap CI,
    per-fold consistency and Holm-corrected p-values across horizons."""
    rows = []
    for h, g in preds[preds["model"] == model].groupby("horizon"):
        a = g[g.feature_set == base_set].set_index("ts")
        c = g[g.feature_set == new_set].set_index("ts")
        idx = a.index.intersection(c.index)
        if len(idx) < 10:
            continue
        a, c = a.loc[idx], c.loc[idx]
        ea, ec = (a.y_true - a.y_pred).to_numpy(), (c.y_true - c.y_pred).to_numpy()
        mse_a, mse_c = np.mean(ea ** 2), np.mean(ec ** 2)
        dm = diebold_mariano(ec, ea, h=int(h))                    # negative => combined has lower loss
        diff = ea ** 2 - ec ** 2                                  # positive => combined better
        _, lo, hi = block_bootstrap_ci(diff, block=max(block, int(h)), n_boot=1000)
        fold_win = (pd.Series(diff, index=idx).groupby(a["fold"].to_numpy()).mean() > 0)
        rows.append({
            "model": model, "horizon": h, "n": len(idx),
            "mae_price": np.mean(np.abs(ea)), "mae_combined": np.mean(np.abs(ec)),
            "rmse_price": np.sqrt(mse_a), "rmse_combined": np.sqrt(mse_c),
            "improvement_rmse_pct": 100 * (np.sqrt(mse_a) - np.sqrt(mse_c)) / np.sqrt(mse_a),
            "improvement_mae_pct": 100 * (np.mean(np.abs(ea)) - np.mean(np.abs(ec))) / np.mean(np.abs(ea)),
            "dm_stat": dm["dm"], "dm_p": dm["p_value"], "mse_diff_ci_lo": lo, "mse_diff_ci_hi": hi,
            "folds_combined_better": int(fold_win.sum()), "folds": int(len(fold_win)),
            "dir_acc_price": directional_accuracy_test(a.y_true.to_numpy(), a.y_pred.to_numpy())["hit_rate"],
            "dir_acc_combined": directional_accuracy_test(c.y_true.to_numpy(), c.y_pred.to_numpy())["hit_rate"],
        })
    out = pd.DataFrame(rows)
    if len(out):
        out["dm_p_holm"] = holm_bonferroni(out["dm_p"].tolist())
    return out


def add_global_correction(inc: pd.DataFrame) -> pd.DataFrame:
    """Holm correction across ALL rows of an incremental-value table (every model x horizon x variant),
    on top of the per-model-across-horizons `dm_p_holm`. Use this column for headline claims."""
    out = inc.copy()
    out["n_tests_global"] = int(out["dm_p"].notna().sum())
    out["dm_p_holm_global"] = holm_bonferroni(out["dm_p"].tolist())
    return out


def strategy_table(preds: pd.DataFrame, price: pd.Series, cost_bps: float = 5.0) -> pd.DataFrame:
    """Economic evaluation (VAL-007). Rule: position = sign(prediction made at close t) held over day t+1,
    1 unit long/short, `cost_bps` per unit of position change. `price` = daily closes indexed by trading day.
    Includes a buy-and-hold row (always long) over each model's own OOS window as the benchmark."""
    from validation.metrics import strategy_metrics

    ret = price.pct_change()
    rows = []
    for (model, fs, h), g in preds.groupby(["model", "feature_set", "horizon"]):
        sig = g.sort_values("ts").set_index("ts")["y_pred"]
        r = ret.reindex(sig.index)
        rows.append({"model": model, "feature_set": fs, "horizon": h, **strategy_metrics(sig, r, cost_bps)})
    for h, g in preds.groupby("horizon"):
        idx = pd.Index(sorted(g["ts"].unique()))
        rows.append({"model": "buy_and_hold", "feature_set": "none", "horizon": h,
                     **strategy_metrics(pd.Series(1.0, index=idx), ret.reindex(idx), cost_bps)})
    return pd.DataFrame(rows)


def versus_persistence(preds: pd.DataFrame) -> pd.DataFrame:
    """Does any model beat the no-change forecast? DM test of every (model, feature_set, horizon) against `zero_return`
    on identical timestamps, with Holm correction across ALL rows (global family). Negative dm => model better."""
    z = preds[preds.model == "zero_return"].drop_duplicates(["ts", "horizon"]).set_index(["ts", "horizon"])["y_true"]
    rows = []
    for (m, fs, h), g in preds[preds.model != "zero_return"].groupby(["model", "feature_set", "horizon"]):
        g = g.set_index("ts")
        idx = g.index.intersection(z.xs(h, level="horizon").index)
        if len(idx) < 30:
            continue
        em = (g.loc[idx, "y_true"] - g.loc[idx, "y_pred"]).to_numpy()
        ez = z.xs(h, level="horizon").loc[idx].to_numpy()                      # zero forecast => error = y_true
        dm = diebold_mariano(em, ez, h=int(h))
        rows.append({"model": m, "feature_set": fs, "horizon": h, "n": len(idx),
                     "improvement_rmse_pct_vs_persistence": 100 * (1 - np.sqrt(np.mean(em ** 2)) / np.sqrt(np.mean(ez ** 2))),
                     "dm_p": dm["p_value"]})
    out = pd.DataFrame(rows)
    if len(out):
        out["n_tests_global"] = len(out)
        out["dm_p_holm_global"] = holm_bonferroni(out["dm_p"].tolist())
    return out
