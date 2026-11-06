"""Multi-horizon architectures (compared with the independent per-horizon models, architecture A):

B. multi-output models: a single estimator predicts all horizons jointly (`mo_ridge`, `mo_extra_trees`).
C. shared representation: neural nets with a shared trunk and horizon-specific heads
   (`shared_mlp`) plus the sequence models in models/deep_learning.py (`gru`, `lstm`, `tcn`, `transformer`).

Output has the same long format as validation.model_comparison.run_walk_forward so incremental_value() works.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from models.deep_learning import KINDS, fit_predict
from models.model_registry import _wrap
from validation.walk_forward import walk_forward_splits

MO_MODELS = ("mo_ridge", "mo_extra_trees")


def _mo_estimator(name: str):
    from sklearn.ensemble import ExtraTreesRegressor
    from sklearn.linear_model import Ridge

    if name == "mo_ridge":
        return _wrap(Ridge(alpha=100.0))
    return _wrap(ExtraTreesRegressor(n_estimators=200, max_depth=6, min_samples_leaf=20, max_features=0.5,
                                     n_jobs=4, random_state=0))


def run_multi_horizon(table: pd.DataFrame, feature_sets: dict[str, list[str]], models: list[str],
                      horizons: list[int], train_min: int, test_len: int, embargo: int = 1) -> pd.DataFrame:
    ycols = [f"y_{h}" for h in horizons]
    Y = table[ycols].to_numpy(float)
    max_h = max(horizons)
    rows = []
    for fs, cols in feature_sets.items():
        X = table[cols].to_numpy(float)
        for name in models:
            for fold in walk_forward_splits(len(table), max_h, train_min, test_len, embargo=embargo):
                te = fold.test[~np.isnan(Y[fold.test]).any(axis=1)]
                tr = fold.train[~np.isnan(Y[fold.train]).any(axis=1)]
                if len(tr) < 50 or len(te) == 0:
                    continue
                if name in MO_MODELS:
                    pred = _mo_estimator(name).fit(X[tr], Y[tr]).predict(X[te])
                elif name in KINDS:
                    pred = fit_predict(name, X, Y, fold.train, te, max_h)
                else:
                    raise ValueError(name)
                for j, h in enumerate(horizons):
                    rows.append(pd.DataFrame({
                        "ts": table.index[te], "horizon": h, "model": name, "feature_set": fs, "fold": fold.fold_id,
                        "price": table["price"].to_numpy()[te], "y_true": Y[te, j], "y_pred": pred[:, j], "params": ""}))
    out = pd.concat(rows, ignore_index=True)
    out["pred_price"] = out["price"] * np.exp(out["y_pred"])
    out["actual_price"] = out["price"] * np.exp(out["y_true"])
    return out
