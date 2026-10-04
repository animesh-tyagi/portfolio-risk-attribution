# Start here — completed 12-feature MVP

M1–M5 are complete: CSV loading, explicit price download/cache, financial engine
and four-plot Streamlit dashboard. [README.md](README.md) has assumptions, working
versions, measured findings, demo/interview explanation and CV bullets.
[PLAN.md](PLAN.md) records verification evidence and its limits.

## Setup and launch

Use Python 3.11+ and keep the checkout and venv on the same platform; do not share
a Windows venv with WSL. From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,data]"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_starter.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Use an existing working venv rather than recreating it. Linux/macOS can create
with `python3 -m venv .venv`, activate with `source .venv/bin/activate` and use
the equivalent Python commands in README. Windows fresh setup was tested;
Linux/macOS was not. Internet is needed for install and explicit downloads.
Stop Streamlit with Ctrl+C. No backend, database, API key or deployment needed.

Upload UTF-8 `ticker,weight` CSV with decimal nonnegative weights totaling one,
or explicitly select the example. Click **Download prices / Refresh data** for
missing/mismatched data; matching-cache reruns are offline. One asset is supported.
Known non-USD is rejected; unknown metadata requires explicit USD confirmation.
No filling of prices or normalization of weights.

Optional CLI download and offline validation:

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --portfolio data/portfolio.csv
.\.venv\Scripts\python.exe scripts/download_data.py --load-cache
```

## Verified state

On 2026-10-05 IST: fresh installation, dependency/scaffold checks, 147 offline
tests, local launch, real CSV-to-refresh-to-dashboard AppTest flows (five assets
and one asset), offline reruns and live-browser inspection of all four plots
passed. CSV bytes were supplied at AppTest's upload boundary; native browser
file-picker interaction was not tested. Missing-data verification uses synthetic
fixtures; the real sample has no gaps. No outstanding blocker.

The starter checker is scaffold-only; pytest verifies financial/data/dashboard
behavior. Recorded working versions are not a lockfile. Environments, market-data
caches and private role notes stay ignored. No commit, push or publication in M5.

## Project map

| Path | Responsibility |
|---|---|
| PROJECT_SPEC.md | Exact 12 features |
| docs/METHODOLOGY.md, docs/DATA_CONTRACT.md | Calculation/data contracts |
| data/portfolio.csv | Example capital allocation |
| config/settings.json | Dates, USD and estimation defaults |
| src/portfolio_risk/data.py | CSV/settings, provider and cache |
| src/portfolio_risk/metrics.py | Returns, matrices, static/rolling volatility |
| src/portfolio_risk/attribution.py | Marginal/component/share and benefit |
| app.py | Single-page dashboard |
| tests/ | Offline known-answer, validation and dashboard tests |

Read AGENTS.md and contracts before maintenance. Preserve the 12-feature scope.
Next action: rehearse the README demo and interview explanation; no further
milestone implementation is pending.
