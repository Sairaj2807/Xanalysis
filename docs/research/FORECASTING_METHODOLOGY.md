# Forecasting Methodology

**Targets:** `y_h = ln(P_{t+h}/P_t)`, h = 1..5, from `close`; `P_hat = P_t exp(y_hat)`. Independent model per horizon (architecture A). Multi-output and shared-head architectures: not implemented (ML-004).

**n+0:** not defined. The spec requires a current-period nowcast kept separate from forecasts and never presented as predictive skill via a trivial identity (ML-006).

**Baselines:** `zero_return` (persistence; also the R²_oos benchmark), `hist_mean` (training-window mean return). Price-only regularised regression = `ridge` on set A.

**Model families:** ridge, lasso, elasticnet, random forest, extra trees, LightGBM, XGBoost, CatBoost (tiny grids; DEC-010). Deep learning: not started. [MODEL_REGISTRY](../models/MODEL_REGISTRY.md).

**Hyperparameter tuning:** chronological validation block (last 120 obs of each training window, purged) — never the test block.

**Trading rule (for strategy metrics only):** position `sign(pred_t)` decided at close `t`, held over day `t+1`; cost 5 bps per unit position change. Forecast quality does not establish profitability.

## n+0 nowcast (implemented, DEC-015)
- Close-to-close: `y_0 = ln(P_D/P_{D-1})`; features = price features through D-1 (shifted one row) + sentiment from posts in (D-1 09:30, D 09:30]; `price` column = P_{D-1}.
- Intraday: `y_0 = ln(close_D/open_D)`; adds the known opening gap `ln(open_D/close_{D-1})`; `price` column = open_D.
- Leakage tests: features never depend on the target day's price (close-to-close) or on its high/low/close (intraday).
- Results: [RESEARCH_FINDINGS](RESEARCH_FINDINGS.md) (EXP-009/010).

## Other architectures (implemented, DEC: ML-004)
Multi-output (B) and shared-representation (C) models compared with independent per-horizon models: [MODEL_REGISTRY](../models/MODEL_REGISTRY.md). Prediction intervals: DEC-019.
