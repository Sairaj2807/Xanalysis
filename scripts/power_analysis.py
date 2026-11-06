"""Power analysis of the A-vs-C comparison on the REAL price table.

A synthetic 'sentiment' column is planted: f = sqrt(r2) * z(y_1) + sqrt(1 - r2) * noise, so it explains r2 of the variance of
the next-day return (corr = sqrt(r2)). We then run the same ridge walk-forward (price-only vs price + planted feature) and the
same Diebold-Mariano test, many times, to learn which true effect sizes this design can detect. Real prices are kept; only
the sentiment column is synthetic.

Usage: python scripts/power_analysis.py [n_seeds]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from validation.model_comparison import incremental_value, run_walk_forward  # noqa: E402

R2S = [0.0, 0.0025, 0.005, 0.01, 0.02, 0.04]


def one(table: pd.DataFrame, px_cols: list[str], r2: float, seed: int, h: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    y = table[f"y_{h}"]
    z = (y - y.mean()) / y.std()
    t = table.copy()
    t["lk_planted"] = np.sqrt(r2) * z + np.sqrt(1 - r2) * rng.normal(size=len(t))
    sets = {"A_price": px_cols, "C_combined": px_cols + ["lk_planted"]}
    p = run_walk_forward(t, sets, ["ridge"], [h], 500, 60, embargo=1, val_len=120)
    inc = incremental_value(p, "ridge").iloc[0]
    return {"r2": r2, "seed": seed, "improvement_rmse_pct": float(inc.improvement_rmse_pct), "dm_p": float(inc.dm_p)}


def main(n_seeds: int = 20) -> pd.DataFrame:
    a = load_settings().asset
    table = pd.read_parquet(ROOT / "data" / "model_ready" / f"model_table_{a.symbol}_primary.parquet")
    sets = json.loads((ROOT / "data" / "model_ready" / "feature_sets.json").read_text())
    rows = [one(table, sets["A_price"], r2, s) for r2 in R2S for s in range(n_seeds)]
    df = pd.DataFrame(rows)
    summ = df.groupby("r2").agg(mean_improvement_pct=("improvement_rmse_pct", "mean"),
                                detect_rate_p05=("dm_p", lambda s: (s < 0.05).mean()),
                                detect_rate_p001=("dm_p", lambda s: (s < 0.001).mean())).reset_index()
    out = ROOT / "artifacts" / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "power_analysis_raw.csv", index=False)
    summ.to_csv(out / "power_analysis_summary.csv", index=False)
    print(summ.round(3).to_string(index=False))
    return summ


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
