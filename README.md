# Portfolio Risk Attribution Engine

**Status: M1 portfolio input and real adjusted-price cache implemented and verified;
financial analytics and the dashboard remain unimplemented.**

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

M1 tests are offline input/adapter/cache checks using the labeled synthetic
fixture and mocked provider responses. The scaffold checker is a separate setup
check. Neither verifies returns, covariance, volatility attribution or the
252-usable-return minimum; those belong to subsequent milestones. The app remains
the original placeholder.
