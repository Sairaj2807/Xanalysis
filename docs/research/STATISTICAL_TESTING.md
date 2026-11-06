# Statistical Testing

Code: [validation/statistical_tests.py](../../validation/statistical_tests.py).

- **Diebold-Mariano** on squared-error differentials, Newey-West HAC with lag `h−1`, Harvey-Leybourne-Newbold small-sample correction, t(n−1) reference. Sign: negative ⇒ the first model has lower loss. Returns NaN for n<10 or constant differentials.
- **Block bootstrap CI** (moving blocks, block ≥ max(5, h), 1000 resamples) on the MSE differential `e_A² − e_C²` (positive ⇒ C better).
- **Directional accuracy** one-sided binomial test against the majority-class base rate (a model cannot win by predicting the common direction).
- **Holm-Bonferroni** across horizons per model (NaN excluded from the family; BUG-002). Cross-model correction is **not** applied automatically — with ten model families the reader must account for it (open item).
- **Fold consistency:** number of folds where C's mean squared error beats A's.
- **Economic vs statistical significance:** reported separately; net PnL after 5 bps costs via `strategy_metrics`.
- **Power caveat:** ~1.2k overlapping daily observations; overlapping targets (h>1) reduce effective sample size; HAC lag only partly compensates.

## Global correction (DEC-014)
`add_global_correction` applies Holm over every row of a comparison table (`dm_p_holm_global`, with `n_tests_global`). Family sizes used so far: EXP-001 40, ablation 105, multi-horizon 35, engagement 60, versus persistence 230. Statements of significance in this project refer to this column only. Per-model Holm across horizons (`dm_p_holm`) is retained but is weaker.
