import pandas as pd
import pytest

from preprocessing.timestamp_alignment import assign_daily_bar, session_close_utc, to_utc

NY = "America/New_York"


def test_naive_timestamps_require_explicit_tz():
    with pytest.raises(ValueError):
        to_utc(pd.Series(["2019-05-27 11:49:14"]))
    out = to_utc(pd.Series(["2019-05-27 11:49:14"]), assume_tz="UTC")
    assert str(out.dt.tz) == "UTC"


def test_mixed_formats_and_bad_values():
    s = pd.Series(["2019-05-27 11:49:14+00:00", "2019-05-27 13:49:14+02:00", "garbage"])
    out = to_utc(s)
    assert out.iloc[0] == out.iloc[1]
    assert pd.isna(out.iloc[2])


def test_dst_aware_close():
    d = pd.Series(["2019-01-15", "2019-07-15"])
    c = session_close_utc(d, NY)
    assert c.iloc[0].hour == 21  # EST = UTC-5
    assert c.iloc[1].hour == 20  # EDT = UTC-4


def test_post_after_close_goes_to_next_bucket():
    # 2019-07-15 (EDT): close 16:00 ET = 20:00 UTC
    ts = pd.Series(pd.to_datetime(["2019-07-15 19:59:59", "2019-07-15 20:00:00", "2019-07-15 20:00:01"], utc=True))
    b = assign_daily_bar(ts, NY)
    assert list(b.dt.strftime("%Y-%m-%d")) == ["2019-07-15", "2019-07-15", "2019-07-16"]


def test_post_after_close_winter_dst():
    # 2019-01-15 (EST): close = 21:00 UTC
    ts = pd.Series(pd.to_datetime(["2019-01-15 20:59:59", "2019-01-15 21:00:01"], utc=True))
    b = assign_daily_bar(ts, NY)
    assert list(b.dt.strftime("%Y-%m-%d")) == ["2019-01-15", "2019-01-16"]


def test_intraday_bar_assignment_boundaries():
    from preprocessing.timestamp_alignment import assign_bar
    ts = pd.Series(pd.to_datetime(["2019-01-02 14:30:00", "2019-01-02 14:30:01", "2019-01-02 14:44:59", "2019-01-02 14:45:00"], utc=True))
    got = assign_bar(ts, "15m")
    assert [str(x.time()) for x in got] == ["14:30:00", "14:45:00", "14:45:00", "14:45:00"]
    assert [str(x.time()) for x in assign_bar(ts, "1h")] == ["15:00:00"] * 4
    assert str(assign_bar(ts, "1d", NY).iloc[0].date()) == "2019-01-02"


def test_aggregate_prices_ohlcv_semantics_and_gaps():
    from preprocessing.timestamp_alignment import aggregate_prices
    idx = pd.date_range("2019-01-02 14:30", periods=6, freq="5min", tz="UTC")
    df = pd.DataFrame({"open": [1, 2, 3, 4, 5, 6.0], "high": [2, 3, 9, 5, 6, 7.0], "low": [0.5, 1, 2, 3, 4, 5.0],
                       "close": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5], "volume": [10, 10, 10, 10, 10, 10]}, index=idx)
    df = df.drop(df.index[3:5])                                    # a gap with no trades
    out = aggregate_prices(df, "15m")
    first = out.iloc[0]
    assert first.open == 1 and first.high == 9 and first.low == 0.5 and first.close == 3.5 and first.volume == 30
    assert len(out) == 2 and out.iloc[1].close == 6.5 and out.iloc[1].volume == 10        # partial bar kept, no forward fill
