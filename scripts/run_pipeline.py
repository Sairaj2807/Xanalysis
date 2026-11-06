"""Pipeline orchestrator: runs the stage scripts in order with checkpoints, retries and job-status tracking.

Each stage is independently executable (its own script). Stages whose output files already exist are SKIPPED unless
--force is given (idempotent re-runs). State is written to artifacts/pipeline_state.json after every stage.

Usage:
  python scripts/run_pipeline.py                      # all stages
  python scripts/run_pipeline.py --stages features,validate
  python scripts/run_pipeline.py --from features --retries 1
  python scripts/run_pipeline.py --list
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


@dataclass(frozen=True)
class Stage:
    name: str
    cmd: Callable[[], list[str]]
    outputs: Callable[[], list[Path]]
    description: str = ""


def _latest(kind: str) -> Path:
    sys.path.insert(0, str(ROOT))
    from reporting.run_index import latest_run
    return latest_run(kind) or ROOT / "artifacts" / "runs" / "__none__"


def default_stages(symbol: str = "AAPL") -> list[Stage]:
    s = lambda f: str(ROOT / "scripts" / f)   # noqa: E731
    d = ROOT / "data"
    return [
        Stage("ingest", lambda: [PY, s("initial_ingestion.py")],
              lambda: [d / "raw" / "x_posts" / f"stock_tweets_{symbol}.parquet", d / "raw" / "prices" / f"{symbol}_1d.parquet"],
              "historical tweets + prices"),
        Stage("clean", lambda: [PY, s("clean_posts.py")], lambda: [d / "processed" / f"posts_{symbol}.parquet"],
              "normalise, dedupe, flag"),
        Stage("score", lambda: [PY, s("score_sentiment.py")], lambda: [d / "processed" / f"sentiment_{symbol}.parquet"],
              "FinBERT scoring (long; resumable)"),
        Stage("features", lambda: [PY, s("build_features.py"), "primary"],
              lambda: [d / "model_ready" / f"model_table_{symbol}_primary.parquet"], "aggregate + features + leakage gate"),
        Stage("validate", lambda: [PY, s("run_validation.py"), "primary"],
              lambda: [_latest("primary") / "incremental_value_price_vs_combined.csv"], "walk-forward A/B/C"),
        Stage("evaluate", lambda: [PY, s("evaluate_run.py"), _latest("primary").name],
              lambda: [_latest("primary") / "strategy_metrics.csv"], "economics + global correction"),
        Stage("ablation", lambda: [PY, s("run_ablation.py"), "primary"],
              lambda: [_latest("ablation_primary") / "ablation_incremental_value.csv"], "feature-group ablation"),
        Stage("analysis", lambda: [PY, s("run_analysis.py")], lambda: [_latest("multihorizon") / "oos_predictions.parquet"],
              "importance, regimes, multi-horizon, deep"),
        Stage("nowcast", lambda: [PY, s("run_nowcast.py"), "--intraday"], lambda: [_latest("nowcast_intraday") / "oos_predictions.parquet"],
              "n+0 nowcast"),
        Stage("report", lambda: [PY, s("generate_report.py")], lambda: [ROOT / "artifacts" / "reports" / "dashboard.html"],
              "dashboard + reports"),
    ]


def subprocess_runner(cmd: list[str]) -> int:
    return subprocess.run(cmd, cwd=ROOT).returncode


def run_pipeline(stages: list[Stage], selected: list[str] | None = None, start_from: str | None = None, force: bool = False,
                 retries: int = 0, runner: Callable[[list[str]], int] = subprocess_runner,
                 state_path: Path | None = None, sleep: Callable[[float], None] = time.sleep) -> dict:
    state_path = state_path or ROOT / "artifacts" / "pipeline_state.json"
    names = [st.name for st in stages]
    if start_from:
        selected = names[names.index(start_from):]
    todo = [st for st in stages if selected is None or st.name in selected]
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    state["run_started"] = datetime.now(timezone.utc).isoformat()
    for st in todo:
        rec = {"description": st.description, "started": datetime.now(timezone.utc).isoformat()}
        if not force and st.outputs() and all(p.exists() for p in st.outputs()):
            rec.update(status="skipped_up_to_date", finished=rec["started"])
            state[st.name] = rec
            continue
        attempts = 0
        while True:
            attempts += 1
            rc = runner(st.cmd())
            if rc == 0 or attempts > retries:
                break
            sleep(2 ** attempts)
        rec.update(status="ok" if rc == 0 else "failed", returncode=rc, attempts=attempts,
                   finished=datetime.now(timezone.utc).isoformat())
        state[st.name] = rec
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2))
        if rc != 0:
            state["halted_at"] = st.name
            break
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))
    return state


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages")
    ap.add_argument("--from", dest="start_from")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retries", type=int, default=0)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    stg = default_stages()
    if a.list:
        for st in stg:
            print(f"{st.name:10s} {st.description}")
        sys.exit(0)
    out = run_pipeline(stg, a.stages.split(",") if a.stages else None, a.start_from, a.force, a.retries)
    failed = [k for k, v in out.items() if isinstance(v, dict) and v.get("status") == "failed"]
    print(json.dumps({k: v.get("status") for k, v in out.items() if isinstance(v, dict)}, indent=2))
    sys.exit(1 if failed else 0)
