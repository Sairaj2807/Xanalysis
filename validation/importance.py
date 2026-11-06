"""Feature importance: walk-forward permutation importance (out-of-sample, per fold) and SHAP.

Permutation importance is measured on each TEST block with a model fitted on the purged training window, so it
reflects out-of-sample usefulness, not in-sample fit. Importance = increase in test MSE when the column is shuffled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from models.model_registry import make_model
from validation.walk_forward import walk_forward_splits


def permutation_importance_wf(table: pd.DataFrame, cols: list[str], model: str, h: int, train_min: int = 500,
                              test_len: int = 60, embargo: int = 1, n_repeats: int = 5, seed: int = 0,
                              params: dict | None = None) -> pd.DataFrame:
    X = table[cols].to_numpy(float)
    y = table[f"y_{h}"].to_numpy(float)
    rng = np.random.default_rng(seed)
    rows = []
    for fold in walk_forward_splits(len(table), h, train_min, test_len, embargo=embargo):
        tr = fold.train[~np.isnan(y[fold.train])]
        te = fold.test[~np.isnan(y[fold.test])]
        if len(tr) < 50 or len(te) < 10:
            continue
        m = make_model(model, **(params or {})).fit(X[tr], y[tr])
        base = np.mean((y[te] - m.predict(X[te])) ** 2)
        for j, c in enumerate(cols):
            inc = []
            for _ in range(n_repeats):
                Xp = X[te].copy()
                Xp[:, j] = rng.permutation(Xp[:, j])
                inc.append(np.mean((y[te] - m.predict(Xp)) ** 2) - base)
            rows.append({"fold": fold.fold_id, "feature": c, "importance": float(np.mean(inc)), "base_mse": float(base)})
    return pd.DataFrame(rows)


def summarise_importance(df: pd.DataFrame) -> pd.DataFrame:
    """Per feature: mean importance over folds, std, share of folds with positive importance (stability)."""
    g = df.groupby("feature")["importance"]
    out = pd.DataFrame({"mean_importance": g.mean(), "std": g.std(), "frac_folds_positive": g.apply(lambda s: (s > 0).mean())})
    out["group"] = out.index.str.split("_").str[0]
    return out.sort_values("mean_importance", ascending=False)


def group_importance(summary: pd.DataFrame) -> pd.Series:
    """Sum of mean importances per feature family (px_ / sn_ / ix_). Permutation importances of correlated
    features understate shared information, so group totals are indicative only."""
    return summary.groupby("group")["mean_importance"].sum().sort_values(ascending=False)


def shap_values_last_fold(table: pd.DataFrame, cols: list[str], h: int, train_min: int = 500, test_len: int = 60,
                          embargo: int = 1, model: str = "lightgbm") -> tuple[pd.DataFrame, np.ndarray]:
    """SHAP values (tree models) for the final walk-forward test block. Returns (transformed test features, values)."""
    import shap

    X = table[cols].to_numpy(float)
    y = table[f"y_{h}"].to_numpy(float)
    folds = list(walk_forward_splits(len(table), h, train_min, test_len, embargo=embargo))
    fold = folds[-1]
    tr = fold.train[~np.isnan(y[fold.train])]
    te = fold.test[~np.isnan(y[fold.test])]
    pipe = make_model(model).fit(X[tr], y[tr])
    Xt = pipe[:-1].transform(X[te])
    est = pipe[-1]
    sv = shap.TreeExplainer(est).shap_values(Xt)
    return pd.DataFrame(Xt, columns=cols, index=table.index[te]), np.asarray(sv)


def feature_target_correlations(table: pd.DataFrame, cols: list[str], horizons: list[int], n_blocks: int = 6) -> pd.DataFrame:
    """Spearman correlation of each feature with each future return, its p-value (Holm-corrected over ALL tests) and the
    number of chronological blocks in which the sign matches the full-sample sign (stability)."""
    from scipy import stats

    from validation.statistical_tests import holm_bonferroni

    rows = []
    for h in horizons:
        y = table[f"y_{h}"]
        for c in cols:
            d = pd.concat([table[c], y], axis=1).dropna()
            if len(d) < 60 or d.iloc[:, 0].nunique() < 3:
                continue
            rho, p = stats.spearmanr(d.iloc[:, 0], d.iloc[:, 1])
            same = 0
            for b in np.array_split(np.arange(len(d)), n_blocks):
                r_b = stats.spearmanr(d.iloc[b, 0], d.iloc[b, 1])[0]
                same += int(np.sign(r_b) == np.sign(rho))
            rows.append({"feature": c, "horizon": h, "spearman": float(rho), "p": float(p), "n": len(d),
                         "blocks_same_sign": same, "blocks": n_blocks})
    out = pd.DataFrame(rows)
    out["p_holm_global"] = holm_bonferroni(out["p"].tolist())
    out["group"] = out["feature"].str.split("_").str[0]
    return out.sort_values("p")
