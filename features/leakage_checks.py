"""Automated look-ahead tests. Used by tests/test_leakage.py and as a pipeline gate."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd


def feature_columns(table: pd.DataFrame) -> list[str]:
    return [c for c in table if c.startswith(("px_", "sn_", "ix_"))]


def check_future_invariance(build: Callable[[pd.DataFrame], pd.DataFrame], px: pd.DataFrame, cut: int,
                            seed: int = 0, atol: float = 1e-12) -> list[str]:
    """Build features on the full series and on a series whose data AFTER position `cut` is scrambled.
    Features at rows <= cut must be identical; otherwise they depend on future data. Returns offending columns."""
    rng = np.random.default_rng(seed)
    full = build(px)
    px2 = px.copy()
    tail = px2.index[cut + 1:]
    for col in px2.select_dtypes("number").columns:
        px2.loc[tail, col] = px2.loc[tail, col].to_numpy()[rng.permutation(len(tail))] * rng.uniform(0.5, 1.5, len(tail))
    alt = build(px2)
    a, b = full.iloc[: cut + 1], alt.iloc[: cut + 1]
    bad = []
    for c in a.columns:
        if not np.allclose(a[c].to_numpy(float), b[c].to_numpy(float), atol=atol, equal_nan=True):
            bad.append(c)
    return bad


def check_targets_are_future_only(table: pd.DataFrame, horizons: list[int]) -> None:
    """y_h at t must equal ln(P_{t+h}/P_t) and be NaN where the future is unavailable; never a feature."""
    for h in horizons:
        exp = np.log(table["price"].shift(-h) / table["price"])
        assert np.allclose(table[f"y_{h}"].to_numpy(float), exp.to_numpy(float), equal_nan=True), f"bad target y_{h}"
        assert table[f"y_{h}"].iloc[-h:].isna().all(), f"y_{h} defined without future data"
    leaked = [c for c in feature_columns(table) if c.startswith("y_")]
    assert not leaked, f"target columns inside feature set: {leaked}"


def check_feature_sets_exclude_targets(sets: dict[str, list[str]]) -> None:
    for name, cols in sets.items():
        bad = [c for c in cols if c.startswith("y_") or "fwd" in c]
        assert not bad, f"{name} contains target-like columns {bad}"
