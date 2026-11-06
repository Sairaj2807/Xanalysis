# Validation Methodology

Code: [validation/walk_forward.py](../../validation/walk_forward.py), [model_comparison.py](../../validation/model_comparison.py).

- Chronological expanding (or rolling) walk-forward; no random splits.
- **Purging:** a training sample at position `t` is removed if `t + h + embargo ≥ first test position` (its target window reaches the test period). Embargo = 1 bar (DEC-010).
- Test blocks are disjoint and ordered; the tests assert this for h ∈ {1,3,5}, both modes.
- Provisional config: train_min 500, test_len 60, val_len 120 (≈ 10–11 folds expected on ~1.2k rows; not yet run).
- **Leakage gate:** future-scramble invariance of price features; target = exact future log return, NaN at the tail; no target in feature sets. Sentiment cutoff validated by alignment tests, *not* by scrambling.
- Predictions: each run writes `artifacts/runs/<UTC timestamp>_<filter>/oos_predictions.parquet` (+ metrics CSVs). Runs are never overwritten. DB persistence not implemented (VAL-006).
- **Verified only on synthetic data:** the runner detects a planted next-day signal (improvement >0, DM p<0.05) and returns no significant improvement for pure-noise sentiment.

## Additions (2026-11-05)
- Run-level immutability: DB triggers + new run folders ([DEC-017](../decisions/DECISION_LOG.md)).
- Economic evaluation: `strategy_table` (5 bps) in `scripts/evaluate_run.py`; buy-and-hold shown as benchmark over the same window.
- Regime splits use causal definitions (expanding median of trailing volatility; volume-spike proxy is NOT news).
- Tests against persistence: `versus_persistence` (global Holm).
- Real-data smoke runs are mandatory after any pipeline change (BUG-008/009 were only visible on real data).
