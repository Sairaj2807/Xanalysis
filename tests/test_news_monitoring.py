import numpy as np
import pandas as pd

from ingestion.news_processing import (categorize_event, cluster_articles, compare_social_news, process_articles,
                                       relevance_score, validate_publication_time)
from monitoring.data_monitor import ingestion_failures, missing_periods, volume_anomalies
from monitoring.drift_monitor import drift_report, psi
from monitoring.model_monitor import RetrainPolicy, promote_candidate, rolling_degradation, should_retrain

ART = [
    {"headline": "Apple beats quarterly earnings estimates", "content": "Apple revenue and EPS rose", "url": "a",
     "published_at": "2019-05-01T12:00:00+00:00", "retrieved_at": "2019-05-01T13:00:00+00:00"},
    {"headline": "Apple beats quarterly earnings estimates again", "content": "", "url": "b",
     "published_at": "2019-05-01T12:30:00+00:00", "retrieved_at": "2019-05-01T13:00:00+00:00"},
    {"headline": "Oil prices drift lower", "content": "energy markets", "url": "c", "published_at": None,
     "retrieved_at": "2019-05-01T13:00:00+00:00"},
    {"headline": "Apple unveils new iPhone", "content": "Apple launch event", "url": "d",
     "published_at": "2019-05-02T12:00:00+00:00", "retrieved_at": "2019-05-01T13:00:00+00:00"},   # published AFTER retrieval
]


class FakeAnalyzer:
    def score(self, texts):
        s = np.array([0.8 if "beats" in t else -0.5 for t in texts])
        return {"sentiment_score": s, "confidence": np.full(len(texts), 0.9)}


def test_relevance_event_and_time_validation():
    assert relevance_score(ART[0], ["apple"]) == 1.0 and relevance_score(ART[2], ["apple"]) == 0.0
    assert categorize_event(ART[0]) == "earnings" and categorize_event(ART[3]) == "product" and categorize_event(ART[2]) == "other"
    assert validate_publication_time(ART[0])["time_valid"]
    assert not validate_publication_time(ART[2])["time_valid"]        # missing time
    assert not validate_publication_time(ART[3])["time_valid"]        # published after retrieval


def test_clustering_groups_near_duplicates_and_pipeline_filters_irrelevant():
    cl = cluster_articles(ART)
    assert cl[0]["cluster_id"] == cl[1]["cluster_id"] != cl[2]["cluster_id"]
    df = process_articles(ART, ["apple"], FakeAnalyzer())
    assert set(df.url) == {"a", "b", "d"} and df.loc[df.url == "a", "sentiment_score"].iloc[0] == 0.8
    assert df.loc[df.url == "d", "time_valid"].iloc[0] == False                      # noqa: E712


def test_social_news_divergence_flags():
    days = pd.bdate_range("2019-05-01", periods=3, name="trading_day")
    social = pd.DataFrame({"trading_day": days, "mean_sentiment": [0.2, -0.2, 0.0], "post_count": [100, 100, 100]})
    news = pd.DataFrame({"trading_day": [days[0], days[1], days[2]], "sentiment_score": [-0.5, 0.5, 0.5]})
    out = compare_social_news(social, news)
    assert out["social_pos_news_neg"].tolist() == [True, False, False]
    assert out["social_neg_news_pos"].tolist() == [False, True, False]


def test_data_monitor_missing_and_anomalies():
    days = pd.bdate_range("2019-01-01", periods=100, name="trading_day")
    daily = pd.DataFrame({"trading_day": days[:90], "post_count": 100.0})
    daily.loc[50, "post_count"] = 0
    m = missing_periods(daily, days)
    assert (m.status == "missing").sum() == 10 and (m.status == "thin").sum() == 1
    pc = pd.Series(np.full(100, 100.0), index=days)
    pc.iloc[80] = 5000
    pc += np.random.default_rng(0).normal(0, 3, 100)
    assert days[80] in volume_anomalies(pc).index


def test_psi_detects_shift_and_ignores_none():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 2000)
    assert psi(a, rng.normal(0, 1, 500)) < 0.1
    assert psi(a, rng.normal(1.5, 1, 500)) > 0.25
    rep = drift_report(pd.DataFrame({"x": a}), pd.DataFrame({"x": rng.normal(2, 1, 300)}), ["x"])
    assert rep.status.iloc[0] == "alert"


def test_retrain_triggers_and_promotion_requires_significant_improvement():
    pol = RetrainPolicy()
    assert should_retrain(pol, 10, 1.0, 0.05) == (False, [])
    flag, why = should_retrain(pol, 120, 1.4, 0.3)
    assert flag and len(why) == 3
    rng = np.random.default_rng(1)
    inc = rng.normal(0, 1.0, 400)
    assert promote_candidate(inc, rng.normal(0, 0.6, 400))["promote"]                 # clearly better
    assert not promote_candidate(inc, inc + rng.normal(0, 0.01, 400))["promote"]      # merely newer/equal
    assert not promote_candidate(inc, rng.normal(0, 1.4, 400))["promote"]             # worse
    deg = rolling_degradation(pd.Series(np.r_[rng.normal(0, 1, 300), rng.normal(0, 2, 60)]), recent=60)
    assert deg["ratio"] > 1.5
