import pandas as pd

from preprocessing.text_cleaner import clean_posts, normalise_text


def _df(texts, users=None):
    n = len(texts)
    return pd.DataFrame({"post_id": [str(i) for i in range(n)],
                         "created_at": pd.date_range("2019-01-01", periods=n, freq="min"),
                         "username": users or [f"u{i}" for i in range(n)], "text": texts})


def test_normalise_urls_entities_unicode():
    s = normalise_text(pd.Series(["Great &amp; strong  https://t.co/x  ｆｕｌｌ"]))
    assert s.iloc[0] == "Great & strong URL full"


def test_near_duplicate_marked_not_dropped():
    out = clean_posts(_df(["$AAPL up 5% today http://a.co/1", "$aapl UP 7% today http://b.co/2", "different text here"]))
    assert len(out) == 3
    assert out["is_duplicate"].sum() == 1
    assert out.sort_values("created_at")["is_duplicate"].tolist() == [False, True, False]  # earliest kept canonical


def test_entities_and_spam_flags():
    out = clean_posts(_df(["lx21 made $10,008 on $AAPL -Check it out! http://profit.ly/x #howtotrade",
                           "$AAPL $MSFT $GOOG $AMZN all moving", "Apple earnings look solid"]))
    assert out.loc[0, "flag_promo"] and out.loc[0, "cashtags"] == ["$AAPL"]
    assert out.loc[0, "hashtags"] == ["#howtotrade"]
    assert out.loc[1, "flag_many_cashtags"]
    assert not out.loc[2, "flag_spam"]


def test_low_engagement_posts_are_kept():
    out = clean_posts(_df(["ok"]))
    assert len(out) == 1


def test_recover_missing_posts_parses_individual_records(tmp_path, monkeypatch):
    import duckdb
    import pandas as pd

    import ingestion.legacy_loaders as L

    raw = ('tweet_id,writer,post_date,body,comment_num,retweet_num,like_num\r\n'
           '550753650352869376,u1,1420144877,"If ""innovation"" is $AAPL",0,0,1\r\n'
           '550753650352869377,u2,1420144900,"plain $AAPL",2,1,0\r\n'
           '550753650352869378,u3,1420144999,"other $MSFT",0,0,0\r\n')
    (tmp_path / "Tweet.csv").write_text(raw, encoding="utf-8", newline="")
    (tmp_path / "Company_Tweet.csv").write_text("tweet_id,ticker_symbol\n550753650352869376,AAPL\n550753650352869377,AAPL\n"
                                                "550753650352869378,MSFT\n", encoding="utf-8")
    pd.DataFrame({"post_id": ["550753650352869377"]}).to_parquet(tmp_path / "stock_tweets_AAPL.parquet")   # one already extracted
    monkeypatch.setattr(L, "DATA", tmp_path)
    out = L.recover_missing_posts("AAPL", out_dir=tmp_path, raw_csv=tmp_path / "Tweet.csv")
    got = pd.read_parquet(out)
    assert list(got.post_id) == ["550753650352869376"] and got.text.iloc[0] == 'If "innovation" is $AAPL'
    assert got.likes.iloc[0] == 1 and str(got.created_at.iloc[0]) == "2015-01-01 20:41:17"
