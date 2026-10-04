# Portfolio Risk Attribution Engine

**Status: M1–M4 implemented. Financial engine and single-page dashboard verified;
M5 fresh-environment setup and final review remain pending.**

A two-day Python project that loads a portfolio CSV, downloads historical prices,
calculates volatility and holding-level risk contributions, and visualizes the
results in Streamlit. Scope is the user's exact 12-feature MVP.

Start with [START_HERE.md](START_HERE.md). See [PROJECT_SPEC.md](PROJECT_SPEC.md)
for scope, [PLAN.md](PLAN.md) for milestones and
[docs/CODEX_PROMPTS.md](docs/CODEX_PROMPTS.md) for implementation prompts.

M1 uses the project venv. Run from the repository in PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --portfolio data/portfolio.csv
.\.venv\Scripts\python.exe scripts/download_data.py --load-cache
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_starter.py
```

The first command explicitly downloads/refreshes data; the second only validates
and reads the cache offline. The CLI resolves relative portfolio, settings and cache
paths from the repository root, even when launched from another directory. Use
`--settings` and `--cache-dir` to select other files/directories. Each portfolio CSV
has exactly `ticker,weight` columns: decimal, finite, nonnegative weights totaling
one within 1e-8. Tickers are trimmed and uppercased; duplicates are rejected.
There is no fixed number of assets and weights are never silently normalized.

The CSV allocates capital (e.g. 0.35 means 35%); it supplies neither prices nor
share quantities. `data/processed/prices.csv` instead contains historical adjusted
closing prices by date and ticker. Prices need not sum to anything, and holdings
are aligned by ticker rather than column position. The shared adapter uses
`yfinance.download(interval="1d", auto_adjust=True)` and extracts `Close`, handling
both single-ticker and MultiIndex responses. In installed yfinance 1.7.0,
`auto_adjust` renames the provider's `Adj Close` to `Close`: the adjustment accounts
for splits and distributions so these events do not create artificial raw-price
changes. Future calculations use decimal simple returns on this adjusted series;
it is not an executable historical quote or a realized trading record. The end
date is exclusive. See the [yfinance download documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html).

All quotes must be USD. Known non-USD instruments are rejected. Unknown currency
metadata stops the download unless the user explicitly passes `--assume-usd`;
that confirmation and its warning are saved in provenance. This flag never
overrides a known non-USD quote. An instrument such as FXE can have euro economic
exposure while its ETF shares are quoted in USD.

The ignored local cache includes `prices.csv` and `manifest.json`: source, UTC
retrieval time, Python/yfinance versions, requested/actual dates, adjustment,
currency verification per ticker, row count, missing counts and SHA-256 hash.
Missing values stay missing. Invalid observed prices, duplicate dates and symbols
with no observed history are rejected. A changed ticker set, date request or
inconsistent metadata/hash invalidates the cache and requires an explicit refresh.
Weight changes and ticker reordering reuse it. A fixed completed historical sample
has no automatic age expiry; retrieval time is retained, and provider revisions
require an explicit refresh. Failed downloads leave the prior cache unchanged.
File replacements are staged and rolled back on ordinary write errors; a process
interruption between the two replacements is detected by the hash on the next load.

Verified on 2026-10-04: the bundled example downloaded **1,003 price dates** from
2022-01-03 through 2025-12-31, with zero missing prices and source-verified USD
currency for every holding. The actual yfinance response used field/ticker
MultiIndex columns. Prices are real Yahoo data via a third-party wrapper, not an
official exchange feed; the cache remains excluded from Git.

Launch the dashboard from the project environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Upload a portfolio CSV or explicitly select **Use bundled example**. The app shows
validated weights and their sum. Click **Download prices / Refresh data** for a
missing/mismatched cache or to obtain provider revisions. Ordinary reruns reuse a
matching cache without network calls. Unknown quote currency needs the explicit
USD confirmation checkbox; known non-USD quotes are rejected. Invalid CSVs and
stale/corrupt caches show reasons and stop calculations. Failed refreshes can
continue displaying a validated matching prior cache, with an error message.

The dashboard calls the tested engine for returns, covariance, volatility and
attribution. Static calculations use the latest 756 complete daily returns,
requiring at least 252, sample ddof=1 and sqrt(252) annualization. Missing prices
are never filled; returns require adjacent prices before common-sample selection.
Fixed weights imply hypothetical daily rebalancing without costs or taxes.
Annualization is a convention, not a future-risk guarantee. A day absent from
every series cannot be detected without an exchange calendar.

Exactly four plots show allocation, correlation, signed annualized component risk
and annualized 60-day rolling portfolio volatility. Component risk uses volatility
percentage points, while risk shares use percentages of total volatility. Negative
components remain signed. Undefined values show unavailable with reasons; rolling
windows require 60 consecutive union return rows and preserve gaps. No exports or
reports are provided.

Verified real dashboard sample on 2026-10-04: **756 common returns from 2022-12-27
through 2025-12-31**, annualized portfolio volatility **8.8704%**, diversification
benefit **34.3627%**. For CSV row `SPY,0.35`, SPY identifies the adjusted-price
column and 0.35 supplies the capital weight. The engine uses its covariance with
the whole weighted portfolio to obtain annualized marginal risk 0.1101552151.
Multiplying by 0.35 gives component 0.0385543253, displayed as **3.8554 volatility
percentage points**. Dividing by portfolio volatility gives **43.4640% of total
risk**, distinct from its 35% capital weight. Components reconcile to total
volatility and shares to 100% before rounding. This measured finding may change
with provider revisions; it demonstrates historical volatility attribution.

M4 verification used the real refresh button in Streamlit AppTest and subsequent
cache reruns with provider calls forbidden, including a reordered CSV supplied at
the upload boundary. Browser rendering was checked separately. **141 offline tests
passed**, including numerical known answers and dashboard error/edge cases. The
starter checker verifies scaffold/configuration only. See PLAN.md for the actual
commands, verification boundaries and next milestone.
