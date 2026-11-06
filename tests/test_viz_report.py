import numpy as np
import pandas as pd
import pytest

from features.feature_pipeline import build_model_table
from prediction.forecasting import latest_forecast
from prediction.uncertainty import coverage_by_fold, empirical_interval
from reporting.sentiment_report import build_outlook, render_html, render_markdown
from tests.test_features import synth
from validation.model_comparison import incremental_value, metrics_table, run_walk_forward
from visualization.forecast_matrix import fig_forecast_matrix, forecast_matrix
from visualization.performance_dashboard import (build_dashboard, fig_error_by_horizon, fig_forecast_vs_actual,
                                                 fig_incremental, fig_residuals, fig_walk_forward)
from visualization.price_sentiment import (divergence_events, fig_divergence, fig_price_sentiment, fig_rolling_correlation,
                                           fig_scatter_future, fig_volume_spikes)
from visualization.sentiment_heatmap import calendar_matrix, fig_heatmaps

H = [1, 2, 3, 4, 5]


@pytest.fixture(scope="module")
def world():
    px, agg = synth(520)
    table, sets = build_model_table(px, agg, H)
    sets2 = {k: v for k, v in sets.items() if k in ("A_price", "C_combined")}
    preds = run_walk_forward(table, sets2, ["zero_return", "ridge"], H, 250, 60, val_len=60)
    return px, agg, table, sets, preds


def test_all_figures_build_and_dashboard_embeds_plotly_once(world):
    px, agg, table, sets, preds = world
    figs = [fig_price_sentiment(px, agg, preds, "ridge", "C_combined", 1), fig_divergence(table), fig_rolling_correlation(table),
            fig_scatter_future(table), fig_volume_spikes(table), fig_heatmaps(agg),
            fig_forecast_vs_actual(preds, "ridge", "C_combined", 1), fig_residuals(preds, "ridge", "C_combined", H),
            fig_error_by_horizon(metrics_table(preds)), fig_walk_forward(preds, "ridge", 1),
            fig_incremental(incremental_value(preds, "ridge"))]
    assert all(len(f.data) > 0 for f in figs)
    html = build_dashboard([(f"s{i}", "d", f) for i, f in enumerate(figs)], "t", ["note"])
    assert html.count("plotly.js v") <= 1 and "<h2>s10</h2>" in html and "note" in html


def test_price_panel_shares_time_axis(world):
    px, agg, *_ = world
    f = fig_price_sentiment(px, agg)
    assert f.layout.xaxis.matches == "x3" and f.layout.xaxis2.matches == "x3"   # all panels linked to one time axis


def test_calendar_matrix_and_events(world):
    px, agg, table, *_ = world
    m = calendar_matrix(agg.set_index("trading_day")["mean_sentiment"])
    assert list(m.columns) == ["Mon", "Tue", "Wed", "Thu", "Fri"]
    ev = divergence_events(table)
    assert set(ev["type"]) <= {"sentiment_above_price", "sentiment_below_price"}


def test_forecast_matrix_columns_and_price_identity(world):
    *_, preds = world
    mat = forecast_matrix(preds, "ridge", "C_combined")
    assert {"actual_price_T (n+0)", "pred_n+1", "pred_n+5", "actual_n+3", "pred_ret_n+2"} <= set(mat.columns)
    r = mat.dropna().iloc[0]
    assert np.isclose(r["pred_n+3"], r["actual_price_T (n+0)"] * np.exp(r["pred_ret_n+3"]))
    assert len(fig_forecast_matrix(mat).data) == 1


def test_interval_coverage_is_roughly_calibrated_for_iid_errors():
    rng = np.random.default_rng(0)
    n = 1200
    preds = pd.DataFrame({"ts": pd.bdate_range("2015-01-01", periods=n), "model": "m", "feature_set": "A", "horizon": 1,
                          "fold": np.repeat(np.arange(n // 100), 100), "y_pred": 0.0, "y_true": rng.normal(0, 0.01, n)})
    c = coverage_by_fold(preds, "m", "A", 1, level=0.8)
    assert abs(c["empirical"] - 0.8) < 0.07 and c["n"] > 800
    lo, hi = empirical_interval(rng.normal(0, 1, 5000), 0.9)
    assert abs(lo + 1.645) < 0.12 and abs(hi - 1.645) < 0.12


def test_latest_forecast_uses_only_realised_targets_and_reconstructs_price(world):
    px, agg, table, sets, preds = world
    fc = latest_forecast(table, sets["A_price"], "ridge", H, preds, "A_price")
    assert list(fc.horizon) == H and fc["asof"].iloc[0] == table.index[-1]
    assert np.allclose(fc.pred_price, table["price"].iloc[-1] * np.exp(fc.pred_return))
    assert (fc.price_lo < fc.price_hi).all()
    # the forecast must not depend on the last row's own (unrealisable) targets
    t2 = table.copy()
    t2.loc[t2.index[-1], "y_1"] = 123.0
    f1 = latest_forecast(table, sets["A_price"], "ridge", [1], None)
    f2 = latest_forecast(t2, sets["A_price"], "ridge", [1], None)
    assert np.isclose(f1.pred_return.iloc[0], f2.pred_return.iloc[0])


def test_outlook_report_separates_blocks_and_avoids_trading_advice(world):
    px, agg, table, sets, preds = world
    fc = latest_forecast(table, sets["A_price"], "ridge", H, preds, "A_price")
    o = build_outlook({"company_name": "Apple", "symbol": "AAPL"}, px, agg, table, fc, 12345, 678,
                      "No evidence of predictive value in out-of-sample tests.")
    md = render_markdown(o)
    for sec in ("## 1. Observed facts", "## 2. Model predictions", "## 3. Research interpretation"):
        assert sec in md
    assert "No news data available" in md and "n+5" in md
    low = md.lower()
    assert "not a validated trading signal" in low and "you should buy" not in low and "you should sell" not in low
    assert "<br>" in render_html(o)
