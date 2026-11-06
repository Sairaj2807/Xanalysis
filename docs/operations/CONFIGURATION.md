# Configuration

- Asset: [config/asset_config.yaml](../../config/asset_config.yaml) (symbol, company, timezone ∈ {America/New_York, UTC, Asia/Kolkata}, bar_interval, horizons, search queries, lookback, history window). Validated by [config/settings.py](../../config/settings.py).
- Environment (`.env`, from [.env.example](../../.env.example)): `APIFY_API_TOKEN`, `APIFY_ACTOR_ID`, `TAVILY_API_KEY`, `DATABASE_URL`, `ASSET_CONFIG`, `LOG_LEVEL`. None are set currently.
- Walk-forward parameters are constants in `scripts/run_validation.py` (not yet in YAML — TECHNICAL_DEBT).
- Not implemented: `config/model_config.yaml`.

Walk-forward constants (`train_min=500`, `test_len=60`, `embargo=1`, `val_len=120`) are currently code constants in `scripts/run_validation.py`, `run_ablation.py`, `run_analysis.py`, `run_nowcast.py`, `run_engagement_leaky.py` (TD-010). Retrain policy defaults live in `monitoring.model_monitor.RetrainPolicy`.
