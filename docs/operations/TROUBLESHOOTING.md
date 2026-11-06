# Troubleshooting

- `ModuleNotFoundError` for duckdb/pandas with system Python: use `.venv`.
- `python -I` ignores user site-packages; do not use it with the venv-less interpreter.
- DuckDB `Required module 'pytz'`: use `epoch_ms(...)` instead of `to_timestamp` (already done) or install pytz (installed in venv).
- DuckDB rejects `tweets.csv`: needs `strict_mode=false`/other options; unresolved (DATA-004).
- Scoring interrupted: rerun the same command; completed chunks are skipped.
- GPU out-of-memory in scoring: lower `batch_size` in `FinBertAnalyzer`.
- Windows: bash heredocs containing apostrophes can break; write files with the editor tool.

- Report/analysis picks the wrong run: runs are matched by exact kind via `reporting/run_index.py` (BUG-009); do not glob `*_primary`.
- Leakage gate raises on real data right after a change: check whether it runs before or after slicing (BUG-008).
- `Relations no longer have fetchone()` (DuckDB 2.0): use `.fetchall()` on relations.
- pandas 3 returns read-only numpy arrays: `.copy()` before in-place edits.
- Shell tool breaks on apostrophes inside heredocs: write files with the editor tool.
- `alembic` cannot find models: run from the repository root (env.py adds it to sys.path).
