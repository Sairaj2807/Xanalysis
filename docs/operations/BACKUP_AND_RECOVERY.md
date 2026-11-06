# Backup and Recovery

No automated backup. Irreplaceable: nothing in `data/raw`/`data/processed` (regenerable from the original CSVs, ~minutes) except `artifacts/sentiment_chunks/` (≈70 min of GPU time) and `artifacts/runs/` (experiment records) and `docs/`. The original `data/*.csv` files must be preserved (read-only inputs). The repo has no commits and the remote has not been pushed to, so **nothing is backed up off this machine.**
