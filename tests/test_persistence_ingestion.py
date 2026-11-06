from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from database.connection import make_engine
from database.repositories import (last_successful_collection, load_predictions, register_run, save_predictions,
                                   save_prices, save_raw_posts)
from ingestion.ingestion_scheduler import Scheduler
from ingestion.x_scraper import XCollector


def _preds(n=6):
    ts = pd.bdate_range("2019-01-02", periods=n)
    rows = []
    for m in ("ridge", "zero_return"):
        for h in (1, 2):
            rows.append(pd.DataFrame({"ts": ts, "horizon": h, "model": m, "feature_set": "A_price", "fold": 0,
                                      "price": 100.0, "y_true": 0.01, "y_pred": 0.005, "params": ""}))
    p = pd.concat(rows, ignore_index=True)
    p["pred_price"] = p["price"] * np.exp(p["y_pred"])
    p["actual_price"] = p["price"] * np.exp(p["y_true"])
    return p


def test_predictions_roundtrip_many_models_per_run_and_idempotent():
    eng = make_engine("sqlite:///:memory:")
    register_run(eng, "run1", "multiple", "A_price", {"train_min": 500})
    p = _preds()
    assert save_predictions(eng, "run1", "AAPL", p) == len(p)          # 2 models x 2 horizons x 6 ts
    assert save_predictions(eng, "run1", "AAPL", p) == 0                # re-saving adds nothing
    back = load_predictions(eng, "run1")
    assert len(back) == len(p) and set(back.model_name) == {"ridge", "zero_return"}


def test_stored_forecasts_are_immutable_but_outcomes_can_be_filled():
    eng = make_engine("sqlite:///:memory:")
    register_run(eng, "r", "m", "A", {})
    save_predictions(eng, "r", "AAPL", _preds(3))
    with eng.begin() as c:                                               # filling the actual outcome is allowed
        c.execute(text("UPDATE model_predictions SET actual_return = 0.02 WHERE id = 1"))
    with pytest.raises(DatabaseError):
        with eng.begin() as c:
            c.execute(text("UPDATE model_predictions SET pred_return = 9.9 WHERE id = 1"))
    with pytest.raises(DatabaseError):
        with eng.begin() as c:
            c.execute(text("DELETE FROM model_predictions"))


def test_prices_and_raw_posts_persist_idempotently():
    eng = make_engine("sqlite:///:memory:")
    px = pd.DataFrame({"bar_start_utc": pd.to_datetime(["2019-01-02", "2019-01-03"], utc=True), "symbol": "AAPL",
                       "interval": "1d", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "adj_close": 1.4, "volume": 10})
    assert save_prices(eng, px) == 2 and save_prices(eng, px) == 0
    posts = pd.DataFrame({"post_id": ["1", "2"], "asset_symbol": "AAPL", "text": ["a", "b"], "username": "u",
                          "created_at": pd.to_datetime(["2019-01-02 15:00", "2019-01-02 16:00"], utc=True)})
    assert save_raw_posts(eng, posts) == 2 and save_raw_posts(eng, posts) == 0


class FakeClient:
    def __init__(self, items_by_window=None, fail_windows=()):
        self.calls, self.items, self.fail = [], items_by_window or {}, set(fail_windows)

    def search(self, q, since, until):
        self.calls.append((q, since, until))
        if (q, since) in self.fail:
            raise RuntimeError("rate limited")
        return self.items.get((q, since), [])


def _item(i, when, text_="$AAPL up"):
    return {"post_id": str(i), "created_at": when, "text": text_, "username": "u", "likes": 1}


def test_collector_is_idempotent_tracks_state_and_isolates_failures():
    eng = make_engine("sqlite:///:memory:")
    now = datetime(2019, 3, 1)
    items = {("$AAPL", "2019-02-22"): [_item(1, "2019-02-23T10:00:00+00:00"), _item(2, "2019-02-24T11:00:00+00:00")]}
    c = XCollector(FakeClient(items), eng, "AAPL", ["$AAPL"], window_days=7)
    r1 = c.collect_incremental(now, lookback_days=7)
    assert r1["status"] == "ok" and r1["new"] == 2 and r1["duplicates"] == 0
    assert r1["latest_post_ts"] == datetime(2019, 2, 24, 11, 0)
    last = last_successful_collection(eng, "apify_x")
    assert last.n_new == 2 and last.last_post_id == "2"
    # second run (next day) overlaps 1 day: same posts come back => 0 new, duplicates counted
    items2 = {("$AAPL", "2019-02-23"): [_item(1, "2019-02-23T10:00:00+00:00"), _item(3, "2019-02-25T09:00:00+00:00")]}
    r2 = XCollector(FakeClient(items2), eng, "AAPL", ["$AAPL"], window_days=7).collect_incremental(now + timedelta(days=1))
    assert r2["new"] == 1 and r2["duplicates"] == 1
    # failure in one window does not lose the others
    cl = FakeClient({("$AAPL", "2019-03-01"): [_item(9, "2019-03-02T00:00:00+00:00")]}, fail_windows={("$AAPL", "2019-02-22")})
    r3 = XCollector(cl, eng, "AAPL", ["$AAPL"], window_days=7).collect(datetime(2019, 2, 22), datetime(2019, 3, 8))
    assert r3["status"] == "partial" and r3["new"] == 1 and len(r3["failures"]) == 1


def test_collector_drops_unparseable_times_and_excluded_keywords():
    eng = make_engine("sqlite:///:memory:")
    items = {("q", "2019-01-01"): [_item(1, "not a date"), _item(2, "2019-01-02T00:00:00+00:00", "buy giveaway now"),
                                   _item(3, "2019-01-02T01:00:00+00:00")]}
    r = XCollector(FakeClient(items), eng, "AAPL", ["q"], exclude_keywords=["giveaway"], window_days=7).collect(
        datetime(2019, 1, 1), datetime(2019, 1, 8))
    assert r["new"] == 1


def test_scheduler_runs_due_jobs_isolates_failures_and_separates_intervals():
    t = {"now": 0.0}
    s = Scheduler(clock=lambda: t["now"])
    log = []
    s.add("refresh", 60, lambda: log.append("refresh"))
    s.add("retrain", 600, lambda: log.append("retrain"))
    s.add("broken", 60, lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert set(s.tick()) == {"refresh", "retrain", "broken"}
    t["now"] = 61
    assert set(s.tick()) == {"refresh", "broken"}                       # retrain not due yet
    st = s.status()
    assert st["broken"]["status"] == "failed" and st["broken"]["failures"] == 2 and st["refresh"]["status"] == "ok"
    t["now"] = 601
    assert "retrain" in s.tick() and log.count("retrain") == 2


def test_alembic_migration_creates_schema_with_immutability_and_downgrades(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "database" / "migrations"))
    eng = create_engine(f"sqlite:///{(tmp_path / 'mig.db').as_posix()}")
    with eng.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
        names = set(inspect(conn).get_table_names())
        assert {"raw_x_posts", "historical_prices", "model_predictions", "model_runs", "ingestion_logs"} <= names
        conn.execute(text("INSERT INTO model_runs (run_id, created_at, model_name, feature_set, config) "
                          "VALUES ('r', '2020-01-01', 'm', 'A', '{}')"))
        conn.execute(text("INSERT INTO model_predictions (run_id, asset, model_name, feature_set, prediction_ts, horizon, "
                          "pred_return, pred_price) VALUES ('r','AAPL','m','A','2020-01-02',1,0.1,100)"))
    with pytest.raises(DatabaseError):
        with eng.begin() as conn:
            conn.execute(text("DELETE FROM model_predictions"))
    with eng.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "base")
        assert "model_predictions" not in set(inspect(conn).get_table_names())
