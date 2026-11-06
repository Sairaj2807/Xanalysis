# Deployment Architecture

Current: single local Windows workstation (Windows 11, Quadro P2200 GPU, Python 3.12 venv). No server, scheduler, container or CI. Data lives under `data/`, artifacts under `artifacts/` (both git-ignored).

Planned (not started): scheduled data refresh separate from model retraining (ING-007, OPS-003), optional PostgreSQL/Timescale (DB-004), drift-triggered retraining with incumbent comparison (MON-001). See [PIPELINE_OPERATIONS](../operations/PIPELINE_OPERATIONS.md).

## Update 2026-11-05
Implemented building blocks: `scripts/run_pipeline.py` (orchestrator with checkpoints), `ingestion/ingestion_scheduler.py` (separate refresh/retrain intervals), `monitoring/` (drift, data, model, retrain + promotion rule). Not deployed as a service; no container/CI.
