"""Post-hoc evaluation of a saved run: strategy/economic metrics (VAL-007) and global multiple-comparison
correction (STAT-004). Writes new files into the run folder; never modifies existing run outputs.

Usage: python scripts/evaluate_run.py <run_dir_name>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config.settings import ROOT, load_settings  # noqa: E402
from validation.model_comparison import add_global_correction, strategy_table  # noqa: E402


def main(run: str, cost_bps: float = 5.0) -> None:
    a = load_settings().asset
    d = ROOT / "artifacts" / "runs" / run
    preds = pd.read_parquet(d / "oos_predictions.parquet")
    px = pd.read_parquet(ROOT / "data" / "raw" / "prices" / f"{a.symbol}_{a.bar_interval}.parquet")
    px["trading_day"] = px["bar_start_utc"].dt.tz_localize(None).dt.normalize()
    price = px.set_index("trading_day").sort_index()["close"]
    st = strategy_table(preds, price, cost_bps)
    st.to_csv(d / "strategy_metrics.csv", index=False)
    inc_path = d / "incremental_value_price_vs_combined.csv"
    if inc_path.exists():
        add_global_correction(pd.read_csv(inc_path)).to_csv(d / "incremental_value_global_correction.csv", index=False)
    pd.set_option("display.width", 200)
    bh = st[st.model == "buy_and_hold"].set_index("horizon")["net_pnl"]
    print(f"run {run}: buy-and-hold net PnL over OOS window (simple sum of daily returns): {bh.iloc[0]:.3f}")
    best = st[st.model != "buy_and_hold"].sort_values("sharpe_net", ascending=False).head(8)
    print(best[["model", "feature_set", "horizon", "gross_pnl", "net_pnl", "sharpe_net", "max_drawdown", "turnover"]].round(3).to_string(index=False))
    print("\nmean net PnL by feature set (excluding baselines):")
    print(st[st.feature_set.isin(["A_price", "B_sentiment", "C_combined"])].groupby("feature_set")[["net_pnl", "sharpe_net"]].mean().round(3))


if __name__ == "__main__":
    main(sys.argv[1])
