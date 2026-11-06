"""Append-only storage of out-of-sample forecasts (database) + run registry."""
from __future__ import annotations

import pandas as pd

from database.repositories import register_run, save_predictions


def store_run_predictions(engine, run_id: str, asset: str, preds: pd.DataFrame, config: dict,
                          artifact_path: str | None = None) -> int:
    """Registers the run (idempotent) and appends every prediction row; previously stored rows are never modified.
    Returns the number of NEW rows stored (0 if the run was already stored)."""
    register_run(engine, run_id, "multiple", "multiple", config, None, artifact_path)
    return save_predictions(engine, run_id, asset, preds)
