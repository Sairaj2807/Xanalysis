# Bug Register

Open issues first. Fixed items are kept. Defects (BUG) are separated from known limitations ([TECHNICAL_DEBT](TECHNICAL_DEBT.md), [DATA_LIMITATIONS](../data/DATA_LIMITATIONS.md)).

## Open
| ID | Severity | Description | Found | Status |
|---|---|---|---|---|
| BUG-005 | Medium | Apify `run_input` keys (`searchTerms`, `maxItems`, `sort`) are an assumption for the configured actor; never run live (ING-003 blocked on credentials) | 2026-11-05 | Open |
| BUG-006 | Low | PostgreSQL branch of `insert_ignore_duplicates` written but untested; the forecast-immutability trigger exists for SQLite only | 2026-11-05 | Open (partially addressed) |
| BUG-011 | Low | `strategy_metrics` assumes a close-to-close fill at the signal bar's close; no slippage/borrow model beyond 5 bps | 2026-11-05 | Known limitation |

## Fixed
| ID | Description | Found by | Fix | Regression test |
|---|---|---|---|---|
| BUG-001 | `to_utc` raised "Mixed timezones detected"; a naive `utc=True` fix would have silently treated naive strings as UTC | `test_alignment.py::test_mixed_formats_and_bad_values` | Split aware/naive strings; naive require explicit `assume_tz` | same |
| BUG-002 | `holm_bonferroni` counted NaN p-values in the family size | `test_validation.py::test_bootstrap_ci_contains_mean_and_holm` | Family size = non-NaN count | same |
| BUG-003 | `requirements.txt` frozen before torch was installed | Documentation audit | Regenerated (twice, last after adding py3langid) | none |
| BUG-004 | 532 AAPL tweet ids linked in `Company_Tweet.csv` missing from the extract. ROOT CAUSE: the bulk DuckDB CSV parser loses a few records after a malformed record (records with doubled quotes); all 532 exist in the raw file | `scripts/diagnose_data_gaps.py` | `recover_missing_posts()` recovers 532/532 into a supplementary Parquet. Downstream pipeline was NOT re-run (0.037% of posts) | `test_cleaning.py::test_recover_missing_posts_*` |
| BUG-007 | Doc tooling: walrus assignment shadowed `test_counts` | Pre-run review | Rewritten | none |
| BUG-008 | Leakage gate false alarm on real data: gate ran after slicing the table at the last tweet date | Real run of `build_features.py` | Run the gate on the full table, then slice | `test_build_features.py::test_gate_does_not_false_alarm_*` |
| BUG-009 | Run lookup `glob("*_primary")` also matched `*_ablation_primary`, so regime analysis (and the pipeline/report helpers) silently picked the wrong run; produced an empty regime file | `run_analysis.py` KeyError on real data | `reporting/run_index.py` with timestamp-anchored regex; all callers switched; empty output deleted | `test_run_index.py` |
| BUG-010 | `model_predictions` unique key (run, asset, ts, horizon) could not hold more than one model per run | Design review while writing repositories | Added model_name/feature_set/fold columns and widened the unique key; migration generated after the change | `test_persistence_ingestion.py::test_predictions_roundtrip_*` |

Lessons: three of the real-data bugs (BUG-008, BUG-009, and the BUG-004 diagnosis) appeared only when running on real data, so every pipeline stage needs a real-data smoke run after changes.
