# Instructions for AI Coding Agents

Permanent working rules. Start every session with the protocol below.

## Session start protocol
1. [docs/README.md](../README.md) → 2. [PROJECT_MASTER_CONTEXT](../PROJECT_MASTER_CONTEXT.md) → 3. [PROJECT_STATUS](../PROJECT_STATUS.md) → 4. [CURRENT_CONTEXT](CURRENT_CONTEXT.md) → 5. [SESSION_HANDOFF](SESSION_HANDOFF.md) → 6. [NEXT_ACTIONS](NEXT_ACTIONS.md) → 7. [MASTER_TASK_REGISTER](../MASTER_TASK_REGISTER.md) → 8. inspect the relevant source → 9. compare docs with code (code and test output win) → 10. pick the highest-priority task that can be completed safely. Do not ask the user to repeat what is documented.

## Session end protocol
Update: implementation tracker, task statuses (add a status-history row), development log, changelog (if behaviour changed), relevant architecture/methodology docs, experiment log (if any run), CURRENT_CONTEXT, SESSION_HANDOFF, NEXT_ACTIONS. Then run `python scripts/update_project_context.py`, `python scripts/generate_codebase_map.py`, `python scripts/generate_project_status.py`, `python scripts/validate_documentation.py`. Never mark untested work VERIFIED; never overwrite historical results; never drop unfinished work from the handoff.

## Objective and layout
Objective: [RESEARCH_OBJECTIVE](../research/RESEARCH_OBJECTIVE.md). Code layout and per-file purpose: [CODEBASE_MAP](../engineering/CODEBASE_MAP.md). Pipeline stages are standalone scripts in `scripts/`, logic lives in importable packages (`ingestion/`, `preprocessing/`, `sentiment/`, `features/`, `models/`, `validation/`, ...). Raw data is read-only.

## Rules
- **Leakage:** see [RESEARCH_RULES](RESEARCH_RULES.md). Any new feature must pass `features/leakage_checks.py` and get a test.
- **Coding:** see [CODING_STANDARDS](CODING_STANDARDS.md).
- **Database:** UTC timestamps, primary keys + unique constraints for idempotency, upserts, append-only predictions. See [DATABASE_ARCHITECTURE](../architecture/DATABASE_ARCHITECTURE.md).
- **Testing:** run `.venv/Scripts/python.exe -m pytest -q` before claiming anything works. Add a test with each behaviour. Synthetic fixtures; no paid API in tests.
- **Security:** secrets only in environment variables (`.env`, never committed). See [SECURITY](../engineering/SECURITY.md).
- **Git:** `origin` points at `github.com/Sairaj2807/Xanalysis.git`. **Do not commit, push, fetch-and-merge, or add AI attribution unless the user explicitly asks in that session.** (User instruction, 2026-11-05: they do not want the AI's involvement displayed in the repository.) The repo currently has zero commits.
- **Honesty:** report failures, null results and skipped steps plainly. Distinguish verified fact / model prediction / interpretation.

## Documentation update table
| Activity | Update |
|---|---|
| New module | [CODEBASE_MAP](../engineering/CODEBASE_MAP.md) (run generator) + [IMPLEMENTATION_TRACKER](../engineering/IMPLEMENTATION_TRACKER.md) |
| Architecture change | [SYSTEM_ARCHITECTURE](../architecture/SYSTEM_ARCHITECTURE.md) |
| New API integration | [API_INTEGRATION](../architecture/API_INTEGRATION.md) |
| Database change | [DATABASE_ARCHITECTURE](../architecture/DATABASE_ARCHITECTURE.md) |
| Feature change | [FEATURE_ENGINEERING](../research/FEATURE_ENGINEERING.md) |
| Model change | [MODEL_REGISTRY](../models/MODEL_REGISTRY.md) |
| New experiment | [EXPERIMENT_LOG](../history/EXPERIMENT_LOG.md) + [MODEL_EXPERIMENTS](../models/MODEL_EXPERIMENTS.md) |
| New test | [TESTING_STATUS](../engineering/TESTING_STATUS.md) |
| Bug found/fixed | [BUG_REGISTER](../engineering/BUG_REGISTER.md) (+ [CHANGELOG](../history/CHANGELOG.md) when fixed) |
| Task done | [MASTER_TASK_REGISTER](../MASTER_TASK_REGISTER.md) |
| Research finding | [RESEARCH_FINDINGS](../research/RESEARCH_FINDINGS.md) |
| Decision | [DECISION_LOG](../decisions/DECISION_LOG.md) |
| Session end | [DEVELOPMENT_LOG](../history/DEVELOPMENT_LOG.md) + [SESSION_HANDOFF](SESSION_HANDOFF.md) |
| New blocker | [PROJECT_STATUS](../PROJECT_STATUS.md) + [NEXT_ACTIONS](NEXT_ACTIONS.md) |

Automation (`scripts/*`) may only rewrite factual inventories (AUTO blocks, CODEBASE_MAP). Research interpretation and decision history are written and reviewed by hand.
