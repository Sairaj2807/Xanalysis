import numpy as np
import pandas as pd

from scripts.build_features import build_table


def _fixture(n_days=140, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2018-01-02", periods=n_days, name="trading_day")
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n_days)))
    px = pd.DataFrame({"open": close, "high": close * 1.005, "low": close * 0.995, "close": close}, index=days)
    # 3 posts per trading day, made at 14:00 New York time (inside the session)
    rows = []
    for i, d in enumerate(days):
        for k in range(3):
            ts = pd.Timestamp(d).tz_localize("America/New_York") + pd.Timedelta(hours=14, minutes=k)
            rows.append({"post_id": f"{i}-{k}", "created_at": ts.tz_convert("UTC"), "username": f"u{k}",
                         "text": "x", "likes": 1, "reposts": 0, "replies": 0, "is_duplicate": False,
                         "flag_spam": False, "english_score": 1.0, "flag_bot_like": False})
    posts = pd.DataFrame(rows)
    sent = pd.DataFrame({"post_id": posts["post_id"], "sentiment_score": rng.uniform(-1, 1, len(posts)),
                         "confidence": rng.uniform(0.5, 1, len(posts))})
    return px, posts, sent


def test_build_table_end_to_end_on_fixture():
    px, posts, sent = _fixture()
    table, sets, agg, used = build_table(px, posts, sent, "America/New_York", [1, 2, 3, 4, 5], start=None)
    assert len(used) == len(posts)
    assert (agg["post_count"] == 3).all()
    assert {"A_price", "B_sentiment", "C_combined"} == set(sets)
    assert table["sn_had_posts"].eq(1.0).all()
    assert table["y_5"].iloc[:-5].notna().all()


def test_filters_remove_flagged_posts_and_after_close_posts_roll_forward():
    px, posts, sent = _fixture()
    posts.loc[posts.index[::2], "flag_spam"] = True               # half the posts flagged
    # one post after the close on day 10 must land on day 11, not day 10
    d10, d11 = px.index[10], px.index[11]
    posts.loc[0, ["post_id", "created_at"]] = ["late", (pd.Timestamp(d10).tz_localize("America/New_York")
                                                       + pd.Timedelta(hours=16, minutes=30)).tz_convert("UTC")]
    sent.loc[0, "post_id"] = "late"
    posts.loc[0, "flag_spam"] = False
    _, _, agg, used = build_table(px, posts, sent, "America/New_York", [1], filter_name="primary", start=None)
    assert len(used) < len(posts)
    assert not used["flag_spam"].any()
    late_day = used.loc[used["post_id"] == "late", "trading_day"].iloc[0]
    assert late_day == d11


def test_naive_utc_created_at_matches_tz_aware():
    """Real parquet stores created_at as a naive UTC instant; results must equal the tz-aware path."""
    px, posts, sent = _fixture()
    t1, _, a1, _ = build_table(px, posts, sent, "America/New_York", [1, 2], start=None)
    naive = posts.copy()
    naive["created_at"] = naive["created_at"].dt.tz_convert("UTC").dt.tz_localize(None)
    t2, _, a2, _ = build_table(px, naive, sent, "America/New_York", [1, 2], start=None)
    pd.testing.assert_frame_equal(a1, a2)
    pd.testing.assert_frame_equal(t1, t2)


def test_gate_does_not_false_alarm_when_posts_end_before_prices():
    """Real data: tweets end 2019-12-31 but prices continue; the table is cut at the last post day."""
    px, posts, sent = _fixture()
    cut = px.index[-20]
    keep = posts["created_at"].dt.tz_convert("America/New_York").dt.tz_localize(None) < pd.Timestamp(cut)
    posts, sent = posts[keep], sent[sent["post_id"].isin(posts[keep]["post_id"])]
    table, _, _, _ = build_table(px, posts, sent, "America/New_York", [1, 5], start=None)
    assert table.index.max() < cut
    # last rows keep their (valid) future-based targets instead of being NaN
    assert np.isclose(table["y_5"].iloc[-1], np.log(px["close"].shift(-5) / px["close"]).loc[table.index[-1]])
