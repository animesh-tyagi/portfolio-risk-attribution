"""M1 input and market-data boundary. Nothing downloads at import or cache load."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import platform
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ADJUSTMENT = "yfinance auto_adjust=True; adjusted Close (splits and distributions)"
SOURCE = "Yahoo Finance via yfinance (third-party wrapper)"


class DataError(ValueError):
    """Invalid inputs or unavailable provider data; never replace with fake data."""


class CacheError(DataError):
    """Absent, mismatched or damaged cache; an explicit refresh is required."""


@dataclass
class PriceData:
    prices: pd.DataFrame
    provenance: dict


def project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def _read_csv(source: str | Path | IO) -> list[list[str]]:
    try:
        if isinstance(source, (str, Path)):
            content = project_path(source).read_text(encoding="utf-8-sig")
        else:
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(content), strict=True))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DataError(f"Cannot read UTF-8 CSV: {exc}") from exc


def load_portfolio(source: str | Path | IO = "data/portfolio.csv") -> pd.Series:
    """Return decimal weights indexed by canonical uppercase ticker, in row order."""
    rows = _read_csv(source)
    if not rows or len(rows[0]) != 2 or set(h.strip() for h in rows[0]) != {"ticker", "weight"}:
        raise DataError("Portfolio CSV requires only ticker,weight columns (decimal weights).")
    headers = [h.strip() for h in rows[0]]
    tickers, weights = [], []
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise DataError(f"Portfolio row {number} must contain ticker and decimal weight.")
        ticker = row[headers.index("ticker")].strip().upper()
        if not ticker or any(c.isspace() for c in ticker) or "," in ticker:
            raise DataError(f"Missing or invalid ticker on row {number}.")
        if ticker in tickers:
            raise DataError(f"Duplicate ticker after trimming/case normalization: {ticker}.")
        try:
            weight = float(row[headers.index("weight")])
        except ValueError as exc:
            raise DataError(f"{ticker}: use a decimal weight such as 0.35, not 35%.") from exc
        if not math.isfinite(weight) or weight < 0:
            raise DataError(f"{ticker}: weight must be finite and nonnegative.")
        tickers.append(ticker)
        weights.append(weight)
    if not tickers:
        raise DataError("Portfolio must contain at least one holding.")
    try:
        total = math.fsum(weights)
    except OverflowError as exc:
        raise DataError("Decimal weights must sum to 1; their sum overflowed. No normalization applied.") from exc
    if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-8):
        raise DataError(f"Decimal weights must sum to 1 within 1e-8; got {total:g}. No normalization applied.")
    return pd.Series(weights, index=pd.Index(tickers, name="ticker"), name="weight", dtype=float)


def _request(tickers, start: str, end: str, currency: str = "USD") -> list[str]:
    if isinstance(tickers, str):
        raise DataError("Pass an explicit list of tickers, including for a single asset.")
    names = list(tickers)
    if not names or any(not isinstance(t, str) or not t or t != t.strip().upper() for t in names):
        raise DataError("Tickers must be nonempty canonical uppercase labels.")
    if len(names) != len(set(names)):
        raise DataError("Duplicate requested tickers.")
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.isoformat() != start or last.isoformat() != end or first >= last:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise DataError("Use YYYY-MM-DD dates with start before exclusive end.") from exc
    if currency != "USD":
        raise DataError("MVP supports USD quotes only; no FX conversion is performed.")
    return names


def load_settings(path: str | Path = "config/settings.json") -> dict:
    try:
        settings = json.loads(project_path(path).read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise DataError("Settings must be a JSON object.")
        if not isinstance(settings.get("title"), str) or not settings["title"].strip():
            raise DataError("title must be a nonempty string.")
        _request(["SETTINGS"], settings["download_start"], settings["download_end_exclusive"], settings["base_currency"])
        for key in ("trading_days", "lookback_returns", "rolling_window", "min_observations"):
            if type(settings[key]) is not int or settings[key] <= 0:
                raise DataError(f"{key} must be a positive integer.")
        if settings["trading_days"] != 252 or not settings["lookback_returns"] >= settings["min_observations"] >= 252:
            raise DataError("Require 252 annualization days and lookback >= minimum >= 252.")
        if not 2 <= settings["rolling_window"] <= settings["lookback_returns"]:
            raise DataError("Rolling window must be between 2 and lookback_returns.")
        if {"holdings", "weights", "portfolio_value", "confidence", "scenarios"} & settings.keys():
            raise DataError("Settings must not contain holdings or out-of-scope configuration.")
        return settings
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise DataError(f"Invalid settings: {exc}") from exc


def validate_prices(prices: pd.DataFrame, tickers) -> pd.DataFrame:
    """Validate observed prices, keep gaps, sort union dates, align by ticker."""
    names = list(tickers)
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        raise DataError("No historical prices returned; requested symbols may be unavailable.")
    if prices.columns.has_duplicates or set(prices.columns) != set(names):
        raise DataError(f"Price columns must match requested tickers {names}; got {list(prices.columns)}.")
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.index.hasnans:
        raise DataError("Prices require valid daily dates in a DatetimeIndex.")
    if prices.index.tz is not None or not prices.index.equals(prices.index.normalize()):
        raise DataError("Prices require timezone-free daily dates without intraday times.")
    if prices.index.has_duplicates:
        raise DataError("Duplicate price dates are invalid.")
    aligned = prices.loc[:, names].copy().sort_index()
    try:
        aligned = aligned.apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise DataError("Observed prices must be numeric.") from exc
    values = aligned.to_numpy()
    observed = ~np.isnan(values)
    if np.any(observed & (~np.isfinite(values) | (values <= 0))):
        raise DataError("Observed prices must be finite and strictly positive; gaps remain missing.")
    unavailable = [t for t in names if aligned[t].isna().all()]
    if unavailable:
        raise DataError(f"Unavailable symbols (no observed prices): {', '.join(unavailable)}.")
    aligned.index.name = "date"
    return aligned


def load_price_csv(source: str | Path | IO, tickers) -> pd.DataFrame:
    rows = _read_csv(source)
    names = list(tickers)
    if not rows or len(rows[0]) != len(names) + 1 or rows[0][0] != "date" or set(rows[0][1:]) != set(names):
        raise DataError("Price CSV requires date followed by exactly the requested ticker columns.")
    if any(len(row) != len(rows[0]) for row in rows[1:]):
        raise DataError("Malformed price CSV row.")
    try:
        dates = [date.fromisoformat(row[0]) for row in rows[1:]]
        if any(d.isoformat() != row[0] for d, row in zip(dates, rows[1:])):
            raise ValueError("Dates must be YYYY-MM-DD.")
        values = [[float(v) if v else np.nan for v in row[1:]] for row in rows[1:]]
    except (ValueError, OverflowError) as exc:
        raise DataError(f"Invalid price CSV dates or numeric values: {exc}") from exc
    # Only empty cells are missing. Textual NaN is not an observed price.
    if any(v.strip().lower() in {"nan", "+nan", "-nan"} for row in rows[1:] for v in row[1:]):
        raise DataError("Use empty cells for missing prices, not textual NaN.")
    return validate_prices(pd.DataFrame(values, index=pd.DatetimeIndex(dates), columns=rows[0][1:]), names)


def _summary(prices: pd.DataFrame) -> dict:
    return {"actual_first_date": prices.index[0].date().isoformat(),
            "actual_last_date": prices.index[-1].date().isoformat(),
            "row_count": len(prices),
            "missing_values": {t: int(prices[t].isna().sum()) for t in prices.columns}}


def _extract_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if raw is None or raw.empty:
        raise DataError("Provider returned no data; check symbols, dates and network access.")
    if isinstance(raw.columns, pd.MultiIndex):
        if raw.columns.nlevels != 2:
            raise DataError("Unsupported provider column structure.")
        levels = [i for i in range(2) if "Close" in raw.columns.get_level_values(i)]
        if len(levels) != 1:
            raise DataError("Provider response lacks an unambiguous adjusted Close field.")
        prices = raw.xs("Close", axis=1, level=levels[0]).copy()
    elif len(tickers) == 1 and "Close" in raw.columns:
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})
    else:
        raise DataError("Provider response lacks ticker-labeled adjusted Close prices.")
    if isinstance(prices.index, pd.DatetimeIndex) and prices.index.tz is not None:
        prices.index = prices.index.tz_localize(None)
    return validate_prices(prices, tickers)


def download_prices(tickers, start: str, end_exclusive: str, *, assume_usd: bool = False) -> PriceData:
    """Explicit network adapter; callers choose when to invoke it, then save cache."""
    names = _request(tickers, start, end_exclusive)
    try:
        import yfinance as yf
    except ImportError as exc:
        raise DataError('Install the data extra: python -m pip install -e ".[dev,data]".') from exc
    try:
        # Keep yfinance's own cookie/timezone cache local and Git-ignored as well.
        yf.set_tz_cache_location(str(ROOT / "data/raw/yfinance"))
        raw = yf.download(tickers=names, start=start, end=end_exclusive, interval="1d",
                          auto_adjust=True, back_adjust=False, repair=False, keepna=True,
                          progress=False, threads=False, ignore_tz=True, timeout=15)
        prices = _extract_close(raw, names)
        if (prices.index < pd.Timestamp(start)).any() or (prices.index >= pd.Timestamp(end_exclusive)).any():
            raise DataError("Provider returned dates outside the requested interval.")
        currency = {}
        warnings = []
        for ticker in names:
            reason = "Provider currency metadata absent."
            try:
                info = yf.Ticker(ticker).get_info()
                quote = info.get("currency")
            except Exception as exc:
                quote = None
                reason = f"Provider currency metadata unavailable ({type(exc).__name__})."
            if quote is not None and str(quote).strip():
                if str(quote).strip().upper() != "USD":
                    raise DataError(f"{ticker} is quoted in {quote}; USD quotes only, no FX conversion.")
                currency[ticker] = {"quote_currency": "USD", "basis": "source-verified", "metadata_field": "currency"}
            else:
                if not assume_usd:
                    raise DataError(f"{ticker}: {reason} Confirm USD explicitly with --assume-usd (CLI) or a UI confirmation.")
                currency[ticker] = {"quote_currency": "USD", "basis": "user-confirmed", "reason": reason}
                warnings.append(f"{ticker}: USD assumed by explicit user confirmation; {reason}")
        manifest = {"schema_version": 1, "provider": "yfinance", "source": SOURCE,
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                    "python_version": platform.python_version(), "provider_version": yf.__version__,
                    "requested_tickers": names, "quote_currency": "USD", "currency_verification": currency,
                    "requested_start": start, "requested_end_exclusive": end_exclusive,
                    "interval": "1d", "auto_adjust": True, "adjustment": ADJUSTMENT,
                    "provider_column_structure": [list(c) if isinstance(c, tuple) else c for c in raw.columns],
                    "warnings": warnings, **_summary(prices)}
        return PriceData(prices, manifest)
    except DataError:
        raise
    except Exception as exc:
        raise DataError(f"Market-data download failed ({type(exc).__name__}): {exc}. Existing cache is unchanged.") from exc


def _validate_provenance(manifest: dict, prices: pd.DataFrame, names: list[str], start: str, end: str) -> None:
    expected = {"schema_version": 1, "provider": "yfinance", "source": SOURCE,
                "quote_currency": "USD", "requested_start": start, "requested_end_exclusive": end,
                "interval": "1d", "auto_adjust": True, "adjustment": ADJUSTMENT, **_summary(prices)}
    if any(type(manifest.get(k)) is not type(v) or manifest.get(k) != v for k, v in expected.items()):
        raise CacheError("Stale/mismatched cache: request, adjustment, currency or price diagnostics differ. Explicit refresh required.")
    saved_names = manifest.get("requested_tickers")
    if not isinstance(saved_names, list) or len(saved_names) != len(names) or set(saved_names) != set(names):
        raise CacheError("Stale cache: ticker set changed. Explicit refresh required.")
    verification = manifest.get("currency_verification", {})
    if not isinstance(verification, dict) or set(verification) != set(names):
        raise CacheError("Cache is missing ticker currency provenance.")
    for ticker in names:
        entry = verification[ticker]
        if not isinstance(entry, dict) or entry.get("quote_currency") != "USD" or entry.get("basis") not in {"source-verified", "user-confirmed"}:
            raise CacheError(f"Cache has invalid USD currency provenance for {ticker}.")
        if entry["basis"] == "source-verified" and entry.get("metadata_field") != "currency":
            raise CacheError(f"Cache lacks source currency field for {ticker}.")
        if entry["basis"] == "user-confirmed" and not entry.get("reason"):
            raise CacheError(f"Cache lacks unknown-currency warning for {ticker}.")
    try:
        retrieved = datetime.fromisoformat(manifest["retrieved_at_utc"])
        if retrieved.tzinfo is None or retrieved.utcoffset().total_seconds() != 0 or retrieved > datetime.now(timezone.utc):
            raise ValueError
        if not all(isinstance(manifest[k], str) and manifest[k] for k in ("python_version", "provider_version")):
            raise ValueError
        if not isinstance(manifest["warnings"], list) or any(not isinstance(w, str) for w in manifest["warnings"]):
            raise ValueError
    except (ValueError, TypeError, KeyError) as exc:
        raise CacheError("Cache retrieval timestamp, versions or warnings are invalid.") from exc
    if (prices.index < pd.Timestamp(start)).any() or (prices.index >= pd.Timestamp(end)).any():
        raise CacheError("Cached dates fall outside the requested interval.")


def save_cache(data: PriceData, directory: str | Path = "data/processed") -> None:
    """Stage and verify both files before replacement; roll back on write failure."""
    manifest = data.provenance.copy()
    try:
        names = _request(manifest["requested_tickers"], manifest["requested_start"], manifest["requested_end_exclusive"])
        prices = validate_prices(data.prices, names)
        _validate_provenance(manifest, prices, names, manifest["requested_start"], manifest["requested_end_exclusive"])
    except (KeyError, TypeError) as exc:
        raise CacheError("Incomplete cache provenance.") from exc
    payload = prices.to_csv(index=True, index_label="date", date_format="%Y-%m-%d", lineterminator="\n").encode("utf-8")
    manifest["prices_sha256"] = hashlib.sha256(payload).hexdigest()
    metadata = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode("utf-8")
    directory = project_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    targets = [directory / "prices.csv", directory / "manifest.json"]
    old = [p.read_bytes() if p.exists() else None for p in targets]
    staged = []
    replaced = []
    try:
        for content in (payload, metadata):
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
                staged.append(Path(handle.name))
                handle.write(content)
        load_cache(names, manifest["requested_start"], manifest["requested_end_exclusive"], directory,
                   _files=staged)
        for temp, target in zip(staged, targets):
            os.replace(temp, target)
            replaced.append(target)
    except Exception:
        for target, previous in zip(targets, old):
            if target in replaced:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(previous)
        raise
    finally:
        for temp in staged:
            temp.unlink(missing_ok=True)


def load_cache(tickers, start: str, end_exclusive: str, directory: str | Path = "data/processed", *, _files=None) -> PriceData:
    """Offline validated cache read; fixed historical samples have no arbitrary TTL.

    A request mismatch is stale. Retrieval time is preserved for display; provider
    revisions require an explicit refresh. Hash validation detects a torn write.
    """
    names = _request(tickers, start, end_exclusive)
    directory = project_path(directory)
    files = _files or [directory / "prices.csv", directory / "manifest.json"]
    try:
        payload = files[0].read_bytes()
        manifest = json.loads(files[1].read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("prices_sha256") != hashlib.sha256(payload).hexdigest():
            raise CacheError("Cache integrity/hash mismatch. Explicit refresh required.")
        prices = load_price_csv(io.BytesIO(payload), names)
        _validate_provenance(manifest, prices, names, start, end_exclusive)
        return PriceData(prices, manifest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CacheError(f"Cache unavailable or invalid: {exc}. Use an explicit download/refresh.") from exc
