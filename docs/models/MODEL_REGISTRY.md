# Model Registry

Code: [models/model_registry.py](../../models/model_registry.py), [multi_horizon.py](../../models/multi_horizon.py), [deep_learning.py](../../models/deep_learning.py). Classical estimators sit in `Pipeline(median imputer → StandardScaler → estimator)` so preprocessing is fitted on the training window only. Seeds fixed.

## Classical (independent per-horizon, architecture A)
| Name | Role | Grid | Tests | Real data |
|---|---|---|---|---|
| zero_return | Persistence baseline | — | yes | EXP-001+ |
| hist_mean | Training-window mean return | — | yes | EXP-001+ |
| ridge | Regularised regression (the spec's price-only baseline on set A) | alpha 10/100/1000 | yes | yes |
| lasso, elasticnet | Sparse linear | alpha (× l1_ratio) | yes | yes |
| random_forest, extra_trees | Trees (depth 6, min leaf 10/40) | min_samples_leaf | yes | yes |
| lightgbm, xgboost, catboost | Boosting (200 trees, shrinkage 0.03) | regulariser | yes | yes |

## Multi-horizon (architectures B and C)
| Name | Architecture | Notes |
|---|---|---|
| mo_ridge, mo_extra_trees | B: one multi-output estimator for n+1..n+5 | purged with max horizon |
| shared_mlp | C: shared trunk + one head per horizon | 2×32 units, dropout 0.2 |
| gru, lstm | C: recurrent trunk (32 units, 10-day windows) + heads | AdamW, early stopping on a chronological tail |
| tcn | C: two causal dilated conv layers + heads | |
| transformer | C: 1-layer encoder (4 heads) + heads | |

All deep models: CPU, 4 threads, seeded, ≤80 epochs, patience 10, training standardisation only. Tests: shapes, finite output, reproducibility. Real-data run: EXP-007.

## Versions
No model has been trained for promotion or deployment. The only "latest forecast" is a ridge model fitted on all realised-target rows to produce the demonstration outlook (see [one-page outlook](../reports/research_reports/2026-11-05_one_page_outlook.md)); out-of-sample evidence says it is not better than no-change. Promotion rule for any future candidate: [monitoring/model_monitor.py](../../monitoring/model_monitor.py).
