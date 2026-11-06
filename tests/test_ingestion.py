from datetime import datetime, timezone

import pandas as pd
import pytest

from config.settings import AssetConfig
from database.connection import insert_ignore_duplicates, make_engine, session_scope
from database.models import RawXPost
from ingestion.apify_client import ApifyError, ApifyXClient, field_availability, parse_item
from ingestion.price_ingestion import normalise_prices
from ingestion.tavily_client import dedupe_articles, parse_result

ITEM = {"id": 123, "createdAt": "Mon Jan 05 15:00:00 +0000 2015", "fullText": "$AAPL up",
        "author": {"userName": "bob", "id": 9, "followers": 50}, "likeCount": 3, "lang": "en"}


def test_apify_parse_maps_fields_and_keeps_nulls():
    r = parse_item(ITEM, "$AAPL", datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert r["post_id"] == "123" and r["username"] == "bob" and r["likes"] == 3
    assert r["views"] is None and r["is_verified"] is None  # not fabricated
    assert r["query_source"] == "$AAPL"


def test_apify_invalid_items_dropped():
    assert parse_item({"fullText": "no id"}, "q") is None
    assert parse_item({"id": 1}, "q") is None


def test_field_availability():
    rows = [parse_item(ITEM, "q")]
    av = field_availability(rows)
    assert av["likes"] == 1.0 and av["views"] == 0.0


def test_apify_requires_credentials():
    with pytest.raises(ApifyError):
        ApifyXClient("", "")


def test_duplicate_post_prevention_is_idempotent():
    eng = make_engine("sqlite:///:memory:")
    row = {"post_id": "1", "asset_symbol": "AAPL", "created_at": datetime(2015, 1, 1), "text": "x"}
    with session_scope(eng) as s:
        assert insert_ignore_duplicates(s, RawXPost, [row]) == 1
    with session_scope(eng) as s:
        assert insert_ignore_duplicates(s, RawXPost, [row]) == 0  # re-ingest adds nothing
        assert s.query(RawXPost).count() == 1


def test_tavily_parse_and_dedupe():
    r = {"title": "Apple beats", "url": "https://www.example.com/a", "content": "c", "score": 0.9}
    a = parse_result(r, "AAPL", "q")
    assert a["source"] == "example.com" and a["published_at"] is None
    assert len(dedupe_articles([a, dict(a)])) == 1
    assert parse_result({"title": "no url"}, "AAPL", "q") is None


def test_price_normalisation_is_utc_sorted_unique():
    idx = pd.to_datetime(["2020-01-03", "2020-01-02", "2020-01-02"])
    df = pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": 0.5, "Close": 1.5, "Adj Close": 1.4, "Volume": 10}, index=idx)
    out = normalise_prices(df, "AAPL", "1d")
    assert str(out["bar_start_utc"].dt.tz) == "UTC"
    assert out["bar_start_utc"].is_monotonic_increasing and out["bar_start_utc"].is_unique


def test_asset_config_validation():
    with pytest.raises(ValueError):
        AssetConfig(symbol="X", company_name="X", bar_interval="2d")
    with pytest.raises(ValueError):
        AssetConfig(symbol="X", company_name="X", exchange_timezone="EST")


def test_update_prices_is_incremental_and_idempotent(tmp_path):
    from ingestion.price_ingestion import normalise_prices, save_prices, update_prices

    def frame(days):
        idx = pd.to_datetime(days)
        df = pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": 0.5, "Close": 1.5, "Adj Close": 1.4, "Volume": 10}, index=idx)
        return normalise_prices(df, "AAPL", "1d")

    save_prices(frame(["2020-01-02", "2020-01-03", "2020-01-06"]), "AAPL", "1d", tmp_path)
    calls = []

    def fake_fetch(sym, start, end, interval):
        calls.append(start)
        return frame(["2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08"])      # 2 overlap + 2 new

    r1 = update_prices("AAPL", "1d", end="2020-01-10", overlap_days=5, fetch=fake_fetch, out_dir=tmp_path)
    assert r1["added"] == 2 and r1["total"] == 5 and calls[0] == "2020-01-01"      # last bar 2020-01-06 minus 5 days
    r2 = update_prices("AAPL", "1d", end="2020-01-10", overlap_days=5, fetch=fake_fetch, out_dir=tmp_path)
    assert r2["added"] == 0 and r2["total"] == 5                                    # idempotent
