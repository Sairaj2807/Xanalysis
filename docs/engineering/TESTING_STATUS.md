# Testing Status

Run: `.venv/Scripts/python.exe -m pytest -q` → **101 passed** in ~33 s (final run 2026-11-05). Config: [pytest.ini](../../pytest.ini). No network, GPU or paid API is required (the FinBERT wrapper tests skip if the weights are not cached).

| File | Tests | Covers |
|---|---:|---|
| test_alignment.py | 7 | Naive-tz rejection, mixed offsets, DST-aware close, after-close roll-forward (summer/winter), intraday bar assignment, OHLCV aggregation with gaps |
| test_analysis.py | 12 | Permutation importance ranks a planted feature first, feature-target correlations, power-analysis helper, causal volatility regimes, regime tables, window construction, every network (shared_mlp/GRU/LSTM/TCN/Transformer) fit/predict/reproducible, multi-horizon runner schema + planted signal |
| test_build_features.py | 4 | `build_table` end-to-end, spam filter + after-close roll, naive-UTC vs tz-aware parity, gate does not false-alarm when posts end before prices (BUG-008) |
| test_cleaning.py | 5 | Normalisation, near-duplicate marking, entity/spam flags, low-engagement posts kept, record-level recovery of dropped CSV rows |
| test_e2e_pipeline.py | 3 | Whole chain on fixtures (posts → table → walk-forward → comparison → economics → DB → forecast → report → dashboard); orchestrator skip/halt/state/retry |
| test_features.py | 5 | Target generation + price reconstruction, feature sets, future-invariance (price + full table), leak detector catches a planted leak |
| test_finbert_wrapper.py | 2 | Probability validity, label mapping, batched vs single scoring order (length-sort restore) |
| test_ingestion.py | 9 | Apify parsing/validation/credentials, idempotent insert, Tavily parse/dedupe, price normalisation, config validation, incremental price update |
| test_models.py | 16 | Baselines/persistence identity, reproducibility, noise ⇒ no gain, planted signal detected, every registry model fits with NaNs, global correction, strategy table timing, versus-persistence test |
| test_news_monitoring.py | 6 | News relevance/events/time validity/clustering/divergence, data monitor, PSI/KS drift, retrain triggers and promotion rule |
| test_nowcast.py | 4 | Pre-open cutoff assignment, nowcast features never see the target-day price, planted same-day signal detected, intraday variant uses only the open gap |
| test_persistence_ingestion.py | 7 | Predictions roundtrip (many models per run), immutability triggers, price/post persistence, incremental collector (idempotence, state, failure isolation, unparseable times), scheduler, Alembic upgrade/downgrade |
| test_run_index.py | 1 | Exact run-kind matching (BUG-009) |
| test_sentiment.py | 5 | Score range/definition, trading-day roll-over, empty days not forward-filled, point-in-time author feature, label resolution |
| test_validation.py | 8 | Walk-forward integrity (purge/embargo/disjoint tests), metrics, DM, bootstrap, Holm, directional test, strategy timing |
| test_viz_report.py | 7 | All figures build, dashboard embeds Plotly once, shared time axis, calendar matrix, forecast matrix identity, interval calibration, latest forecast leakage, outlook report structure |

**Known gaps:** no coverage % measured; live Apify/Tavily and PostgreSQL paths untested; the sentiment-cutoff scrambling test covers price inputs only; visual rendering of the dashboard was not inspected; the documentation validator has no tests; `scripts/*` entry points are exercised by running them, not by unit tests (except `build_features.build_table` and the orchestrator).
