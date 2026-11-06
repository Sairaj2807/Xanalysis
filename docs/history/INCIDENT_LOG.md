# Incident Log

| Date | Incident | Impact | Resolution |
|---|---|---|---|
| 2026-11-05 | `pip install` into system Python 3.14 silently installed to user site; `python -I` could not import duckdb | Minor | Ran helper scripts without `-I`; moved work to a 3.12 venv |
| 2026-11-05 | Heredoc with an apostrophe broke a shell command that wrote three docs | None | Wrote files with the file-writing tool |
| 2026-11-05 | `requirements.txt` frozen before torch install | Reproducibility | BUG-003 fixed |
