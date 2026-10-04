"""Offline Streamlit flow checks; provider calls are replaced explicitly."""

import io
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import app
from portfolio_risk import data
from portfolio_risk.attribution import calculate_attribution
from portfolio_risk.metrics import calculate_metrics

APP = Path(__file__).resolve().parents[1] / "app.py"
CSV = b"ticker,weight\nA,0.2\nB,0.8\n"


def prices_data(*, rows=301, constant=False, gap=False):
    dates = pd.bdate_range("2022-01-03", periods=rows)
    r = np.resize([0.002, -0.002], rows)
    prices = pd.DataFrame({"A": 100 * np.cumprod(1 + r),
                           "B": 100 * np.cumprod(1 - r / 2)}, index=dates)
    if constant:
        prices[:] = 100
    if gap:
        prices.iloc[180, 0] = np.nan
    p = {"schema_version": 1, "provider": "yfinance", "source": data.SOURCE,
         "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
         "python_version": "test", "provider_version": "test",
         "requested_tickers": ["A", "B"], "quote_currency": "USD",
         "currency_verification": {t: {"quote_currency": "USD", "basis": "source-verified",
                                      "metadata_field": "currency"} for t in prices},
         "requested_start": "2022-01-01", "requested_end_exclusive": "2026-01-01",
         "interval": "1d", "auto_adjust": True, "adjustment": data.ADJUSTMENT,
         "warnings": [], **data._summary(prices)}
    return data.PriceData(prices, p)


@pytest.fixture
def dashboard(monkeypatch, tmp_path):
    payload = {"csv": CSV}
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: io.BytesIO(payload["csv"]))
    load = data.load_cache
    save = data.save_cache
    monkeypatch.setattr(data, "load_cache", lambda tickers, start, end, directory=None, **kwargs:
                        load(tickers, start, end, directory or tmp_path, **kwargs))
    monkeypatch.setattr(data, "save_cache", lambda item: save(item, tmp_path))
    calls = []

    def download(tickers, start, end, *, assume_usd=False):
        calls.append((tickers, start, end, assume_usd))
        return prices_data()

    monkeypatch.setattr(data, "download_prices", download)
    return payload, calls, tmp_path, lambda: AppTest.from_file(str(APP), default_timeout=20).run()


def test_explicit_download_cache_reuse_and_changed_allocation(dashboard):
    payload, calls, cache, run = dashboard
    at = run()
    assert not at.exception and not calls and not at.metric
    assert "download/refresh" in at.warning[0].value.lower()
    at.button[0].click().run()
    assert not at.exception
    assert calls == [(["A", "B"], "2022-01-01", "2026-01-01", False)]
    assert len(at.metric) == 2 and len(at.get("plotly_chart")) == 4
    assert at.table[3].value.loc["A"].iloc[3] < 0
    payload["csv"] = b"ticker,weight\nB,0.5\nA,0.5\n"
    at.run()
    assert not at.exception and len(calls) == 1
    assert list(at.table[3].value.index) == ["B", "A"]
    payload["csv"] = b"ticker,weight\nC,1\n"
    at.run()
    assert not at.exception and not at.metric and not at.get("plotly_chart")
    assert "refresh" in at.warning[0].value.lower()
    assert len(calls) == 1


@pytest.mark.parametrize("csv,reason", [
    (b"ticker,weight\nA,35%\n", "decimal"),
    (b"ticker,weight\nA,0.4\n", "sum to 1"),
    (b"ticker,weight\nA,0.5\na,0.5\n", "Duplicate"),
    (b"ticker,weight,price\nA,1,100\n", "only ticker,weight"),
])
def test_invalid_csv_stops_before_download(dashboard, csv, reason):
    payload, calls, _, run = dashboard
    payload["csv"] = csv
    at = run()
    assert not at.exception and reason in at.error[0].value
    assert not at.button and not at.metric and not calls


def test_corrupt_cache_and_failed_refresh_are_visible(dashboard, monkeypatch):
    _, calls, cache, run = dashboard
    at = run()
    at.checkbox[0].check().run()
    at.button[0].click().run()
    assert calls[-1][-1] is True
    prior = (cache / "prices.csv").read_bytes()

    def fail(*a, **k):
        raise data.DataError("Provider unavailable")

    monkeypatch.setattr(data, "download_prices", fail)
    at.button[0].click().run()
    assert "Provider unavailable" in at.error[0].value
    assert len(at.metric) == 2 and (cache / "prices.csv").read_bytes() == prior
    (cache / "prices.csv").write_bytes(prior + b"corruption")
    at.run()
    assert not at.exception and not at.metric
    assert "hash mismatch" in at.warning[0].value


@pytest.mark.parametrize("constant,rows", [(True, 301), (False, 20)])
def test_zero_risk_and_insufficient_history(dashboard, constant, rows):
    _, _, cache, run = dashboard
    data.save_cache(prices_data(constant=constant, rows=rows))
    at = run()
    assert not at.exception
    if constant:
        assert at.metric[0].value == "0.0000%"
        assert at.metric[1].value == "Unavailable"
        assert at.table[3].value.iloc[:, 2:].isna().all().all()
        assert any("undefined" in w.value for w in at.warning)
        assert len(at.get("plotly_chart")) == 4
    else:
        assert "Insufficient history" in at.error[0].value
        assert not at.metric and not at.get("plotly_chart")


def test_plot_units_signed_values_and_rolling_gaps():
    weights = data.load_portfolio(io.BytesIO(CSV))
    metrics = calculate_metrics(prices_data(gap=True).prices, weights)
    attribution = calculate_attribution(metrics.covariance, weights)
    figures = app.build_figures(weights, metrics, attribution, 60)
    assert len(figures) == 4
    np.testing.assert_allclose(figures[0].data[0].y, [20, 80])
    assert figures[1].data[0].zmin == -1 and figures[1].data[0].zmax == 1
    assert figures[2].data[0].y[0] < 0
    np.testing.assert_allclose(figures[2].data[0].y.sum(),
                               metrics.portfolio_volatility.annualized * 100)
    assert figures[3].data[0].connectgaps is False
    np.testing.assert_allclose(figures[3].data[0].y, metrics.rolling_volatility * 100,
                               equal_nan=True)
    assert np.isnan(figures[3].data[0].y[180:200]).all()


def test_default_requires_explicit_input(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("No cache or provider access before portfolio selection")
    monkeypatch.setattr(data, "load_cache", forbidden)
    monkeypatch.setattr(data, "download_prices", forbidden)
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception and not at.metric and not at.button
    assert "explicitly select" in at.info[0].value
