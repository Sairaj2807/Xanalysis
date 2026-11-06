# Documentation Index

Single source of truth for the Xanalysis project. **AI agents: follow the session protocol in [AGENTS](ai_context/AGENTS.md).**

## Read first
[PROJECT_MASTER_CONTEXT](PROJECT_MASTER_CONTEXT.md) · [PROJECT_STATUS](PROJECT_STATUS.md) · [CURRENT_CONTEXT](ai_context/CURRENT_CONTEXT.md) · [SESSION_HANDOFF](ai_context/SESSION_HANDOFF.md) · [NEXT_ACTIONS](ai_context/NEXT_ACTIONS.md) · [MASTER_TASK_REGISTER](MASTER_TASK_REGISTER.md)

## Map
| Area | Documents |
|---|---|
| Project | [PROJECT_CHARTER](PROJECT_CHARTER.md), [DEVELOPMENT_ROADMAP](DEVELOPMENT_ROADMAP.md) |
| Architecture | [SYSTEM](architecture/SYSTEM_ARCHITECTURE.md), [DATA_FLOW](architecture/DATA_FLOW.md), [DATABASE](architecture/DATABASE_ARCHITECTURE.md), [MODULE](architecture/MODULE_ARCHITECTURE.md), [API](architecture/API_INTEGRATION.md), [DEPLOYMENT](architecture/DEPLOYMENT_ARCHITECTURE.md) |
| Research | [OBJECTIVE](research/RESEARCH_OBJECTIVE.md), [HYPOTHESES](research/RESEARCH_HYPOTHESES.md), [DATA](research/DATA_METHODOLOGY.md), [SENTIMENT](research/SENTIMENT_METHODOLOGY.md), [FEATURES](research/FEATURE_ENGINEERING.md), [FORECASTING](research/FORECASTING_METHODOLOGY.md), [VALIDATION](research/VALIDATION_METHODOLOGY.md), [STATISTICS](research/STATISTICAL_TESTING.md), [FINDINGS](research/RESEARCH_FINDINGS.md) |
| Data | [INVENTORY](data/DATA_INVENTORY.md), [DICTIONARY](data/DATA_DICTIONARY.md), [LINEAGE](data/DATA_LINEAGE.md), [QUALITY](data/DATA_QUALITY_REPORT.md), [INGESTION](data/INGESTION_STATUS.md), [LIMITATIONS](data/DATA_LIMITATIONS.md) |
| Models | [REGISTRY](models/MODEL_REGISTRY.md), [EXPERIMENTS](models/MODEL_EXPERIMENTS.md), [PERFORMANCE](models/MODEL_PERFORMANCE.md), [WALK_FORWARD](models/WALK_FORWARD_RESULTS.md), [IMPORTANCE](models/FEATURE_IMPORTANCE.md), [LIMITATIONS](models/MODEL_LIMITATIONS.md) |
| Engineering | [TRACKER](engineering/IMPLEMENTATION_TRACKER.md), [CODEBASE_MAP](engineering/CODEBASE_MAP.md), [TESTING](engineering/TESTING_STATUS.md), [DEBT](engineering/TECHNICAL_DEBT.md), [BUGS](engineering/BUG_REGISTER.md), [SECURITY](engineering/SECURITY.md) |
| Decisions | [LOG](decisions/DECISION_LOG.md), [ARCHITECTURE](decisions/ARCHITECTURE_DECISIONS.md), [RESEARCH](decisions/RESEARCH_DECISIONS.md) |
| History | [CHANGELOG](history/CHANGELOG.md), [DEVELOPMENT_LOG](history/DEVELOPMENT_LOG.md), [EXPERIMENT_LOG](history/EXPERIMENT_LOG.md), [INCIDENT_LOG](history/INCIDENT_LOG.md), [RELEASES](history/RELEASE_HISTORY.md) |
| Operations | [INSTALL](operations/INSTALLATION.md), [CONFIG](operations/CONFIGURATION.md), [EXECUTE](operations/EXECUTION_GUIDE.md), [PIPELINE](operations/PIPELINE_OPERATIONS.md), [TROUBLESHOOT](operations/TROUBLESHOOTING.md), [BACKUP](operations/BACKUP_AND_RECOVERY.md) |
| AI context | [AGENTS](ai_context/AGENTS.md), [CODING](ai_context/CODING_STANDARDS.md), [RESEARCH_RULES](ai_context/RESEARCH_RULES.md) |
| Reports | [model performance](reports/model_validation/2026-11-05_model_performance_report.md), [walk-forward](reports/model_validation/2026-11-05_walk_forward_report.md), [feature importance](reports/research_reports/2026-11-05_feature_importance_report.md), [one-page outlook](reports/research_reports/2026-11-05_one_page_outlook.md), [data quality](reports/data_quality/2026-11-05_data_quality_report.md), [monitoring](reports/data_quality/2026-11-05_monitoring_report.md), [initial audit](reports/project_reviews/2026-11-05_initial_audit.md); interactive dashboard: `artifacts/reports/dashboard.html` (generated, git-ignored) |
| Historical (Phase 1) | [DATA_AUDIT](DATA_AUDIT.md), [PROJECT_ARCHITECTURE](PROJECT_ARCHITECTURE.md), [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) — kept unchanged as the original audit record |

## Conventions
Status vocabulary: NOT_STARTED, IN_PROGRESS, IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEPRECATED (definitions in the task register). Auto-generated content sits between `AUTO` markers or is labelled; everything else is hand-written. Check with `python scripts/validate_documentation.py`.
