"""Locate saved experiment runs by exact kind. Run folder names are `<UTC timestamp>_<kind>`.

Matching is anchored on the timestamp prefix, so kind 'primary' does NOT match '..._ablation_primary'
(a plain glob '*_primary' did, and silently selected the wrong run - BUG-009).
"""
from __future__ import annotations

import re
from pathlib import Path

RUNS = Path(__file__).resolve().parents[1] / "artifacts" / "runs"


def list_runs(kind: str, runs_dir: Path | None = None) -> list[Path]:
    rx = re.compile(rf"^\d{{8}}T\d{{6}}Z_{re.escape(kind)}$")
    d = runs_dir or RUNS
    return sorted(p for p in d.glob("*") if p.is_dir() and rx.match(p.name)) if d.exists() else []


def latest_run(kind: str, runs_dir: Path | None = None) -> Path | None:
    r = list_runs(kind, runs_dir)
    return r[-1] if r else None
