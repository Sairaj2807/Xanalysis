# Pipeline Operations

Current: manual, stage-by-stage ([EXECUTION_GUIDE](../operations/EXECUTION_GUIDE.md)). Checkpointing exists only for FinBERT scoring (chunk files). No scheduler, job-status tracking, structured run metadata, or retraining policy yet (ING-007, OPS-003, MON-001). Principle to implement: data refresh frequency is separate from retraining frequency; a retrained model is not promoted without beating the incumbent on validation.

## Update 2026-11-05
`scripts/run_pipeline.py` provides checkpointed runs (`artifacts/pipeline_state.json`), skip-if-outputs-exist, retries and halt-on-failure. `ingestion/ingestion_scheduler.py` runs jobs on independent intervals (refresh vs retrain). Retraining policy and promotion rule: `monitoring/model_monitor.py` (RetrainPolicy: age ≥ 90 days, error ratio ≥ 1.25, PSI ≥ 0.25; promote only with a one-sided DM p < 0.05). The orchestrator has not been used to drive a complete real run; stages were run individually.
