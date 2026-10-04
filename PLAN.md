# Two-day execution plan — focused MVP

Budget: approximately 12 focused hours, six per day. Times are estimates.
The goal is all 12 requested features, with no stretch features. Update this file
with verified progress so a new Codex session can continue without the old chat.

| Stage | Budget | Work | Exit condition |
|---|---:|---|---|
| M0 — setup | Day 1, 0.5 h | Environment, scope, scaffold check, Git checkpoint | Setup passes; CSV and settings understood |
| M1 — portfolio and prices | Day 1, 2 h | Portfolio CSV validation, explicit downloader, adjusted-price cache and provenance | Uploaded holdings determine tickers; real cache loads offline |
| M2 — metrics | Day 1, 2 h | Daily returns, annualized asset volatility, covariance/correlation, portfolio/rolling volatility | Known examples and missing-data rules pass |
| M3 — attribution | Day 1, 1.5 h | Marginal/component/percentage risk and diversification benefit | Components reconcile; negative/zero risk cases handled |
| M4 — dashboard | Day 2, 3 h | CSV input, explicit download/cache action, tables and all four visualizations | Full 12-feature flow works with real data |
| M5 — validate and explain | Day 2, 3 h | Correctness review, fresh setup, README, demo and code walkthrough | Reproducible run; all features verified; user can explain results |

## Status
- [x] Starter revised to the user's exact 12-feature MVP.
- [ ] M0 completed on the user's development machine.
- [x] M1 completed with CSV portfolio and real market-data cache (2026-10-04).
- [x] M2 completed with known-answer metric tests (2026-10-04).
- [ ] M3 completed with attribution invariants.
- [ ] M4 completed with all four required plots.
- [ ] M5 completed with end-to-end verification and explanation.

## Scope control
At the end of Day 1, validate the calculation engine before UI work. Keep the
app to one page, use basic readable charts and fixed config settings. Do not
spend time on styling frameworks, extra metrics, exports or deployment.
At hour 9, freeze additions and use remaining time to finish or fix the requested
features. Preserve all four plots; reduce polish, not the agreed feature list.

If a download fails, limit provider troubleshooting to about 30 minutes before
continuing the offline engine/tests using the labeled synthetic fixture. Record
the blocker and return to the downloader. Synthetic data does not satisfy the
real-data requirement; do not mark M1 or the whole project complete without it.

## Learning checkpoints
- After M1: explain portfolio CSV versus historical-price CSV and price adjustment.
- After M2: explain covariance, correlation, annualization and fixed-weight returns.
- After M3: explain capital weight versus risk share, Euler reconciliation and
  why some holdings can have negative contributions.
- After M4: trace one uploaded CSV through the pipeline to a displayed result.
- After M5: give a 90-second demonstration with one actual measured finding and
  explain the limits of using historical ETF returns for risk analysis.

## Current handoff
Completed: M1 CSV/settings loading, observed-price validation, explicit shared
yfinance adapter, CLI and validated local adjusted-price cache with provenance.
The real bundled-example cache downloaded and subsequently loaded offline.
M2 pure returns/volatility calculations now pass offline known-answer tests.
Attribution and dashboard remain unimplemented; app.py is unchanged.
Next: M3 in docs/CODEX_PROMPTS.md. M0's environment/scaffold checks have passed,
but its full setup/checkpoint milestone was not performed in this M1-only session.

## Milestone log — M1, 2026-10-04

- Stage/status: M1 complete; real prices acquired and matching cache verified offline.
- Files changed: added src/portfolio_risk/data.py, scripts/download_data.py and
  tests/test_data.py; updated README.md, tests/README.md and PLAN.md. Created
  ignored data/processed/prices.csv, manifest.json and provider cache under data/raw.
  No UI, metrics or attribution implementation was added.
- Environment: existing native Windows .venv; Python 3.11.4, NumPy 2.4.6,
  pandas 3.0.6, pytest 9.1.1, yfinance 1.7.0, Streamlit 1.65.0, Plotly 6.9.0.
  No packages installed or environments replaced. Initial sandbox launch could
  not create the base Python process; approved execution of the same venv worked.
- Commands and actual results (all Python commands used .venv/Scripts/python.exe):
  - `scripts/check_starter.py`: PASS; scaffold/configuration check only.
  - `-m pip check`: "No broken requirements found."
  - `scripts/download_data.py`: exit 0; retrieved 2026-10-04T09:32:36.017395+00:00
    from Yahoo Finance via yfinance; requested 2022-01-01 to exclusive 2026-01-01.
    Actual 1,003 union price dates, 2022-01-03 through 2025-12-31; zero missing
    prices for SPY, TLT, LQD, GLD and FXE. Every quote currency source-verified USD;
    no --assume-usd flag used. Actual provider columns were field/ticker MultiIndex.
  - `scripts/download_data.py --load-cache`: exit 0; same actual counts/dates,
    matching hash/provenance validated offline. Cache load imports no provider.
  - `-m pytest -q`: final **57 passed in 3.48s**. Offline M1 tests use the existing
    four-row synthetic fixture and mocked provider responses, including one asset,
    arbitrary portfolio size, malformed weights/prices, preserved gaps, currency
    uncertainty, unavailable symbols, stale/corrupt caches and failed-write rollback.
    Includes a CLI subprocess launched from another working directory.
  - `git diff --check`: passed. `git check-ignore` confirmed prices.csv,
    manifest.json and data/raw/yfinance are excluded. No commit, push or publish.
- Finance concept: weights describe fractions of portfolio capital and sum to one;
  historical price columns describe each instrument's price history and are joined
  to holdings by ticker. Changing weights alone reuses the same price cache.
  auto_adjust=True extracts adjusted Close, accounting for splits/distributions;
  inspected installed yfinance auto_adjust code confirms Adj Close becomes Close.
  A euro-exposure ETF such as FXE can still have a USD quote currency.
- Decisions: trim/uppercase ticker labels, preserve CSV row order, reject duplicate
  normalized labels; never normalize weights or fill/drop incomplete price rows.
  Unknown quote currency requires explicit CLI --assume-usd (or future UI
  confirmation) with recorded warning/basis; known non-USD is rejected regardless.
  Request/ticker/adjustment/currency/hash mismatches require explicit refresh.
  Weight changes and ticker reordering are compatible. No arbitrary time expiry
  for the fixed historical sample; retrieval timestamp is available for display,
  and provider revisions require explicit refresh. Stage both cache files and
  roll back ordinary write failures; interrupted two-file replacement is detected
  by hash validation, not claimed to be an atomic two-file transaction.
- Verification boundary: M1 verifies inputs and price acquisition/cache, not
  financial-engine correctness. Usable return counts, 252-return minimum and the
  latest-756-return sample remain M2/M4 responsibilities. No calculated risk
  findings or business impact have been measured. No remaining M1 blocker.
- Interview question: "Why can changing SPY's weight reuse cached prices, while
  replacing SPY with another ticker requires a refresh?" Answer: price histories
  belong to instruments, independently of allocation; weights combine their
  future calculated returns, while a different instrument requires its own
  validated price series and currency provenance.
- Next action: implement M2 daily returns on the sorted union date index without
  filling, then common-sample selection/diagnostics and the specified volatility,
  covariance/correlation and rolling-volatility functions with known-answer tests.

## Milestone log — M2, 2026-10-04

- Stage/status: M2 complete. Added src/portfolio_risk/metrics.py and
  tests/test_metrics.py; updated tests/README.md and PLAN.md. M1 code, existing
  cache, settings and app.py are preserved. No attribution or UI work added.
- API: calculate_metrics(prices, weights, ...) returns a structured MetricsResult;
  pass lookback_returns, min_observations, rolling_window and trading_days from
  loaded settings. Defaults are 756, 252, 60 and 252. Standalone functions support
  small offline examples; prepare_returns defaults to the mathematical minimum
  of two complete observations, while calculate_metrics defaults to the dashboard
  minimum of 252. No provider calls or cache writes in calculations.
- Decisions: validate/sort prices using M1, calculate simple returns on adjacent
  union price dates without filling, omit only the initial no-prior-price row,
  preserve subsequent excluded dates in ReturnSample.daily_returns/excluded_dates,
  and select the latest complete rows for every static metric. Extreme finite
  price ratios that overflow are unavailable and counted in return diagnostics.
  Diagnostics retain actual sample dates, row counts, missing prices and unavailable
  returns by ticker. Days absent from every series remain undetectable without
  an exchange calendar; the result includes this limitation.
- Units/conventions: decimal daily returns; ddof=1 covariance in daily decimal
  return squared; Pearson correlation dimensionless; asset/portfolio/rolling
  volatility annualized by sqrt(252). Align weights and both covariance axes by
  ticker, reject invalid weights without normalization, accept singular covariance,
  reject materially indefinite/nonfinite/asymmetric inputs. Only negative daily
  variance within 1e-14 is clamped, retaining a diagnostic. Constant-asset
  correlation cells (including diagonals) are NaN with an explicit reason.
- Rolling decision: output covers the selected estimation span through the last
  available union return date, retaining internal/trailing gaps. It does not borrow
  observations before the selected start. Use 60 consecutive union return rows;
  first 59 and any window containing an excluded return date are NaN. A zero-weight
  holding still participates in complete-sample selection. M4 must plot NaN gaps
  without joining them and display the returned warnings/provenance.
- Commands and actual results: `.venv/Scripts/python.exe -m pytest -q` initially
  could not launch the base Python process in the sandbox; approved execution of
  the same command succeeded: **99 passed in 3.80s** (57 M1, 42 new M2 cases).
  `git diff --check` passed for tracked changes. No packages installed, market-data
  download, commit, push or publication in this milestone.
- Financial verification: independent diagonal example gives daily variance
  0.000125 and volatility 0.0111803398875; one asset with daily std 0.02 gives
  annualized volatility 0.3174901573. The existing four-price synthetic fixture
  gives equal-weight portfolio returns (0.05, 0, 0), daily std 0.0288675134595 and
  annualized std sqrt(0.21). Tests reconcile covariance-based volatility with
  weighted-return sample std, check single-asset shapes, constants/zero risk,
  singular matrices, label alignment, missing-price adjacency, lookback/minimum
  counts, rolling known answers, gap invalidation and recovery. These are verified
  synthetic calculation results, not measured market-data findings. The previous
  scaffold checker is separate from this financial-engine verification; it was
  not rerun in M2. No end-to-end dashboard claim or remaining M2 blocker.
- Finance intuition: covariance combines how two returns move together with
  their sizes; correlation divides covariance by both asset standard deviations
  to give a dimensionless measure. For daily stds 0.02 and 0.01 and correlation
  0.5, covariance is 0.5 * 0.02 * 0.01 = 0.0001. With equal weights, daily
  portfolio variance is 0.00015, compared with the tested uncorrelated example's
  0.000125. Correlation alone does not determine portfolio volatility: individual
  asset volatility and capital weights also matter. Square-root annualization
  is a convention, and fixed weights describe hypothetical daily rebalancing.
- Interview question: "Why must sqrt(w.T @ S @ w) equal std(returns @ w, ddof=1)?"
  Answer: sample covariance expands the variance of the same weighted daily
  returns. Equality requires matching ticker labels, observations and ddof;
  calculate_metrics checks this reconciliation before returning results.
- Next action: M3 only, using this common daily covariance, aligned weights and
  portfolio volatility for marginal/component/percentage risk and the specified
  diversification benefit; preserve negative contributions and explicit zero-risk
  handling. M4/M5 remain pending.
