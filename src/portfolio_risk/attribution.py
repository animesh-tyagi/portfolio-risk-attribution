"""Pure M3 volatility attribution on the common daily covariance from M2.

Volatility and contributions are decimals. Risk shares and diversification benefit
are fractions; multiply by 100 only for display. No provider or UI calls.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import pandas as pd

from .metrics import MetricsError, PortfolioVolatility, _weights, portfolio_volatility


@dataclass
class AttributionResult:
    table: pd.DataFrame  # ticker index in portfolio order, explicit units in columns
    portfolio_volatility: PortfolioVolatility
    weighted_standalone_daily_volatility: float
    diversification_benefit: float  # fraction, NaN when unavailable
    attribution_unavailable_reason: str | None
    diversification_unavailable_reason: str | None
    diagnostics: tuple[str, ...]


def calculate_attribution(covariance: pd.DataFrame, weights: pd.Series, *,
                          trading_days: int = 252) -> AttributionResult:
    """Euler marginal/component risk and the specified diversification benefit.

    Both covariance axes and weights are aligned by ticker before arithmetic.
    MRC is unconstrained weight sensitivity; a funded move from j to i has
    sensitivity MRC[i] - MRC[j]. Singular covariance and signed CRC are valid.
    At daily portfolio volatility <=1e-12, all attribution columns stay NaN.
    Benefit = 1 - sigma_p / sum(w_i * sigma_i), using the same daily horizon.
    """
    volatility = portfolio_volatility(covariance, weights, trading_days=trading_days)
    aligned = _weights(weights, weights.index)
    matrix = covariance.loc[aligned.index, aligned.index].to_numpy(dtype=float)
    w = aligned.to_numpy()
    scale = math.sqrt(trading_days)
    diagnostics = list(volatility.diagnostics)
    diagonal = np.diag(matrix)
    # M2 tolerates rounding-scale PSD violations. A negative diagonal has no
    # real standalone std: do not invent one, even if portfolio variance is valid.
    asset_daily = np.full(len(w), np.nan)
    np.sqrt(diagonal, out=asset_daily, where=diagonal >= 0)
    table = pd.DataFrame({"weight": aligned,
                          "daily_asset_volatility": asset_daily,
                          "annualized_asset_volatility": asset_daily * scale})
    columns = ("daily_marginal_contribution", "annualized_marginal_contribution",
               "daily_component_contribution", "annualized_component_contribution",
               "risk_share")
    table[list(columns)] = np.nan
    attribution_reason = None
    if volatility.daily <= 1e-12:
        attribution_reason = ("Daily portfolio volatility is zero/negligible (<=1e-12); "
                              "marginal/component contributions and risk shares are undefined.")
    else:
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            marginal = (matrix @ w) / volatility.daily
            component = w * marginal
            shares = component / volatility.daily
            annual_marginal = marginal * scale
            annual_component = component * scale
        if not all(np.isfinite(x).all() for x in
                   (marginal, component, shares, annual_marginal, annual_component)):
            raise MetricsError("Risk attribution overflowed; inputs are outside the numerical range.")
        for total, expected in ((math.fsum(component), volatility.daily),
                                (math.fsum(annual_component), volatility.annualized),
                                (math.fsum(shares), 1.0)):
            if not math.isclose(total, expected, rel_tol=1e-8, abs_tol=1e-10):
                raise MetricsError("Risk contributions do not reconcile with portfolio volatility.")
        table[list(columns)] = np.column_stack(
            [marginal, annual_marginal, component, annual_component, shares])

    benefit = float("nan")
    benefit_reason = None
    standalone = float("nan")
    if np.isnan(asset_daily).any():
        benefit_reason = "Standalone volatility is undefined for a negative covariance diagonal."
        diagnostics.append(benefit_reason)
    else:
        standalone = math.fsum(w * asset_daily)
        if standalone <= 1e-12:
            benefit_reason = "Weighted standalone daily volatility is zero/negligible (<=1e-12)."
        else:
            benefit = 1 - volatility.daily / standalone
    return AttributionResult(table, volatility, standalone, benefit, attribution_reason,
                             benefit_reason, tuple(diagnostics))
