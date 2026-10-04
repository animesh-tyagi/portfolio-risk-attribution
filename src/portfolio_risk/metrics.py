"""Pure M2 calculations. Returns/volatilities are decimals; covariance is daily.

Static metrics share the latest complete sample. Rolling metrics retain union
dates and missing returns, so excluded dates cannot disappear inside a window.
No provider, cache, or UI calls belong here.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from .data import DataError, validate_prices


class MetricsError(DataError):
    """Invalid calculation inputs or insufficient usable observations."""


@dataclass
class ReturnSample:
    daily_returns: pd.DataFrame  # union dates, excluding the initial no-prior-price row
    returns: pd.DataFrame  # latest complete rows, shared by all static metrics
    excluded_dates: pd.Series  # True for incomplete/nonfinite daily return rows
    diagnostics: dict


@dataclass
class PortfolioVolatility:
    daily_variance: float
    daily: float
    annualized: float
    diagnostics: tuple[str, ...] = ()


@dataclass
class MetricsResult:
    sample: ReturnSample
    asset_volatility: pd.Series  # annualized decimal volatility
    covariance: pd.DataFrame  # daily decimal return squared
    correlation: pd.DataFrame  # dimensionless; NaN for constant assets
    portfolio_returns: pd.Series  # common static sample, fixed weights
    portfolio_volatility: PortfolioVolatility
    rolling_volatility: pd.Series  # annualized, date gaps retained
    warnings: tuple[str, ...]


def _integer(value, name: str, minimum: int = 1) -> None:
    if type(value) is not int or value < minimum:
        raise MetricsError(f"{name} must be an integer >= {minimum}.")


def _labels(labels, name: str) -> None:
    if len(labels) == 0 or labels.has_duplicates or any(
        not isinstance(t, str) or not t or t != t.strip().upper() for t in labels
    ):
        raise MetricsError(f"{name} require unique, nonempty canonical uppercase ticker labels.")


def _daily_index(index) -> None:
    if (not isinstance(index, pd.DatetimeIndex) or index.hasnans or index.has_duplicates
            or index.tz is not None or not index.equals(index.normalize())
            or not index.is_monotonic_increasing):
        raise MetricsError("Returns require sorted unique timezone-free daily dates.")


def _returns(returns: pd.DataFrame, *, allow_missing: bool = False) -> pd.DataFrame:
    if not isinstance(returns, pd.DataFrame) or returns.empty:
        raise MetricsError("Returns must be a nonempty ticker-labeled DataFrame.")
    _labels(returns.columns, "Returns")
    _daily_index(returns.index)
    try:
        values = returns.astype(float)
    except (ValueError, TypeError) as exc:
        raise MetricsError("Returns must be numeric decimals.") from exc
    array = values.to_numpy()
    if np.isinf(array).any() or (not allow_missing and np.isnan(array).any()):
        raise MetricsError("Use the same complete finite return sample for static metrics.")
    if not allow_missing and len(values) < 2:
        raise MetricsError("At least two complete returns are required for ddof=1.")
    return values


def _weights(weights: pd.Series, tickers) -> pd.Series:
    if not isinstance(weights, pd.Series):
        raise MetricsError("Weights must be a ticker-indexed Series of decimal capital weights.")
    _labels(weights.index, "Weights")
    if set(weights.index) != set(tickers):
        raise MetricsError("Weight tickers must match data tickers exactly.")
    try:
        aligned = weights.reindex(tickers).astype(float)
        total = math.fsum(aligned)
    except (ValueError, TypeError, OverflowError) as exc:
        raise MetricsError("Weights must be finite nonnegative decimals summing to 1.") from exc
    if (not np.isfinite(aligned).all() or (aligned < 0).any()
            or not math.isclose(total, 1, rel_tol=0, abs_tol=1e-8)):
        raise MetricsError("Weights must be finite nonnegative decimals summing to 1 within 1e-8; no normalization.")
    return aligned


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple adjacent-row returns on sorted union dates; never fill/drop prices.

    The first price row has no preceding price and is omitted. Other unavailable
    returns remain NaN, including both the missing-price date and its successor.
    """
    if not isinstance(prices, pd.DataFrame):
        raise MetricsError("Prices must be a ticker-labeled DataFrame.")
    _labels(prices.columns, "Prices")
    aligned = validate_prices(prices, prices.columns)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        returns = aligned.div(aligned.shift(1)).sub(1).iloc[1:]
    # Extreme but finite price ratios can overflow; exclude and diagnose them.
    return returns.replace([np.inf, -np.inf], np.nan)


def prepare_returns(prices: pd.DataFrame, *, lookback_returns: int = 756,
                    min_observations: int = 2) -> ReturnSample:
    """Select latest complete returns while preserving the full exclusion mask.

    The dashboard must pass its configured minimum (252). Small offline examples
    may use two observations, the mathematical minimum for sample covariance.
    """
    _integer(lookback_returns, "lookback_returns", 2)
    _integer(min_observations, "min_observations", 2)
    if min_observations > lookback_returns:
        raise MetricsError("min_observations cannot exceed lookback_returns.")
    daily = daily_returns(prices)
    excluded = (~np.isfinite(daily.to_numpy()).all(axis=1))
    mask = pd.Series(excluded, index=daily.index, name="excluded_return_date")
    complete = daily.loc[~mask]
    selected = complete.tail(lookback_returns).copy()
    if len(selected) < min_observations:
        raise MetricsError(f"Insufficient history: {len(selected)} usable common daily returns; "
                           f"require {min_observations} (no filling or normalization).")
    diagnostics = {
        "union_price_rows": len(prices), "candidate_return_rows": len(daily),
        "complete_return_rows": len(complete), "excluded_return_rows": int(mask.sum()),
        "selected_return_rows": len(selected),
        "complete_rows_outside_lookback": len(complete) - len(selected),
        "missing_prices_by_ticker": prices.isna().sum().astype(int).to_dict(),
        "unavailable_returns_by_ticker": daily.isna().sum().astype(int).to_dict(),
        "sample_first_date": selected.index[0].date().isoformat(),
        "sample_last_date": selected.index[-1].date().isoformat(),
        "limitation": "Days absent from every price series cannot be detected without an exchange calendar.",
    }
    return ReturnSample(daily, selected, mask, diagnostics)


def annualized_asset_volatility(returns: pd.DataFrame, *, trading_days: int = 252) -> pd.Series:
    """Sample standard deviation (ddof=1) times sqrt(trading_days)."""
    _integer(trading_days, "trading_days")
    values = _returns(returns)
    result = values.std(ddof=1) * math.sqrt(trading_days)
    if not np.isfinite(result).all():
        raise MetricsError("Asset volatility overflowed; inputs are outside the numerical range.")
    return result.rename("annualized_asset_volatility")


def daily_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    """Sample covariance, ddof=1; always a labeled NxN matrix, including N=1."""
    values = _returns(returns)
    result = values.cov(ddof=1)
    if not np.isfinite(result.to_numpy()).all():
        raise MetricsError("Covariance overflowed; inputs are outside the numerical range.")
    return result


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation on a complete sample; constant-asset cells are NaN."""
    values = _returns(returns)
    result = values.corr(method="pearson")
    constant = values.nunique() == 1
    result.loc[constant, :] = np.nan
    result.loc[:, constant] = np.nan
    return result


def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Fixed-weight, hypothetical daily-rebalanced returns, aligned by ticker.

    A gap in any requested asset invalidates the whole row, even at zero weight.
    This preserves the common-sample contract used by every metric.
    """
    values = _returns(returns, allow_missing=True)
    aligned = _weights(weights, values.columns)
    with np.errstate(over="ignore", invalid="ignore"):
        result = pd.Series(values.to_numpy() @ aligned.to_numpy(), index=values.index,
                           name="portfolio_return")
    if np.isinf(result).any():
        raise MetricsError("Portfolio returns overflowed.")
    return result


def portfolio_volatility(covariance: pd.DataFrame, weights: pd.Series, *,
                         trading_days: int = 252) -> PortfolioVolatility:
    """sqrt(w.T @ daily covariance @ w), with PSD/input validation.

    Singular matrices are valid. Tiny negative daily variance (<=1e-14 in
    magnitude) is clamped only with a retained diagnostic, as specified.
    """
    _integer(trading_days, "trading_days")
    if not isinstance(covariance, pd.DataFrame):
        raise MetricsError("Covariance must be a ticker-labeled square DataFrame.")
    _labels(covariance.columns, "Covariance columns")
    _labels(covariance.index, "Covariance rows")
    if set(covariance.index) != set(covariance.columns):
        raise MetricsError("Covariance row and column tickers must match.")
    aligned = _weights(weights, covariance.columns)
    try:
        matrix = covariance.loc[covariance.columns, covariance.columns].to_numpy(dtype=float)
    except (ValueError, TypeError) as exc:
        raise MetricsError("Covariance must be numeric.") from exc
    if not np.isfinite(matrix).all():
        raise MetricsError("Covariance must be finite.")
    if not np.allclose(matrix, matrix.T, rtol=0, atol=1e-14):
        raise MetricsError("Covariance must be symmetric.")
    # Tolerate only rounding-scale violations; never accept a materially
    # indefinite matrix just because this particular allocation has positive v.
    if np.linalg.eigvalsh(matrix).min() < -1e-14:
        raise MetricsError("Covariance must be positive semidefinite (PSD).")
    with np.errstate(over="ignore", invalid="ignore"):
        variance = float(aligned.to_numpy() @ matrix @ aligned.to_numpy())
    if not math.isfinite(variance) or variance < -1e-14:
        raise MetricsError("Invalid or materially negative portfolio variance.")
    diagnostics = ()
    if variance < 0:
        diagnostics = ("Tiny negative daily variance (<=1e-14) clamped to zero.",)
        variance = 0.0
    daily = math.sqrt(variance)
    annualized = daily * math.sqrt(trading_days)
    if not math.isfinite(annualized):
        raise MetricsError("Annualized portfolio volatility overflowed.")
    return PortfolioVolatility(variance, daily, annualized, diagnostics)


def rolling_portfolio_volatility(daily: pd.DataFrame, weights: pd.Series, *,
                                window: int = 60, trading_days: int = 252) -> pd.Series:
    """Annualized ddof=1 volatility over consecutive union return rows.

    Input must retain excluded dates as NaN rows (use ReturnSample.daily_returns,
    not its compact static returns). Full windows require every row to be valid.
    The first window-1 values and windows spanning a gap remain unavailable.
    """
    _integer(window, "window", 2)
    _integer(trading_days, "trading_days")
    result = portfolio_returns(daily, weights).rolling(window, min_periods=window).std(ddof=1)
    result *= math.sqrt(trading_days)
    return result.rename("annualized_rolling_portfolio_volatility")


def calculate_metrics(prices: pd.DataFrame, weights: pd.Series, *,
                      lookback_returns: int = 756, min_observations: int = 252,
                      rolling_window: int = 60, trading_days: int = 252) -> MetricsResult:
    """M2 pipeline; UI supplies loaded settings and displays diagnostics/NaNs.

    Rolling output covers the selected estimation span, including internal and
    trailing excluded dates. It does not borrow rows before the sample start.
    """
    sample = prepare_returns(prices, lookback_returns=lookback_returns,
                             min_observations=min_observations)
    common = sample.returns
    asset_vol = annualized_asset_volatility(common, trading_days=trading_days)
    covariance = daily_covariance(common)
    correlation = correlation_matrix(common)
    fixed_returns = portfolio_returns(common, weights)
    volatility = portfolio_volatility(covariance, weights, trading_days=trading_days)
    if not math.isclose(float(fixed_returns.std(ddof=1)), volatility.daily,
                        rel_tol=1e-8, abs_tol=1e-10):
        raise MetricsError("Portfolio covariance volatility does not reconcile with weighted-return std.")
    rolling_input = sample.daily_returns.loc[common.index[0]:]
    rolling = rolling_portfolio_volatility(rolling_input, weights, window=rolling_window,
                                          trading_days=trading_days)
    warnings = [sample.diagnostics["limitation"],
                "Fixed weights imply hypothetical daily rebalancing without costs or taxes.",
                "Square-root annualization is a convention, not a future-risk guarantee.",
                "Rolling volatility is unavailable before a full window or when the window spans excluded return dates."]
    constants = list(common.columns[common.nunique() == 1])
    if constants:
        warnings.append(f"Undefined correlation for constant-return assets: {', '.join(constants)} (including diagonal).")
    if sample.excluded_dates.any():
        warnings.append(f"Excluded {int(sample.excluded_dates.sum())} incomplete/nonfinite return dates; no prices or returns filled.")
    warnings.extend(volatility.diagnostics)
    return MetricsResult(sample, asset_vol, covariance, correlation, fixed_returns,
                         volatility, rolling, tuple(warnings))
