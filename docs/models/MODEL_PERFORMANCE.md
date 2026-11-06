# Model Performance

Source: run `20261105T141541Z_primary` (EXP-001), 720 OOS days per cell (2017-01-26..2019-12-04); full per-model tables in `artifacts/runs/20261105T141541Z_primary/metrics_by_model_horizon.csv`. Values are RMSE of the h-day log-return forecast.

| Horizon | Persistence (zero) RMSE | hist_mean RMSE | Best model RMSE (model/set) | Mean RMSE ratio to persistence: A / B / C |
|---|---|---|---|---|
| n+1 | 0.01588 | see CSV | 0.01583 (extra_trees/A) | 1.003 / 1.017 / 1.016 |
| n+2 | 0.02251 | 0.02249 | 0.02249 (hist_mean) | 1.009 / 1.017 / 1.014 |
| n+3 | 0.02710 | 0.02706 | 0.02706 (hist_mean) | 1.017 / 1.017 / 1.019 |
| n+4 | 0.03095 | 0.03088 | 0.03088 (hist_mean) | 1.027 / 1.022 / 1.027 |
| n+5 | 0.03468 | 0.03457 | 0.03457 (hist_mean) | 1.032 / 1.021 / 1.032 |

Reading: ratio >1 = worse than predicting no change. Incremental value of sentiment (C vs A) and significance: [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md). Not computed yet in this document: IC/rank-IC summaries (they are in the CSV), strategy PnL (VAL-007), n+0.

The generic template below is retained for later runs.

Full auto-generated tables (all models, incremental value, economics, ablation, robustness incl. FinTwitBERT, deep models, nowcasts, regimes, correlations): [model performance report](../reports/model_validation/2026-11-05_model_performance_report.md) and [walk-forward report](../reports/model_validation/2026-11-05_walk_forward_report.md).

| Model | Horizon | MAE | RMSE | Dir. acc. | IC | OOS R² |
|---|---|---|---|---|---|---|
| Persistence | n+1…n+5 | — | — | — | — | 0 by definition |
| Price-only | n+1…n+5 | — | — | — | — | — |
| Sentiment-only | n+1…n+5 | — | — | — | — | — |
| Combined | n+1…n+5 | — | — | — | — | — |
