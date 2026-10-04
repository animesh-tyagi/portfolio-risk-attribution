"""Single-page M4 dashboard; finance stays in the tested calculation engine."""

import io
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from portfolio_risk.attribution import calculate_attribution
from portfolio_risk.data import (
    CacheError, DataError, download_prices, load_cache, load_portfolio,
    load_settings, save_cache,
)
from portfolio_risk.metrics import calculate_metrics


def display_table(attribution):
    """Convert engine decimals to presentation units only."""
    columns = {
        "weight": "Capital weight (%)",
        "annualized_asset_volatility": "Annualized asset volatility (%)",
        "annualized_marginal_contribution": "Annualized marginal risk (volatility pp / unit weight)",
        "annualized_component_contribution": "Annualized component risk (volatility pp)",
        "risk_share": "Share of total volatility (%)",
    }
    return (attribution.table.loc[:, list(columns)] * 100).rename(columns=columns)


def build_figures(weights, metrics, attribution, rolling_window):
    """Exactly four plots, using engine results; no financial calculations."""
    allocation = go.Figure(go.Bar(x=weights.index, y=weights * 100,
                                 hovertemplate="%{x}: %{y:.2f}% capital<extra></extra>"))
    allocation.update_layout(title="Portfolio allocation", xaxis_title="Ticker",
                             yaxis_title="Capital weight (%)")
    correlation = go.Figure(go.Heatmap(
        x=metrics.correlation.columns, y=metrics.correlation.index,
        z=metrics.correlation.to_numpy(), zmin=-1, zmax=1,
        colorscale="RdBu", reversescale=True, hoverongaps=False,
        colorbar_title="Correlation",
        hovertemplate="%{y} / %{x}: %{z:.4f}<extra></extra>"))
    correlation.update_layout(title="Correlation matrix (dimensionless)",
                              xaxis_title="Ticker", yaxis_title="Ticker")
    components = attribution.table["annualized_component_contribution"] * 100
    risk = go.Figure(go.Bar(
        x=components.index, y=components,
        marker_color=["#c0392b" if value < 0 else "#2471a3" for value in components],
        hovertemplate="%{x}: %{y:.4f} volatility pp<extra></extra>"))
    risk.update_layout(title="Signed annualized risk contribution by asset",
                       xaxis_title="Ticker", yaxis_title="Component risk (volatility pp)",
                       yaxis_zeroline=True, yaxis_zerolinewidth=2)
    if attribution.attribution_unavailable_reason:
        risk.add_annotation(text="Risk contributions unavailable: zero/negligible volatility",
                            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    rolling = go.Figure(go.Scatter(
        x=metrics.rolling_volatility.index, y=metrics.rolling_volatility * 100,
        mode="lines", connectgaps=False,
        hovertemplate="%{x|%Y-%m-%d}: %{y:.4f}%<extra></extra>"))
    rolling.update_layout(title=f"Annualized {rolling_window}-day rolling portfolio volatility",
                          xaxis_title="Return date", yaxis_title="Annualized volatility (%)")
    return allocation, correlation, risk, rolling


def show_provenance(data, settings):
    p = data.provenance
    st.subheader("Historical prices and provenance")
    st.write(f"Source: {p['source']} · yfinance {p['provider_version']} · "
             f"Python {p['python_version']} · Retrieved UTC: {p['retrieved_at_utc']}")
    st.write(f"Requested: {settings['download_start']} through exclusive "
             f"{settings['download_end_exclusive']}. Actual prices: "
             f"{p['actual_first_date']} through {p['actual_last_date']} "
             f"({p['row_count']} union price dates). Quote currency: USD.")
    st.caption(p["adjustment"])
    st.table(pd.DataFrame.from_dict(p["currency_verification"], orient="index")
                 .rename_axis("ticker"))
    st.caption("Fixed completed historical sample: cache age alone does not invalidate it. "
               "Request or integrity mismatches require refresh; provider revisions are "
               "obtained only by explicit refresh.")
    for warning in p["warnings"]:
        st.warning(warning)


def main():
    st.set_page_config(page_title="Portfolio Risk Attribution", layout="wide")
    try:
        settings = load_settings()
    except DataError as exc:
        st.error(str(exc))
        st.stop()
    st.title(settings["title"])
    st.caption("Historical portfolio volatility analysis · Long-only, fully invested, USD quotes")
    choice = st.radio("Portfolio input", ["Upload portfolio CSV", "Use bundled example"],
                      horizontal=True)
    st.caption("CSV requires only ticker,weight columns. Use decimal weights such as 0.35; "
               "weights must be finite, nonnegative and sum to 1 within 1e-8.")
    if choice == "Upload portfolio CSV":
        uploaded = st.file_uploader("Portfolio CSV", type=["csv"])
        if uploaded is None:
            st.info("Upload a portfolio CSV or explicitly select the bundled example to begin.")
            st.stop()
        source = io.BytesIO(uploaded.getvalue())
    else:
        source = "data/portfolio.csv"
        st.info("Bundled example: demonstration allocation, not an investment recommendation.")
    try:
        weights = load_portfolio(source)
    except DataError as exc:
        st.error(f"Invalid portfolio CSV: {exc}")
        st.stop()
    st.subheader("Validated portfolio")
    st.table(weights.to_frame().rename(columns={"weight": "Capital weight (decimal)"}))
    st.write(f"Decimal weight sum: {math.fsum(weights):.10f} "
             f"({math.fsum(weights) * 100:.6f}%). No normalization applied.")
    start, end = settings["download_start"], settings["download_end_exclusive"]
    st.caption(f"Daily adjusted prices requested for {', '.join(weights.index)}: "
               f"{start} through exclusive {end}.")
    assume_usd = st.checkbox(
        "I confirm USD quotes for any holding whose provider currency metadata is unavailable",
        value=False,
        help="Records a warning and user-confirmed provenance for unknown currencies. "
             "Known non-USD quotes are always rejected.")
    if st.button("Download prices / Refresh data", type="primary"):
        try:
            with st.spinner("Downloading adjusted prices and checking quote currencies…"):
                downloaded = download_prices(list(weights.index), start, end, assume_usd=assume_usd)
                save_cache(downloaded)
            st.success("Prices downloaded and cache saved. Results use the validated cache.")
        except (DataError, OSError) as exc:
            st.error(f"Download/refresh failed: {exc}")
            st.info("Retry the explicit action. A matching prior cache, if valid, is shown below.")
    try:
        data = load_cache(list(weights.index), start, end)
    except CacheError as exc:
        st.warning(str(exc))
        st.info("Use Download prices / Refresh data for this portfolio. "
                "Changing weights alone or reordering tickers can reuse a matching cache.")
        st.stop()
    st.caption("Using matching local cache; integrity, request and currency provenance validated. "
               "No network call on ordinary reruns.")
    show_provenance(data, settings)
    try:
        metrics = calculate_metrics(data.prices, weights, **{
            key: settings[key] for key in
            ("lookback_returns", "min_observations", "rolling_window", "trading_days")})
        attribution = calculate_attribution(metrics.covariance, weights,
                                            trading_days=settings["trading_days"])
    except DataError as exc:
        st.error(f"Calculations unavailable: {exc}")
        st.write("Missing observed prices by ticker:", data.provenance["missing_values"])
        st.stop()
    d = metrics.sample.diagnostics
    st.subheader("Common estimation sample")
    st.write(f"{d['selected_return_rows']} common daily returns: {d['sample_first_date']} "
             f"through {d['sample_last_date']}. Latest up to {settings['lookback_returns']} "
             f"complete returns; minimum {settings['min_observations']}.")
    st.write(f"Full downloaded history: {d['candidate_return_rows']} candidate return dates, "
             f"{d['complete_return_rows']} complete, {d['excluded_return_rows']} excluded. "
             f"{d['complete_rows_outside_lookback']} complete returns precede the selected sample. "
             "The first price date has no prior price and is not a return observation.")
    st.table(pd.DataFrame({
        "Missing prices (full history)": d["missing_prices_by_ticker"],
        "Unavailable returns (full history)": d["unavailable_returns_by_ticker"],
    }).rename_axis("ticker"))
    st.caption(f"Sample covariance and standard deviations use ddof=1. Annualization uses "
               f"sqrt({settings['trading_days']}). All static metrics use the same complete sample. "
               "Returns remain decimal internally; no filling or interpolation.")
    for warning in dict.fromkeys((*metrics.warnings, *attribution.diagnostics)):
        st.warning(warning)
    for reason in (attribution.attribution_unavailable_reason,
                   attribution.diversification_unavailable_reason):
        if reason:
            st.warning(reason)
    left, right = st.columns(2)
    left.metric("Annualized portfolio volatility", f"{metrics.portfolio_volatility.annualized:.4%}")
    benefit = attribution.diversification_benefit
    right.metric("Diversification benefit", f"{benefit:.4%}" if math.isfinite(benefit) else "Unavailable")
    st.caption("Diversification benefit: percentage volatility reduction relative to weighted "
               "standalone volatility. It is not expected-return improvement or a loss probability.")
    st.subheader("Asset volatility and risk attribution")
    st.table(display_table(attribution).style.format("{:.4f}", na_rep="Unavailable"))
    st.caption("Marginal risk is unconstrained sensitivity per 1.0 extra weight. Component risk "
               "is measured in annualized volatility percentage points (pp); risk share is a "
               "percentage of total volatility. A 2.5 pp component and a 25% risk share differ. "
               "Negative contributions are preserved; unavailable values are not zero.")
    st.subheader("Daily covariance matrix (decimal return squared)")
    st.table(metrics.covariance.style.format("{:.8g}", na_rep="Unavailable"))
    st.subheader("Correlation matrix (dimensionless)")
    st.table(metrics.correlation.style.format("{:.4f}", na_rep="Unavailable"))
    st.caption("Undefined correlation cells appear unavailable in the table and blank in the heatmap.")
    for figure in build_figures(weights, metrics, attribution, settings["rolling_window"]):
        st.plotly_chart(figure, config={"modeBarButtonsToRemove": ["toImage"]})
    rolling = metrics.rolling_volatility
    st.caption(f"Rolling span: {rolling.index[0].date()} through {rolling.index[-1].date()}; "
               f"{rolling.notna().sum()} available windows. The first "
               f"{settings['rolling_window'] - 1} rows and windows containing excluded returns "
               "are unavailable and are plotted as gaps without joining them.")


if __name__ == "__main__":
    main()
