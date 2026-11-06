# Walk-Forward Results

EXP-001 (run `20261105T141541Z_primary`): expanding mode, train_min 500, test_len 60, embargo 1, val_len 120, 12 folds, test period 2017-01-26..2019-12-04. Per-fold detail is in the run's `oos_predictions.parquet` (`fold` column); folds where C beat A are counted in `incremental_value_price_vs_combined.csv` (typically 2-8 of 12, i.e. no consistent advantage). Method: [VALIDATION_METHODOLOGY](../research/VALIDATION_METHODOLOGY.md). For each run record: run id, config (train_min, test_len, embargo, mode), number of folds, per-fold metrics, folds where C beat A.
