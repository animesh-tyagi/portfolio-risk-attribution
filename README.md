# Portfolio Risk Attribution Engine

Completed 12-feature MVP: portfolio CSV → adjusted-price download/cache → daily
returns and volatility attribution → four Streamlit plots. This demonstrates
historical portfolio market volatility, not counterparty credit, PFE, margin or
regulatory capital.

## Install and run

From the repository root, Windows PowerShell (Python 3.11+):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,data]"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Use an existing working venv rather than recreating it. No activation is needed.
Linux/macOS equivalent (not executed in M5):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,data]"
python -m pip check
python -m pytest -q
python -m streamlit run app.py
```

Internet is required for installation and explicit downloads. Tests/calculations
and matching-cache reruns are offline. Stop Streamlit with Ctrl+C.
Upload a UTF-8 portfolio CSV or select **Use bundled example**, then click
**Download prices / Refresh data** for an absent/mismatched cache or provider
revisions. Ordinary reruns validate/reuse the cache without provider calls.

```csv
ticker,weight
SPY,0.35
TLT,0.25
LQD,0.15
GLD,0.15
FXE,0.10
```

Only `ticker,weight` columns are accepted. Decimal weights must be finite,
nonnegative and sum to one within 1e-8; never normalized. Labels are trimmed and
uppercased; duplicates rejected. Any nonempty valid portfolio of supported USD
instruments is accepted, including `SPY,1`. The five-asset example is a demo input.
Changing allocation means uploading another CSV. Optional CLI commands:

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --portfolio data/portfolio.csv
.\.venv\Scripts\python.exe scripts/download_data.py --load-cache
.\.venv\Scripts\python.exe scripts/check_starter.py
```

CLI also accepts `--settings` and `--cache-dir`; relative paths resolve from the
repository root. Its output verifies prices, not risk metrics. The starter checker
checks scaffold/configuration/syntax only; pytest checks financial correctness.

## Assumptions and contracts

- `data.py` isolates yfinance: explicit daily `auto_adjust=True` adjusted Close,
  start 2022-01-01, exclusive end 2026-01-01. Adjustments account for splits and
  distributions. Yahoo via yfinance is a third-party source, not an exchange feed.
  Quotes must be USD. Known non-USD is rejected; unknown metadata requires the
  explicit USD checkbox or CLI `--assume-usd`, with recorded basis/warning. No FX
  conversion. A USD quote does not imply only USD economic exposure.
- Ignored `data/processed/prices.csv` and `manifest.json` retain source, UTC
  retrieval time, Python/provider versions, dates, currency, adjustment, missing
  counts and SHA-256 integrity. Changed ticker sets/dates or corrupt metadata/data
  require refresh; reordered tickers/changed weights reuse the cache. Failed
  downloads preserve it. Staged writes roll back ordinary errors; hash validation
  detects interruption between replacements, rather than an atomic two-file write.
- Decimal simple returns are `P[t]/P[t-1]-1` on sorted union dates **before**
  common-sample selection. No filling, interpolation or zero substitution. An
  interior missing price invalidates two adjacent returns. Static metrics use
  the latest 756 complete common returns, requiring at least 252 in the dashboard.
  A zero-weight holding still participates in common-sample validation.
- Sample std/covariance use ddof=1; daily covariance has decimal return squared
  units, correlation is dimensionless. Volatility and marginal/component risk
  annualize by sqrt(252). Align weights and both matrix axes by ticker. Portfolio
  volatility reconciles with the std of the same weighted daily returns.
- Fixed retrospective weights imply hypothetical daily rebalancing without costs
  or taxes. Annualization is a convention, not a forecast. Days absent from every
  series cannot be detected without an exchange calendar. ETFs are instrument
  proxies, not isolated factors or a realized trading track record.
- Daily `MRC = S @ w / sigma`, `CRC = w * MRC`, `share = CRC / sigma`.
  Components sum to volatility, shares to 100% before rounding. Components use
  volatility percentage points (pp); shares use percentages of total volatility.
  Negative components remain signed; singular covariance is valid. Attribution
  is unavailable with a reason when daily volatility <=1e-12. Tiny negative daily
  variance of magnitude <=1e-14 may be clamped only with a diagnostic.
- Diversification benefit is `1 - sigma / sum(w * asset_std)` at a common horizon;
  unavailable when denominator <=1e-12. It measures volatility reduction, not
  expected-return improvement or loss probability. Constant-asset correlations
  are unavailable, including diagonals; zero-risk cases are explicit.
- Exactly four plots: capital allocation, correlation heatmap, signed annualized
  component risk and annualized 60-row rolling portfolio volatility. Rolling uses
  consecutive union return rows, ddof=1; initial 59 rows and windows spanning gaps
  are unavailable, with lines that do not connect gaps.

The app displays provenance, actual dates/counts, missing-data diagnostics and
units. See [METHODOLOGY.md](docs/METHODOLOGY.md),
[DATA_CONTRACT.md](docs/DATA_CONTRACT.md) and [PROJECT_SPEC.md](PROJECT_SPEC.md).
Market-data caches, environments and private role notes remain excluded from Git.

## Measured finding

Verified on 2026-10-05 IST, manifest UTC 2026-10-04T19:37:23.842145+00:00:
1,003 adjusted-price dates from 2022-01-03 through 2025-12-31, all five quotes
source-verified USD and no missing prices. Latest 756 common returns span
2022-12-27 through 2025-12-31.

**SPY's 35% capital allocation contributed 43.4639% of portfolio volatility.**
Annualized portfolio volatility was **8.8704%**, diversification benefit **34.3627%**.
SPY annualized MRC was 0.1101551454; times 0.35 gives CRC 0.0385543009, displayed
as **3.8554 volatility pp**. Dividing CRC by total volatility gives the share.
Component sum was 0.08870411863114672 versus volatility 0.08870411863114673;
share sum was 0.9999999999999999. Rolling had 697 available windows and 59 initial
unavailable rows. Provider revisions may change these historical findings.

## Verification and working versions

M5 reviewed all 12 features against both contracts. **147 offline tests passed**
in the existing environment (7.32s) and fresh environment (7.39s). Tests cover
independent known answers, label alignment, one asset, singular/zero risk, negative
components, missing-price adjacency/rolling recovery, malformed inputs, cache
integrity, failed refresh/write rollback and dashboard behavior. M5 fixed invalid
or missing title validation and added six targeted cases.

Fresh Windows editable installation, `pip check`, scaffold check and local
Streamlit launch passed. Separate real-provider AppTest flows supplied CSV bytes
at the upload boundary, clicked the actual refresh button, verified two metrics
and four serialized plots, and reran with downloads forbidden. Both example and
SPY-only passed; one-asset volatility was 15.3576%, share 100%, benefit 0%.
The live browser's example tables and all four plots were visually inspected.
Native browser file-picker interaction was not exercised: AppTest substitutes
upload bytes because it exposes no file-upload action. Missing-data tests use
synthetic fixtures; real data had no gaps. No outstanding setup/provider/code
blocker remains. [PLAN.md](PLAN.md) records the detailed evidence and boundaries.

| Dependency | Fresh Windows environment |
|---|---|
| Python | 3.11.4 |
| NumPy | 2.4.6 |
| pandas | 3.0.6 |
| Streamlit | 1.65.0 |
| Plotly | 6.9.0 |
| pytest | 9.1.1 |
| yfinance | 1.7.0 |
| pip | 23.1.2 |
| setuptools (runtime) | 65.5.0 |

Observed versions are not a lockfile. pip's isolated build dependencies satisfied
setuptools>=68 separately from runtime setuptools. Other combinations are unverified.

## 90-second demo

1. Launch the app, choose the example or upload CSV, show weights total one,
   then refresh. Point to source, quote verification, dates and the 756-return sample.
2. Compare allocation and component bars. SPY has 35% capital, 3.8554 volatility
   pp and 43.4639% risk share: covariance with the whole portfolio matters.
3. Show correlation and rolling plots, 8.8704% total annualized volatility and
   34.3627% diversification benefit relative to weighted standalone volatility.
   Explain the 59 initial unavailable rolling observations.
4. Rerun to demonstrate cache reuse. State fixed weights, historical ETF proxies,
   missing-data exclusions and annualization limits.

## Interview explanation tied to the code

`load_portfolio` in `data.py` validates CSV weights; `download_prices` is the
provider adapter and `load_cache` checks hash/request/provenance. `daily_returns`
and `prepare_returns` in `metrics.py` preserve adjacency and select the common
sample. `calculate_metrics` reconciles covariance volatility with std of weighted
returns. `calculate_attribution` in `attribution.py` applies Euler contributions
and checks sums. `app.py` converts decimals to display units and builds the plots.

Question: **Why does SPY's 35% weight give 43.46% risk share, and does MRC predict
a funded move from TLT to SPY?** Contribution depends on covariance with the
weighted portfolio: weight times marginal sensitivity gives the component;
dividing by total volatility gives share. MRC is unconstrained sensitivity per
extra unit of weight. A fully invested transfer of delta has first-order change
`delta * (MRC_SPY - MRC_TLT)` at the same horizon. A negative component can reduce
volatility locally but does not guarantee a hedge.

## CV bullets — completed work only

- Built a CSV-driven Python portfolio volatility engine with adjusted-price
  acquisition, validated caching, covariance/correlation, Euler risk attribution
  and diversification analysis; verified numerical/input contracts with 147
  offline pytest cases.
- Developed a Streamlit dashboard with four Plotly visualizations and transparent
  data provenance; demonstrated on 756 historical common returns that a 35% SPY
  capital allocation contributed 43.46% of portfolio volatility.
