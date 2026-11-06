"""Model registry. Every model is wrapped in Pipeline(imputer -> scaler -> estimator) so that all
preprocessing is fitted on the training window only (no normalisation before the split)."""
from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class ZeroReturn(BaseEstimator, RegressorMixin):
    """Persistence: predicts no change (P_hat = P_t)."""
    def fit(self, X, y):
        return self
    def predict(self, X):
        return np.zeros(len(X))


class HistoricalMean(BaseEstimator, RegressorMixin):
    """Predicts the training-window mean h-step log return."""
    def fit(self, X, y):
        self.mu_ = float(np.mean(y))
        return self
    def predict(self, X):
        return np.full(len(X), self.mu_)


def _wrap(est) -> Pipeline:
    return Pipeline([("imp", SimpleImputer(strategy="median", keep_empty_features=True)),
                     ("sc", StandardScaler()), ("est", est)])


def _lgbm(**kw):
    from lightgbm import LGBMRegressor
    return LGBMRegressor(n_estimators=200, learning_rate=0.03, num_leaves=8, min_child_samples=30, subsample=0.8,
                         subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=0, n_jobs=4, **kw)


def _xgb(**kw):
    from xgboost import XGBRegressor
    return XGBRegressor(n_estimators=200, learning_rate=0.03, max_depth=3, subsample=0.8, colsample_bytree=0.8,
                        random_state=0, n_jobs=4, verbosity=0, **kw)


def _cat(**kw):
    from catboost import CatBoostRegressor
    return CatBoostRegressor(iterations=200, learning_rate=0.03, depth=4, random_seed=0, verbose=0, thread_count=4, **kw)


# name -> (factory(**params), param grid). Grids are deliberately tiny: ~1-2k daily samples cannot support more.
REGISTRY: dict[str, tuple[Callable, dict[str, list]]] = {
    "zero_return": (lambda: ZeroReturn(), {}),
    "hist_mean": (lambda: HistoricalMean(), {}),
    "ridge": (lambda alpha=100.0: _wrap(Ridge(alpha=alpha)), {"alpha": [10.0, 100.0, 1000.0]}),
    "lasso": (lambda alpha=1e-4: _wrap(Lasso(alpha=alpha, max_iter=5000)), {"alpha": [1e-5, 1e-4, 1e-3]}),
    "elasticnet": (lambda alpha=1e-4, l1_ratio=0.5: _wrap(ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=5000)),
                   {"alpha": [1e-5, 1e-4, 1e-3], "l1_ratio": [0.2, 0.8]}),
    "random_forest": (lambda min_samples_leaf=20: _wrap(RandomForestRegressor(
        n_estimators=200, max_depth=6, min_samples_leaf=min_samples_leaf, max_features=0.5, n_jobs=4, random_state=0)),
        {"min_samples_leaf": [10, 40]}),
    "extra_trees": (lambda min_samples_leaf=20: _wrap(ExtraTreesRegressor(
        n_estimators=200, max_depth=6, min_samples_leaf=min_samples_leaf, max_features=0.5, n_jobs=4, random_state=0)),
        {"min_samples_leaf": [10, 40]}),
    "lightgbm": (lambda reg_lambda=10.0: _wrap(_lgbm(reg_lambda=reg_lambda)), {"reg_lambda": [1.0, 50.0]}),
    "xgboost": (lambda reg_lambda=10.0: _wrap(_xgb(reg_lambda=reg_lambda)), {"reg_lambda": [1.0, 50.0]}),
    "catboost": (lambda l2_leaf_reg=10.0: _wrap(_cat(l2_leaf_reg=l2_leaf_reg)), {"l2_leaf_reg": [3.0, 30.0]}),
}

NO_FEATURE_MODELS = {"zero_return", "hist_mean"}


def grid_points(name: str) -> list[dict]:
    grid = REGISTRY[name][1]
    if not grid:
        return [{}]
    keys = list(grid)
    return [dict(zip(keys, v)) for v in product(*[grid[k] for k in keys])]


def make_model(name: str, **params):
    return REGISTRY[name][0](**params)
