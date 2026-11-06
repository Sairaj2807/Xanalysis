"""Chronological walk-forward splits with purging and embargo.

A training sample at position t has target window (t, t+h]. It is PURGED if t+h >= first test position
(its target overlaps/peeks into the test period). An extra EMBARGO of `embargo` bars is removed before the test.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np


@dataclass(frozen=True)
class Fold:
    train: np.ndarray
    test: np.ndarray
    fold_id: int


def purge_train(train: np.ndarray, test_start: int, horizon: int, embargo: int = 0) -> np.ndarray:
    return train[train + horizon + embargo < test_start]


def walk_forward_splits(n: int, horizon: int, train_min: int, test_len: int, step: int | None = None,
                        embargo: int = 0, mode: str = "expanding", window: int | None = None) -> Iterator[Fold]:
    """mode='expanding' grows the train set; mode='rolling' keeps the most recent `window` bars."""
    if mode not in ("expanding", "rolling"):
        raise ValueError(mode)
    if mode == "rolling" and not window:
        raise ValueError("rolling mode needs window")
    step = step or test_len
    start, k = train_min, 0
    while start + test_len <= n:
        lo = 0 if mode == "expanding" else max(0, start - window)
        train = purge_train(np.arange(lo, start), start, horizon, embargo)
        test = np.arange(start, start + test_len)
        if len(train):
            yield Fold(train, test, k)
            k += 1
        start += step


def split_validation(train: np.ndarray, val_len: int, horizon: int, embargo: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Carve a chronological validation block off the END of a training set for hyperparameter tuning."""
    val = train[-val_len:]
    fit = purge_train(train[:-val_len], val[0], horizon, embargo)
    return fit, val
