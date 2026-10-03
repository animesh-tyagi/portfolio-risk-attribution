# Data contracts and module boundaries

## 1. Portfolio input: data/portfolio.csv or a user upload
UTF-8 CSV with exactly these required columns:

```csv
ticker,weight
SPY,0.35
TLT,0.25
LQD,0.15
GLD,0.15
FXE,0.10
```

Each row is an instrument's capital weight. Accept any nonempty valid portfolio
of provider-supported USD-quoted instruments, not just the sample tickers.
Trim whitespace around headers/tickers; reject missing names or duplicate tickers
after trimming. Weights must be numeric, finite, >=0 and sum to 1 within 1e-8.
Reject percentage strings such as "35%" and weights totaling 100: explain the
expected decimal format. Do not merge duplicates or silently normalize weights.
Reject extra columns in the MVP to keep the contract unambiguous. Preserve row
order for display; align by ticker for calculations. A single asset is supported.
The CSV uses weights, not quantities, prices, dollar notionals or client exposures.

This is different from the price CSV below. Portfolio uploads must not be mistaken
for price uploads. There is no independent historical-price upload UI in this MVP.

## 2. Settings: config/settings.json
Contains title, base currency, annualization days, download dates, estimation
lookback, rolling window and minimum observations. It contains no weights,
portfolio value, tail-risk confidence level or scenarios.
Paths used by the CLI/dashboard are resolved from the repository root, not from
an unpredictable working directory. Default portfolio is data/portfolio.csv.

## 3. Historical price acquisition
Implement a shared downloader adapter in data.py and a small explicit CLI wrapper
scripts/download_data.py. The Streamlit download button calls that same adapter.
Never fetch data at module import or on every app rerun.

Use yfinance.download with explicit ticker list, start, exclusive end,
interval="1d" and auto_adjust=True. Extract adjusted Close; handle both one-ticker
and MultiIndex results deliberately. Do not assume an Adj Close column exists.
See the [provider wrapper documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)
when implementing. Record the installed version and actual provider behavior.

yfinance is a third-party wrapper for Yahoo data, not an official exchange feed.
Preserve source and adjustment metadata; keep market-data caches out of public
Git by default. Do not assume redistribution rights for downloaded prices.

Input contract: USD-quoted instruments only. Validate quote currency using source
metadata when available. If unknown, require an explicit USD-currency confirmation
in the app with a warning; for a CLI download use an explicit --assume-usd flag.
Record whether currency was source-verified or user-confirmed. Reject known non-USD
quotes; do not silently combine currencies or add FX conversion to this MVP.

## 4. Local cache
Canonical data/processed/prices.csv: date plus one adjusted-close column for each
requested ticker. Rows sorted ascending; unique YYYY-MM-DD dates; no extra index.
Requested tickers must all be present. Diagnose missing prices, reject nonpositive
or infinite observed values, and compute returns as in METHODOLOGY.md.

Create data/processed/manifest.json with actual values:
- provider/source, UTC retrieval timestamp and Python/provider-library versions;
- requested ticker set, quote currency and verification/confirmation basis;
- requested start and exclusive end, actual first/last date and adjustment convention;
- row count, missing values per ticker and SHA-256 hash of prices.csv.

For MVP use one cache, not a database. Validate hash, ticker set, date request and
adjustment/currency metadata on load. A changed ticker set or date request requires
an explicit refresh; changed weights alone reuse the cache. Label mismatches and
never quietly calculate with a previous portfolio's data. Reordering tickers alone
does not invalidate the cache. Failed downloads must not overwrite a working cache.

At least 252 aligned daily returns are needed for app metrics. Use latest 756 if
available; show actual counts/dates and exclusions. Handle insufficient history
with a clear error. Synthetic fixtures are for tests, not the real-data demo.

## 5. Planned modules
| File | Responsibility |
|---|---|
| src/portfolio_risk/data.py | Portfolio CSV/config; isolated provider adapter; price cache; validation/alignment |
| src/portfolio_risk/metrics.py | Daily returns, annualized asset volatility, daily covariance/correlation, portfolio/rolling volatility |
| src/portfolio_risk/attribution.py | Marginal/component/percentage volatility contribution; diversification benefit |
| scripts/download_data.py | CLI wrapper, e.g. --portfolio data/portfolio.csv --settings config/settings.json |
| app.py | CSV upload/example selection, explicit download/load flow, tables and four plots |
| tests/test_*.py | Offline calculation and input-contract verification |

Suggested in-memory result: settings/provenance, weights, returns, asset volatility,
covariance, correlation, portfolio volatility, attribution table, diversification
benefit, rolling volatility and warnings. A dictionary or small dataclass is enough.
Do not add serialized report outputs or a reporting module.
