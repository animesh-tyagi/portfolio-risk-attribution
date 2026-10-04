"""Offline M1 validation. All fake provider responses/cache files are test-only."""

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from portfolio_risk import data

FIXTURE = data.ROOT / "tests/fixtures/prices_synthetic.csv"
START, END = "2024-01-01", "2024-02-01"


@pytest.fixture
def prices():
    return data.load_price_csv(FIXTURE, ["A", "B"])


@pytest.fixture
def provider(monkeypatch, prices):
    calls = []
    currency = {"A": "USD", "B": "USD"}
    raw = pd.concat({"Close": prices, "Open": prices * 0.9}, axis=1)

    def download(**kwargs):
        calls.append(kwargs)
        return fake.raw.copy()

    def info(ticker):
        value = currency[ticker]
        if isinstance(value, Exception):
            raise value
        return {"currency": value}

    fake = SimpleNamespace(__version__="test-only", raw=raw, calls=calls, currency=currency,
                           download=download, set_tz_cache_location=lambda _: None,
                           Ticker=lambda ticker: SimpleNamespace(get_info=lambda: info(ticker)))
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    return fake


def test_portfolio_trim_order_single_zero_and_arbitrary_asset_count():
    w = data.load_portfolio(io.BytesIO(b" weight , ticker \n0.25, b \n0.75,A\n0,C\n"))
    assert list(w.index) == ["B", "A", "C"]
    assert list(w) == [0.25, 0.75, 0]
    assert data.load_portfolio(io.StringIO("ticker,weight\nANY,1\n")).to_dict() == {"ANY": 1}
    csv = "ticker,weight\n" + "\n".join(f"T{i},0.125" for i in range(8))
    assert len(data.load_portfolio(io.StringIO(csv))) == 8


@pytest.mark.parametrize("text", ["", "ticker,weight\n", "ticker,weight,quantity\nA,1,1",
    "ticker,ticker\nA,A", "ticker,weight\n,1", "ticker,weight\nA,0.5\n a ,0.5",
    "ticker,weight\nA,35%", "ticker,weight\nA,no", "ticker,weight\nA,nan",
    "ticker,weight\nA,inf", "ticker,weight\nA,-0.1\nB,1.1", "ticker,weight\nA,100",
    "ticker,weight\nA,0", "ticker,weight\nA,0.9", "ticker,weight\nA,1,extra",
    "ticker,weight\nA", "ticker,weight\nA B,1", "ticker,weight\nA,1e308\nB,1e308"])
def test_invalid_portfolios(text):
    with pytest.raises(data.DataError):
        data.load_portfolio(io.StringIO(text))


def test_weight_tolerance_does_not_normalize():
    w = data.load_portfolio(io.StringIO("ticker,weight\nA,1.000000001"))
    assert w.iloc[0] == 1.000000001
    with pytest.raises(data.DataError):
        data.load_portfolio(io.StringIO("ticker,weight\nA,1.00000002"))


def test_synthetic_known_prices_alignment_and_gaps(prices):
    assert list(prices["A"]) == [100, 110, 99, 99]
    assert list(prices["B"]) == [200, 200, 220, 220]
    assert data.validate_prices(prices.iloc[::-1], ["B", "A"]).iloc[0].tolist() == [200, 100]
    prices.loc[prices.index[1], "A"] = np.nan
    result = data.validate_prices(prices, ["A", "B"])
    assert len(result) == 4 and np.isnan(result.iloc[1, 0])  # no filling or dropping


@pytest.mark.parametrize("value", [0, -1, np.inf, -np.inf, "bad"])
def test_invalid_observed_prices(prices, value):
    prices = prices.astype(object)
    prices.iloc[0, 0] = value
    with pytest.raises(data.DataError):
        data.validate_prices(prices, ["A", "B"])


def test_duplicate_dates_missing_symbol_and_all_missing(prices):
    with pytest.raises(data.DataError, match="Duplicate"):
        data.validate_prices(pd.concat([prices, prices.iloc[:1]]), ["A", "B"])
    with pytest.raises(data.DataError, match="columns"):
        data.validate_prices(prices, ["A", "C"])
    prices["B"] = np.nan
    with pytest.raises(data.DataError, match="Unavailable symbols.*B"):
        data.validate_prices(prices, ["A", "B"])


@pytest.mark.parametrize("text", ["date,A,A\n2024-01-02,1,2", "date,A\n20240102,1",
    "date,A\n2024-01-02,nan", "date,A\n2024-01-02,foo", "date,A\n2024-01-02,1,2"])
def test_price_csv_schema(text):
    with pytest.raises(data.DataError):
        data.load_price_csv(io.StringIO(text), ["A"])


def test_explicit_adapter_flags_and_adjusted_close(provider, prices):
    result = data.download_prices(["B", "A"], START, END)
    pd.testing.assert_frame_equal(result.prices, prices[["B", "A"]])
    args = provider.calls[0]
    assert args["tickers"] == ["B", "A"] and args["interval"] == "1d"
    assert args["auto_adjust"] is True and args["keepna"] is True
    assert args["repair"] is False and args["start"] == START and args["end"] == END
    assert result.provenance["currency_verification"]["A"]["basis"] == "source-verified"


@pytest.mark.parametrize("layout", ["flat", "field-first", "ticker-first"])
def test_single_ticker_and_multiindex_layouts(provider, prices, layout):
    raw = prices[["A"]].rename(columns={"A": "Close"})
    if layout == "field-first":
        raw.columns = pd.MultiIndex.from_tuples([("Close", "A")])
    elif layout == "ticker-first":
        raw.columns = pd.MultiIndex.from_tuples([("A", "Close")])
    provider.raw = raw
    pd.testing.assert_frame_equal(data.download_prices(["A"], START, END).prices, prices[["A"]])


@pytest.mark.parametrize("unknown", [None, "", RuntimeError("metadata unreachable")])
def test_unknown_currency_requires_explicit_confirmation(provider, unknown):
    provider.currency["A"] = unknown
    with pytest.raises(data.DataError, match="assume-usd"):
        data.download_prices(["A", "B"], START, END)
    result = data.download_prices(["A", "B"], START, END, assume_usd=True)
    assert result.provenance["currency_verification"]["A"]["basis"] == "user-confirmed"
    assert result.provenance["warnings"]


def test_non_usd_is_never_overridden(provider):
    provider.currency["B"] = "EUR"
    with pytest.raises(data.DataError, match="EUR"):
        data.download_prices(["A", "B"], START, END, assume_usd=True)


def test_provider_failure_and_missing_close(provider):
    provider.raw = pd.DataFrame()
    with pytest.raises(data.DataError, match="no data"):
        data.download_prices(["A", "B"], START, END)
    provider.raw = pd.DataFrame({"Adj Close": [100]}, index=pd.to_datetime(["2024-01-02"]))
    with pytest.raises(data.DataError, match="Close"):
        data.download_prices(["A"], START, END)


def test_provider_out_of_range_and_unavailable_symbol(provider):
    with pytest.raises(data.DataError, match="outside"):
        data.download_prices(["A", "B"], "2024-01-04", END)
    provider.raw[("Close", "B")] = np.nan
    with pytest.raises(data.DataError, match="Unavailable symbols.*B"):
        data.download_prices(["A", "B"], START, END)


def test_cache_roundtrip_offline_reorder_weights_and_missing_values(provider, tmp_path):
    provider.raw.loc[provider.raw.index[1], ("Close", "A")] = np.nan
    result = data.download_prices(["A", "B"], START, END)
    data.save_cache(result, tmp_path)
    provider.download = lambda **_: pytest.fail("Cache load must stay offline")
    # Cache matching receives ticker labels only; changing weights cannot invalidate it.
    weights = data.load_portfolio(io.StringIO("ticker,weight\nB,0.9\nA,0.1"))
    loaded = data.load_cache(weights.index, START, END, tmp_path)
    pd.testing.assert_frame_equal(loaded.prices, result.prices[["B", "A"]])
    assert loaded.provenance["missing_values"] == {"A": 1, "B": 0}
    assert len(loaded.provenance["prices_sha256"]) == 64


@pytest.mark.parametrize("change", ["hash", "tickers", "dates", "adjustment", "currency", "row_count", "basis", "timestamp", "missing", "version"])
def test_cache_mismatch_and_corruption(provider, tmp_path, change):
    data.save_cache(data.download_prices(["A", "B"], START, END), tmp_path)
    path = tmp_path / "manifest.json"
    m = json.loads(path.read_text())
    if change == "hash":
        (tmp_path / "prices.csv").write_text("date,A,B\n2024-01-02,1,2\n")
    elif change == "tickers":
        with pytest.raises(data.CacheError):
            data.load_cache(["A"], START, END, tmp_path)
        return
    elif change == "dates":
        with pytest.raises(data.CacheError):
            data.load_cache(["A", "B"], "2023-01-01", END, tmp_path)
        return
    elif change == "adjustment":
        m["auto_adjust"] = False
    elif change == "currency":
        m["quote_currency"] = "EUR"
    elif change == "row_count":
        m["row_count"] = 999
    elif change == "basis":
        m["currency_verification"]["A"]["basis"] = "guessed"
    elif change == "timestamp":
        m["retrieved_at_utc"] = "2024-01-01"  # timezone is required
    elif change == "missing":
        m["missing_values"]["A"] = 7
    else:
        m.pop("provider_version")
    path.write_text(json.dumps(m))
    with pytest.raises(data.CacheError):
        data.load_cache(["A", "B"], START, END, tmp_path)


def test_failed_refresh_and_write_preserve_cache(provider, tmp_path, monkeypatch):
    good = data.download_prices(["A", "B"], START, END)
    data.save_cache(good, tmp_path)
    before = [(tmp_path / name).read_bytes() for name in ("prices.csv", "manifest.json")]
    provider.raw.iloc[:, :] = np.nan
    with pytest.raises(data.DataError):
        data.save_cache(data.download_prices(["A", "B"], START, END), tmp_path)
    replace = os.replace
    def fail_manifest(src, dst):
        if Path(dst).name == "manifest.json":
            raise OSError("test-only simulated disk failure")
        replace(src, dst)
    monkeypatch.setattr(data.os, "replace", fail_manifest)
    with pytest.raises(OSError):
        data.save_cache(good, tmp_path)
    assert [(tmp_path / name).read_bytes() for name in ("prices.csv", "manifest.json")] == before
    data.load_cache(["A", "B"], START, END, tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == {"prices.csv", "manifest.json"}


def test_settings_and_paths_independent_of_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert data.load_settings()["base_currency"] == "USD"
    assert len(data.load_portfolio()) == 5  # bundled example only
    settings = data.load_settings()
    settings["base_currency"] = "EUR"
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings))
    with pytest.raises(data.DataError, match="USD"):
        data.load_settings(path)
    path.write_text("[]")
    with pytest.raises(data.DataError, match="JSON object"):
        data.load_settings(path)


def test_cli_cache_load_from_other_working_directory(provider, tmp_path):
    settings = data.load_settings()
    result = data.download_prices(["A", "B"], settings["download_start"], settings["download_end_exclusive"])
    data.save_cache(result, tmp_path)
    portfolio = tmp_path / "portfolio.csv"
    portfolio.write_text("ticker,weight\nB,0.3\nA,0.7\n")
    command = [sys.executable, str(data.ROOT / "scripts/download_data.py"), "--load-cache",
               "--portfolio", str(portfolio), "--cache-dir", str(tmp_path)]
    proc = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "4 union dates" in proc.stdout and "M1 price-data verification only" in proc.stdout


def test_missing_cache(tmp_path):
    with pytest.raises(data.CacheError, match="refresh"):
        data.load_cache(["A"], START, END, tmp_path)
