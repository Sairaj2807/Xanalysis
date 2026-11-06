# Development Log

## Session 2026-11-05 (session 1)

### Objective
Build the sentiment-based AAPL prediction platform from an empty repo (Phases 1–6 machinery) and then initialise the documentation/context system.

### Work Completed
Audit of `data/`; AAPL tweet extraction (1,424,481 rows) and price download (1,343 bars); cleaning; FinBERT validation (accuracy 0.604, n=48) and launch of full scoring; aggregation, features, leakage checks, validation machinery, model registry and experiment runner (synthetic-tested); documentation system.

### Files Created
See [SESSION_HANDOFF](../ai_context/SESSION_HANDOFF.md) and [CODEBASE_MAP](../engineering/CODEBASE_MAP.md).

### Files Modified
`requirements.txt` (regenerated). No pre-existing data modified.

### Tests
`pytest -q`: 34 passed mid-session, **39 passed** after model tests; two tests initially failed and exposed BUG-001 and BUG-002 (fixed). `scripts/validate_documentation.py`: 0 errors, 0 warnings (checks required files/sections, relative links, task-register IDs/statuses/dependencies, NEXT_ACTIONS references, staleness). The validator itself has no tests.

### Research Findings
FinBERT weak on slang/mixed statements and overconfident (n=48, self-labelled). 30% of AAPL posts are near-duplicates. No predictive results.

### Issues
532-ID gap; Apify/Tavily credentials missing; requirements omitted torch (fixed).

### Decisions
DEC-001 … DEC-012 ([DECISION_LOG](../decisions/DECISION_LOG.md)).

### Remaining Work
Finish scoring; build table; run EXP-001; cover untested models; ablation/importance; nowcast; DB persistence; visuals; reports.

### Next Session
[NEXT_ACTIONS](../ai_context/NEXT_ACTIONS.md).

Note on history: this repository has no git history, so dates and events above come from this session's command output only; nothing earlier is known.

## Session 2026-11-05 (continuation)
Objective: proceed after documentation setup. Work: added 8 parametrised tests covering every real registry model (ML-002 -> TESTED); suite now **47 passed**. Updated the register, tracker, testing status and handoff accordingly. Scoring continued in the background.

Also: refactored `scripts/build_features.py` into a pure `build_table()` + CLI and added `tests/test_build_features.py` (3 tests, incl. naive-UTC vs tz-aware parity because the real parquet stores naive UTC). Suite: **50 passed**. TEST-004 -> TESTED.

Scoring finished 19:34 (NLP-003 VERIFIED). `build_features.py primary` first failed the leakage gate; diagnosis showed a false alarm from slicing order (BUG-008), fixed with a regression test; rebuilt: 1,238 x 57 table. EXP-001 (`scripts/run_validation.py primary`) launched ~19:37 in the background; results pending.

EXP-001 completed (~8 min, run `20261105T141541Z_primary`). Outcome and caveats recorded in EXPERIMENT_LOG/RESEARCH_FINDINGS. Added tasks STAT-004 and VAL-007. Docs synchronised.

## Session 2026-11-05 (completion)
### Objective
User away: finish the entire backlog autonomously (no commits/pushes).
### Work Completed
Everything in CHANGELOG "completion session"; FinTwitBERT full run (~84 min GPU) in the background while engineering proceeded.
### Tests
`pytest -q`: 101 passed (final). `scripts/validate_documentation.py`: 0 errors, 0 warnings.
### Research Findings
No significant sentiment benefit in any experiment after global correction; nowcast edge is an overnight-gap echo; power analysis shows only effects of roughly R² ≥ 4% were detectable at n+1.
### Issues
BUG-009 (wrong run selected by a loose glob), BUG-010 (predictions key), parser-dropped rows (BUG-004 root cause), crypto parse-loss suspicion disproved.
### Decisions
DEC-013..019.
### Remaining Work
Owner-dependent items in NEXT_ACTIONS (credentials, label review) and optional extensions.
### Next Session
[NEXT_ACTIONS](../ai_context/NEXT_ACTIONS.md).
