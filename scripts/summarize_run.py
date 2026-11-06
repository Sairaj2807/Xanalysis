"""Print the standard EXP summary for one or more saved runs (same statistics for every run).

Usage: python scripts/summarize_run.py <run_dir_name> [<run_dir_name> ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT  # noqa: E402
from validation.model_comparison import add_global_correction  # noqa: E402


def summarize(run: str) -> dict:
    d = ROOT / "artifacts" / "runs" / run
    m = pd.read_csv(d / "metrics_by_model_horizon.csv")
    inc = add_global_correction(pd.read_csv(d / "incremental_value_price_vs_combined.csv"))
    z = m[m.model == "zero_return"].set_index("horizon").RMSE
    m["ratio"] = m.apply(lambda r: r.RMSE / z[r.horizon], axis=1)
    fs = m[m.feature_set.isin(["A_price", "B_sentiment", "C_combined"])].pivot_table(
        index="feature_set", columns="horizon", values="ratio").round(4)
    beat = {int(h): int((g[g.model != "zero_return"].RMSE < z[h]).sum()) for h, g in m.groupby("horizon")}
    mean_imp = inc.groupby("horizon").improvement_rmse_pct.mean().round(3)
    out = {
        "run": run, "n_oos": int(inc.n.iloc[0]), "n_tests": int(inc.n_tests_global.iloc[0]),
        "mean_improvement_by_h": mean_imp.to_dict(), "positive_cells": int((inc.improvement_rmse_pct > 0).sum()),
        "raw_sig": int((inc.dm_p < 0.05).sum()),
        "raw_sig_positive": int(((inc.dm_p < 0.05) & (inc.improvement_rmse_pct > 0)).sum()),
        "global_holm_sig": int((inc.dm_p_holm_global < 0.05).sum()),
        "max_improvement": float(inc.improvement_rmse_pct.max()),
        "models_beating_persistence": beat, "ratio_table": fs,
    }
    return out


if __name__ == "__main__":
    for r in sys.argv[1:]:
        s = summarize(r)
        print(f"\n=== {s['run']}  (OOS n={s['n_oos']}, tests={s['n_tests']})")
        print("mean C-vs-A RMSE improvement % by horizon:", s["mean_improvement_by_h"])
        print(f"positive cells {s['positive_cells']}/{s['n_tests']} | raw p<.05: {s['raw_sig']} (positive: {s['raw_sig_positive']}) "
              f"| global-Holm p<.05: {s['global_holm_sig']} | max improvement {s['max_improvement']:.2f}%")
        print("model/set configs beating persistence RMSE, by horizon:", s["models_beating_persistence"])
        print(s["ratio_table"].to_string())
