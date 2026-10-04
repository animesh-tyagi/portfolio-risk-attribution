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
- [ ] M2 completed with known-answer metric tests.
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
Financial functions and dashboard remain unimplemented; app.py is unchanged.
Next: M2 in docs/CODEX_PROMPTS.md. M0's environment/scaffold checks have passed,
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
