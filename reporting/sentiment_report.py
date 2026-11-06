"""One-page current sentiment outlook. Three clearly separated blocks: OBSERVED FACTS, MODEL PREDICTIONS, INTERPRETATION.

It never labels sentiment a buy/sell signal: the experiments in this repository found no validated predictive value.
News context is reported as unavailable unless a news table is passed in.
"""
from __future__ import annotations

import html
from datetime import datetime

import numpy as np
import pandas as pd


def _label_sentiment(net: float) -> str:
    return "Positive" if net > 0.02 else "Negative" if net < -0.02 else "Neutral"


def _label_momentum(delta: float, tol: float = 0.005) -> str:
    return "Improving" if delta > tol else "Deteriorating" if delta < -tol else "Stable"


def build_outlook(asset: dict, px: pd.DataFrame, agg: pd.DataFrame, table: pd.DataFrame, forecast: pd.DataFrame,
                  n_posts_total: int, n_unique_authors: int, evidence: str, news: pd.DataFrame | None = None) -> dict:
    a = agg.set_index("trading_day") if "trading_day" in agg.columns else agg
    window = a.loc[:table.index[-1]].tail(20)
    recent = window.dropna(subset=["mean_sentiment"])
    pos = float(window["positive_count"].sum() / max(window["post_count"].sum(), 1))
    neg = float(window["negative_count"].sum() / max(window["post_count"].sum(), 1))
    neu = 1 - pos - neg
    net = float(recent["mean_sentiment"].mean())
    ma5, ma20 = recent["mean_sentiment"].tail(5).mean(), recent["mean_sentiment"].mean()
    mom = float(ma5 - ma20)
    close = px["close"].loc[:table.index[-1]]
    ret5 = float(close.iloc[-1] / close.iloc[-6] - 1)
    ret20 = float(close.iloc[-1] / close.iloc[-21] - 1)
    vol20 = float(np.log(close).diff().tail(20).std())
    trend = "up" if close.tail(5).mean() > close.tail(20).mean() else "down"
    div = float(table["ix_sent_price_divergence"].dropna().iloc[-1])
    facts = {
        "asset": asset["company_name"], "ticker": asset["symbol"], "data_as_of": str(table.index[-1].date()),
        "report_generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "latest_price": float(close.iloc[-1]),
        "coverage": f"{table.index[0].date()} to {table.index[-1].date()}",
        "posts_analysed_total": int(n_posts_total), "unique_authors": int(n_unique_authors),
        "last20d_posts": int(window["post_count"].sum()), "positive_pct": 100 * pos, "negative_pct": 100 * neg,
        "neutral_pct": 100 * neu, "net_sentiment_20d": net, "sentiment_momentum_5v20": mom,
        "sentiment_volatility_20d": float(recent["mean_sentiment"].std()),
        "post_volume_trend": float(window["post_count"].tail(5).mean() / max(window["post_count"].mean(), 1) - 1),
        "return_5d": ret5, "return_20d": ret20, "vol_20d_daily": vol20, "price_trend": trend, "divergence_z": div,
        "news": "No news data available (Tavily has not been run)." if news is None or len(news) == 0 else
                f"{len(news)} articles; see news table.",
    }
    interp = {
        "current_sentiment": _label_sentiment(net), "sentiment_momentum": _label_momentum(mom),
        "relationship": evidence,
        "bullish": [f"20-day net FinBERT sentiment {net:+.3f} ({_label_sentiment(net).lower()})" if net > 0 else None,
                    f"5-day return {ret5:+.1%}" if ret5 > 0 else None,
                    "Short-term trend above 20-day average" if trend == "up" else None],
        "bearish": [f"20-day net FinBERT sentiment {net:+.3f}" if net < 0 else None,
                    f"5-day return {ret5:+.1%}" if ret5 < 0 else None,
                    "Short-term trend below 20-day average" if trend == "down" else None],
        "limitations": ["Forecast models did not beat the no-change forecast out of sample.",
                        "Sentiment model accuracy ~0.60-0.71 on a small hand-labelled set.",
                        "Single asset, 2015-2019 history; no live data or news layer.",
                        "Intervals are empirical from past errors and not guaranteed calibrated."],
    }
    interp["bullish"] = [x for x in interp["bullish"] if x] or ["None identified"]
    interp["bearish"] = [x for x in interp["bearish"] if x] or ["None identified"]
    return {"facts": facts, "forecast": forecast, "interpretation": interp}


def render_markdown(o: dict) -> str:
    f, i = o["facts"], o["interpretation"]
    fc = o["forecast"]
    lines = [f"# {f['asset']} ({f['ticker']}) - Sentiment Outlook (data as of {f['data_as_of']})", "",
             f"*Report generated {f['report_generated']}. Research output - not investment advice; sentiment is not a validated trading signal.*", "",
             "## 1. Observed facts", "",
             f"- Latest observable close: **{f['latest_price']:.2f}**; data coverage {f['coverage']}.",
             f"- X posts analysed: {f['posts_analysed_total']:,} ({f['unique_authors']:,} unique authors); last 20 trading days: {f['last20d_posts']:,}.",
             f"- Last-20-day mix: positive {f['positive_pct']:.1f}% / neutral {f['neutral_pct']:.1f}% / negative {f['negative_pct']:.1f}%; "
             f"net sentiment {f['net_sentiment_20d']:+.3f}; momentum (5d vs 20d) {f['sentiment_momentum_5v20']:+.3f}; "
             f"volatility {f['sentiment_volatility_20d']:.3f}; post-volume trend {f['post_volume_trend']:+.0%}.",
             f"- Price: 5-day {f['return_5d']:+.1%}, 20-day {f['return_20d']:+.1%}; daily vol {f['vol_20d_daily']:.2%}; short-term trend {f['price_trend']}; "
             f"sentiment-price divergence z = {f['divergence_z']:+.2f}.",
             f"- News: {f['news']}", "",
             "## 2. Model predictions (research forecast)", "",
             "| Horizon | Predicted price | Predicted return | 80% empirical interval |", "|---|---:|---:|---|"]
    lines.append(f"| n+0 | {f['latest_price']:.2f} (observed close; not a prediction) | - | - |")
    for r in fc.itertuples():
        iv = "n/a" if np.isnan(r.price_lo) else f"{r.price_lo:.2f} - {r.price_hi:.2f}"
        lines.append(f"| n+{r.horizon} | {r.pred_price:.2f} | {r.pred_return:+.3%} | {iv} |")
    lines += ["", f"Model: `{fc['model'].iloc[0]}`. Out-of-sample evidence shows such models do not beat 'no change'; treat as indicative only.", "",
              "## 3. Research interpretation", "",
              f"- Current sentiment: **{i['current_sentiment']}**; momentum: **{i['sentiment_momentum']}**.",
              f"- Price-sentiment relationship: {i['relationship']}",
              "- Bullish observations: " + "; ".join(i["bullish"]), "- Bearish observations: " + "; ".join(i["bearish"]),
              "- Limitations: " + " ".join(i["limitations"]), ""]
    return "\n".join(lines)


def render_html(o: dict) -> str:
    md = render_markdown(o)
    body = html.escape(md).replace("\n", "<br>\n")
    return ("<html><head><meta charset='utf-8'><style>body{font-family:Segoe UI,Arial;max-width:900px;margin:auto;font-size:13px}"
            "</style></head><body>" + body + "</body></html>")
