"""TEST-002: whole chain on synthetic fixtures - no paid APIs, no network, no GPU.
posts + sentiment + prices -> table -> walk-forward -> comparison -> economics -> DB storage -> forecast -> report."""
import json

import numpy as np
import pandas as pd

from database.connection import make_engine
from database.repositories import load_predictions
from features.leakage_checks import check_targets_are_future_only
from prediction.forecasting import latest_forecast
from prediction.prediction_storage import store_run_predictions
from reporting.sentiment_report import build_outlook, render_markdown
from scripts.build_features import build_table
from scripts.run_pipeline import Stage, run_pipeline
from tests.test_build_features import _fixture
from validation.model_comparison import add_global_correction, incremental_value, run_walk_forward, strategy_table
from visualization.performance_dashboard import build_dashboard, fig_incremental

H = [1, 2, 3, 4, 5]


def test_full_chain_on_fixtures(tmp_path):
    px, posts, sent = _fixture(n_days=420)
    table, sets, agg, used = build_table(px, posts, sent, "America/New_York", H, start=None)
    check_targets_are_future_only(table, H)
    preds = run_walk_forward(table, {k: sets[k] for k in ("A_price", "C_combined")}, ["zero_return", "ridge"], H, 200, 60, val_len=60)
    inc = add_global_correction(incremental_value(preds, "ridge"))
    assert len(inc) == 5 and "dm_p_holm_global" in inc
    st = strategy_table(preds, px["close"])
    assert {"buy_and_hold", "ridge", "zero_return"} <= set(st.model)
    eng = make_engine("sqlite:///:memory:")
    assert store_run_predictions(eng, "e2e", "AAPL", preds, {"train_min": 200}) == len(preds)
    assert store_run_predictions(eng, "e2e", "AAPL", preds, {"train_min": 200}) == 0           # idempotent
    assert len(load_predictions(eng, "e2e")) == len(preds)
    fc = latest_forecast(table, sets["A_price"], "ridge", H, preds, "A_price")
    o = build_outlook({"company_name": "Apple", "symbol": "AAPL"}, px, agg, table, fc, len(used), used.username.nunique(), "test")
    assert "## 2. Model predictions" in render_markdown(o)
    html = build_dashboard([("incremental", "d", fig_incremental(incremental_value(preds, "ridge")))], "e2e")
    out = tmp_path / "d.html"
    out.write_text(html, encoding="utf-8")
    assert out.stat().st_size > 10_000


def _stages(tmp_path, ok_marker):
    mk = lambda name: Stage(name, lambda name=name: ["echo", name], lambda name=name: [tmp_path / f"{name}.out"], name)  # noqa: E731
    return [mk("a"), mk("b"), mk("c")]


def test_orchestrator_skips_up_to_date_halts_on_failure_and_records_state(tmp_path):
    calls = []

    def runner(cmd):
        calls.append(cmd[-1])
        if cmd[-1] == "b":
            return 3
        (tmp_path / f"{cmd[-1]}.out").write_text("x")
        return 0

    stages = _stages(tmp_path, None)
    sp = tmp_path / "state.json"
    state = run_pipeline(stages, runner=runner, state_path=sp, sleep=lambda s: None)
    assert calls == ["a", "b"]                                  # c never runs after b fails
    assert state["a"]["status"] == "ok" and state["b"]["status"] == "failed" and state["halted_at"] == "b"
    assert "c" not in state
    calls.clear()
    state = run_pipeline(stages, runner=runner, state_path=sp, sleep=lambda s: None)   # a is up to date now
    assert state["a"]["status"] == "skipped_up_to_date" and calls == ["b"]
    assert json.loads(sp.read_text())["b"]["returncode"] == 3
    calls.clear()
    run_pipeline(stages, selected=["a"], force=True, runner=runner, state_path=sp)      # --force re-runs
    assert calls == ["a"]


def test_orchestrator_retries_transient_failures(tmp_path):
    n = {"k": 0}

    def flaky(cmd):
        n["k"] += 1
        if n["k"] < 3:
            return 1
        (tmp_path / "a.out").write_text("x")
        return 0

    st = run_pipeline([_stages(tmp_path, None)[0]], retries=3, runner=flaky, state_path=tmp_path / "s.json", sleep=lambda s: None)
    assert st["a"]["status"] == "ok" and st["a"]["attempts"] == 3
