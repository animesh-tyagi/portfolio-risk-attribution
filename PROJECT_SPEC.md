# Portfolio Risk Attribution Engine

## Purpose
Explain how a portfolio's capital allocation differs from its allocation of
volatility risk, and how correlation affects the diversification benefit.
This revision supersedes the earlier broader scope. Implement only the following
user-selected features; validation, caching and tests support these features.

## MVP Features

1. Load a portfolio from CSV
2. Download historical market prices
3. Calculate daily returns
4. Calculate annualized asset volatility
5. Calculate covariance and correlation matrices
6. Calculate total portfolio volatility
7. Calculate marginal contribution to risk
8. Calculate component contribution to risk
9. Calculate percentage contribution to total portfolio risk
10. Calculate diversification benefit
11. Visualize:
   - portfolio allocation
   - correlation matrix
   - risk contribution by asset
   - rolling portfolio volatility
12. Streamlit dashboard

## Defaults and assumptions
- Python, NumPy, pandas, Streamlit, Plotly; pytest; yfinance as the download adapter.
- CSV columns: ticker,weight. Weights are decimal capital allocations, nonnegative
  and sum to 1. No holdings/weights duplicated in JSON.
- Example data/portfolio.csv: SPY 35%, TLT 25%, LQD 15%, GLD 15%, FXE 10%.
  These are USD-listed equity, Treasury, corporate-bond, gold and euro proxies.
  This allocation is a demonstration input, not an investment recommendation.
- Loader and engine accept a nonempty valid portfolio of supported USD-quoted
  instruments; do not require five assets or these specific tickers.
- All input prices must share the declared USD quote currency. No automatic FX
  conversion. An ETF is a proxy, not a derivative or isolated economic risk factor.
- Fixed completed download sample: 2022-01-01 through 2025-12-31, with provider
  exclusive end 2026-01-01. Default estimation: latest 756 common daily returns.
- At least 252 usable daily returns for the dashboard; rolling window 60 rows;
  252 trading days for annualization. Show actual available dates and counts.
- Daily portfolio returns apply fixed weights retrospectively, equivalent to a
  hypothetical daily-rebalanced portfolio without transaction costs or taxes.

## Dashboard
One page is sufficient. Use a CSV upload with a clearly labeled bundled-example
option. Show the loaded weights and their sum. Require a valid portfolio before
calculation. To change the allocation, upload another CSV; no weight editor required.
An explicit Download prices / Refresh data action obtains data for the loaded
tickers and configured dates. Reuse a validated cache on subsequent reruns.

Display:
- Annualized total portfolio volatility and diversification benefit.
- A table of annualized asset volatility, marginal risk, component risk, and
  percentage contribution to total risk alongside each capital weight.
- Daily covariance matrix and correlation matrix, with clear units.
- Allocation bar chart; correlation heatmap; signed risk-contribution bar chart;
  annualized 60-day rolling portfolio-volatility line chart.
- Source, actual dates, sample size, missing-data diagnostics and assumptions.

Do not hide negative risk contributions or force them into a pie chart. A risk
share of 25% and a component of 2.5 volatility percentage points are different.

## Planned structure
| Path | Purpose |
|---|---|
| data/portfolio.csv | Example portfolio input |
| config/settings.json | Dates, currency and estimation settings only |
| src/portfolio_risk/data.py | Portfolio CSV, price acquisition/cache and validation |
| src/portfolio_risk/metrics.py | Returns, asset volatility, matrices, portfolio/rolling volatility |
| src/portfolio_risk/attribution.py | Marginal, component and percentage risk; diversification benefit |
| scripts/download_data.py | Explicit CLI wrapper around the shared downloader |
| app.py | Streamlit input flow, metric tables and four plots |
| tests/ | Offline known-answer and validation tests |

These modules are planned, not yet implemented. Keep the provider adapter isolated
within data.py so the rest of the pipeline remains offline and testable.

## Definition of done
- A fresh environment can install and launch the app using documented commands.
- Uploading a valid portfolio drives the requested tickers, aligned weights and results.
- Historical market data downloads and later loads from a matching local cache.
- All 12 features work. Component risk sums to portfolio volatility; risk shares
  sum to 100% when volatility is nonzero; zero-risk cases are explicit.
- Known-answer tests and input-validation tests pass offline.
- All four plots use actual calculated data and display the correct units.
- README documents setup, assumptions and one verified result the user can explain.

## Scope boundary
No stress testing, historical scenarios, VaR, Expected Shortfall, drawdown, HHI,
report/export pipeline, automated commentary, group/factor attribution, comparison
mode, optimizer, derivatives pricing, ML, LLM, SQL or deployment task. No stretch
features in the two-day plan. Time saved goes to correctness and understanding.

## Role relevance
The project demonstrates historical-data analysis, Python numerical reasoning,
portfolio-risk interpretation and visualization relevant to the target CEM role.
Its results concern market volatility, not counterparty exposure or margin.
