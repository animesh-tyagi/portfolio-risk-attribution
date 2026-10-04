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
- [x] M3 completed with attribution invariants (2026-10-04).
- [x] M4 completed with all four required plots (2026-10-04).
- [x] M5 completed with end-to-end verification and explanation (2026-10-05 IST).

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
M2 pure returns/volatility calculations and M3 attribution pass offline
known-answer tests. M4 single-page dashboard now consumes the engine, with CSV
input, explicit refresh, validated cache reuse, metrics/matrices and four plots.
Real-data refresh and offline reruns were verified in Streamlit AppTest.
M5 is now complete: fresh setup, contract review, offline and real-provider flows,
browser plot checks and README demonstration/explanation. Next: rehearse the demo.
M0's setup checks have passed, including fresh setup in M5; its original Git
checkpoint was not performed here, so that historical milestone remains unchecked.

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

## Milestone log — M3, 2026-10-04

- Stage/status: M3 complete. Added src/portfolio_risk/attribution.py and
  tests/test_attribution.py; updated tests/README.md and PLAN.md. Existing M1/M2
  code, app.py, settings and market-data cache are preserved. No UI, factor/group
  attribution or optimizer added. No commit, push or publication.
- API: calculate_attribution(daily_covariance, weights, trading_days=252) returns
  AttributionResult with a ticker-indexed table in portfolio row order, portfolio
  volatility, weighted standalone daily volatility, fractional diversification
  benefit, explicit unavailable reasons and diagnostics. Reuses M2 covariance,
  weight and annualization validation. Both covariance axes and weights align by
  ticker before arithmetic. M4 can pass MetricsResult.covariance and loaded weights
  directly; pass the same configured trading_days to both milestones.
- Units: table columns distinguish daily/annualized asset volatility, marginal
  contribution and component contribution; risk_share is a fraction. Presentation
  multiplies shares and diversification benefit by 100. A decimal annualized
  component of 0.025 is 2.5 volatility percentage points, not a 2.5% risk share.
  No rounded values or percentages are used in calculation.
- Decisions: preserve negative marginal/components and shares; zero weights have
  zero component/share when portfolio volatility is defined, but their marginal
  sensitivity can be nonzero. No inverse is required for singular covariance.
  All attribution columns remain NaN with a reason at daily volatility <=1e-12.
  Benefit uses 1 - sigma_p / B with B=sum(w_i*sqrt(S_ii)), at the daily horizon;
  unavailable when B<=1e-12. Exact hedge with positive B has benefit 1 even though
  attribution is undefined. A positive negligible sigma_p is used as calculated
  in the benefit if B exceeds its threshold, rather than rounded to zero.
  M2's tiny-negative-variance clamp diagnostic is retained. If a rounding-scale
  negative covariance diagonal passes M2 PSD tolerance, its standalone volatility
  and benefit are unavailable with a reason; no diagonal is silently clipped.
- Commands and actual results: `.venv/Scripts/python.exe -m pytest -q` could not
  launch the base Python process inside the sandbox. Approved execution of that
  same command passed: **131 passed in 4.78s** (99 existing, 32 new M3 cases).
  Tests are offline; no market provider calls or real cache changes. New cases
  cover independent known answers, daily/annualized component sums, share and
  displayed-percentage sums, single assets, negative contributions, zero weights,
  zero/negligible portfolio volatility, threshold equality, singular covariance,
  independently reordered axes/weights and reordered price columns through M2,
  invalid weights/covariance/labels, and annualization settings.
- Financial verification: documented diagonal S=(0.0004,0.0001), w=(0.5,0.5)
  gives daily volatility 0.0111803398875, MRC=(0.01788854382,0.004472135955),
  CRC=(0.00894427191,0.0022360679775), shares=(0.8,0.2), B=0.015 and benefit
  0.2546440075 (25.4644%). The signed example gives CRC approximately
  (-0.00141421356237,0.00707106781187) and shares=(-0.25,1.25), preserving the
  sum identities. These are verified synthetic examples, not measured market
  findings or business impact. Scaffold checking was not rerun; this milestone
  verifies the financial attribution engine, not the end-to-end dashboard.
- Finance intuition: in the diagonal two-asset example, A's daily standalone
  volatility is 2% versus B's 1%. Equal capital weights produce variance terms
  0.5^2*0.02^2=0.0001 and 0.5^2*0.01^2=0.000025. With zero covariance, A supplies
  four times B's variance term, so Euler volatility shares are 4/(4+1)=80% and
  20%. Annualization scales both components equally and leaves these shares
  unchanged. Capital allocation alone does not capture volatility or covariance.
  A negative component means the holding reduces total volatility locally in
  that allocation; it is not a negative capital weight or a guaranteed hedge.
- Interview question: "Does MRC[A] predict the change when moving capital from
  B to A?" Answer: MRC[A] is the unconstrained sensitivity. A fully invested move
  changes both weights; the first-order daily volatility change for a small
  decimal weight transfer delta is delta*(MRC[A]-MRC[B]). In this example the
  difference is approximately 0.013416407865 per unit of transferred weight.
- Next action: M4 dashboard only when requested, consuming M2/M3 structured
  results and displaying units, unavailable reasons, diagnostics and provenance;
  add the four specified plots with signed components and rolling gaps. M4/M5
  remain pending. No remaining M3 blocker.

## Milestone log — M4, 2026-10-04

- Stage/status: M4 complete. Replaced app.py's placeholder with the single-page
  Streamlit dashboard; added tests/test_dashboard.py, updated README.md,
  tests/README.md and this plan. No engine formulas copied into the UI; M1–M3
  financial modules unchanged. No exports, reports, additional metrics, commits,
  pushes, publication, subagents or worktrees.
- Input/data flow: upload is the default and requires a file; bundled example
  requires explicit selection. Existing loader validates decimal weights and
  ticker labels. Every ordinary rerun validates the on-disk cache; only the
  Download prices / Refresh data button invokes the shared download adapter.
  Explicit optional USD confirmation applies only to unavailable currency metadata.
  Failed refreshes show errors and may display a validated matching prior cache.
  Changed tickers/requests or damaged cache stop calculations with refresh guidance.
- Presentation: two requested summary metrics, weight/asset-volatility/marginal/
  component/share table, daily covariance and dimensionless correlation tables;
  exactly allocation bars, correlation heatmap, signed annualized component bars,
  annualized 60-day rolling volatility. Percentages and volatility pp are distinct.
  Static tables have no export toolbar; Plotly image download control is removed.
  NaN attribution/correlation is visibly unavailable with engine reasons; rolling
  gaps remain gaps. Source, UTC retrieval, versions, adjustment, requested/actual
  dates, currency basis, common observation counts and missing data are displayed.
- Actual verification: `.venv/Scripts/python.exe -m pytest -q` passed **141 tests
  in 7.75s**, including 10 dashboard tests and all 131 existing financial/data
  tests. Dashboard tests cover explicit-action-only downloads, matching cache
  reruns, reordered/changed weights, mismatched ticker sets, invalid CSVs, corrupted
  cache, failed refresh retaining valid data, currency-confirmation forwarding,
  insufficient history, zero risk, signed chart values/units and rolling gaps.
  These tests are offline with provider mocks and temporary synthetic caches.
  The sandbox could not launch base Python; approved venv execution was used.
- Real-data verification: ignored local data/raw/verify_m4.py used Streamlit
  AppTest to select the bundled example, click its actual refresh button through
  the shared Yahoo/yfinance adapter, verify two metrics and four charts, then
  rerun and supply a reordered CSV with provider calls forbidden. No app errors
  or exceptions. Upload bytes were supplied at the file_uploader boundary because
  AppTest lacks a native file-upload interaction; browser rendering was inspected
  separately on a running local Streamlit server. A fresh-environment install and
  full M5 correctness review remain pending; this is not scaffold-only validation.
- Measured real sample: source Yahoo Finance via yfinance 1.7.0; retrieval
  final refresh 2026-10-04T10:37:15.020092+00:00; 1,003 adjusted-price dates, 2022-01-03 through
  2025-12-31, all five quotes source-verified USD. 1,002 complete returns, no missing
  prices or excluded return dates; latest 756 selected, 2022-12-27 through
  2025-12-31. Annualized portfolio volatility **8.870413%**, diversification benefit
  **34.362675%**. Components sum to 0.08870413226775613 versus portfolio volatility
  0.08870413226775611; shares sum to 1.0000000000000002. Rolling series has 756 rows,
  697 available windows and 59 initial unavailable rows. Prices/cache and manual
  verification script remain ignored. The final rerun after removing exports also
  passed both real refresh and forbidden-provider cache/upload checks. The prior
  refresh at 10:30:12 UTC gave 8.8704139718% volatility: small provider-data revisions
  appeared on the later refresh. `git diff --check` passed; browser inspected final
  static tables and plot labels on the running local app. No scaffold check rerun.
- Finance intuition/CSV trace: row `SPY,0.35` gives ticker SPY and decimal capital
  weight 0.35. The price column is selected by ticker, adjusted prices become
  adjacent daily returns, and the common sample produces the covariance used by
  calculate_attribution. The engine's annualized SPY marginal contribution is
  0.1101552151; multiplying by its weight produces component 0.0385543253,
  displayed as **3.8554 annualized volatility pp**. Dividing by portfolio volatility
  gives **43.4640% of total risk**, despite only **35% of capital**. Its volatility
  and covariance with every other holding explain that difference.
- Interview question: "Why does SPY's 35% capital allocation produce a 43.46%
  volatility share?" Answer: contribution depends on its covariance with the
  whole weighted portfolio, not weight alone; component equals weight times
  marginal sensitivity, then share divides component by total volatility.
- Next action: M5 final correctness review, fresh setup, reproducible demo and
  walkthrough. No remaining M4 blocker; no new scope requested.

## Milestone log — M5, 2026-10-05 (Asia/Kolkata)

- Status: complete within the exact MVP. Reviewed PROJECT_SPEC.md and both
  calculation/data contracts against data.py, metrics.py, attribution.py, app.py
  and all existing tests. No incorrect financial formula found. Fixed one concrete
  settings boundary: missing/non-string/blank title previously passed validation
  and could crash/misrender the UI; load_settings now raises a visible DataError.
  Four invalid-title cases plus one-asset and missing-price dashboard tests added.
- Changed: data.py, tests/test_data.py, tests/test_dashboard.py, README.md,
  START_HERE.md, tests/README.md and PLAN.md. README holds actual commands,
  assumptions, measured finding, code-linked explanation, 90-second demo and
  exactly two CV bullets. No report/export pipeline or other feature added.

| MVP item | Implementation and verification evidence |
|---|---|
| 1 CSV portfolio | load_portfolio; decimal/schema/duplicate/weight tests; real example and SPY-only CSV bytes supplied at upload boundary |
| 2 Historical download | download_prices shared by app/CLI; real dashboard refresh downloaded five assets and SPY alone; source-verified USD; validated save/load |
| 3 Daily returns | daily_returns/prepare_returns; independent synthetic answers and two-adjacent-return missing-price exclusion |
| 4 Annualized asset volatility | annualized_asset_volatility; 2% daily std gives 31.74901573% annualized; real table |
| 5 Covariance/correlation | daily_covariance/correlation_matrix; ddof=1 known answers, label/shape/constant cases; real matrices |
| 6 Portfolio volatility | portfolio_volatility/calculate_metrics; diagonal example and weighted-return-std reconciliation; real 8.8704% |
| 7 Marginal risk | calculate_attribution; independent MRC answers, units, alignment; real table |
| 8 Component risk | same; signed examples, zero-weight handling, Euler sum; real sum 0.08870411863114672 |
| 9 Risk shares | same; shares reconcile to 1; single asset 100%; undefined zero-risk reasons |
| 10 Diversification benefit | same; independent 0.2546440075 example, perfect-correlation/hedge/zero cases; real 34.3627%, single asset 0% |
| 11 Four plots | build_figures; values/sign/units/NaN/connectgaps tests, real serialization and live-browser visual inspection of allocation, heatmap, component bars, rolling line |
| 12 Streamlit dashboard | offline AppTest error/input/cache flows, separate real refresh/cache flows and fresh-environment local server/browser |

- Offline commands: existing `.venv/Scripts/python.exe -m pytest -q` baseline
  **141 passed in 9.97s**, expanded suite **147 passed in 7.32s**. The sandbox
  could not launch base Python; approved execution used the same venv. All provider
  calls in pytest are mocked; no live data needed. Missing-price UI test shows
  one missing A price, two unavailable A returns, visible exclusion warning and
  all four plots. Existing tests verify rolling gap windows/recovery, insufficient
  history, constants, zero/negative risk, singular/invalid covariance, label
  reordering, cache corruption/currency and failed refresh/write rollback.
- Fresh environment: created ignored `data/raw/m5-venv` with Python 3.11.4;
  `-m pip install -e ".[dev,data]"` exit 0 (build isolation enabled);
  `-m pip check`: no broken requirements; `scripts/check_starter.py`: PASS,
  explicitly scaffold/config/syntax only; `-m pytest -q`: **147 passed in 7.39s**.
  Core installed versions: NumPy 2.4.6, pandas 3.0.6, Streamlit 1.65.0, Plotly
  6.9.0, pytest 9.1.1, yfinance 1.7.0, pip 23.1.2, runtime setuptools 65.5.0.
  pip's isolated build satisfied pyproject setuptools>=68; runtime setuptools
  is separate. This is tested Windows setup, not a lockfile or Linux verification.
- Launch: fresh Python ran `-m streamlit run app.py --server.headless true
  --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false`.
  Server started; in-app browser showed the input page, example metrics/matrices
  and all four rendered plots with correct labels. Browser initialization was slow
  but recovered; one attempted scroll used an out-of-viewport coordinate and was
  corrected. Browser screenshots inspected allocation/heatmap, component bars
  and rolling line. Server stopped after verification.
- Real flow: ignored `data/raw/verify_m5.py`, executed with fresh Python, exit 0.
  Injected example CSV bytes at Streamlit file_uploader, clicked actual refresh
  button through unmocked yfinance, validated two metrics/four charts, then reran
  with download_prices forbidden. Repeated with `SPY,1` using an isolated ignored
  single-asset cache so canonical example cache remains intact. No app error or
  exception. All four figure objects serialized with data; component/share sums
  reconciled. Initial manual-script attempts failed on its app import path and
  cache-redirection lambda's missing staging arguments; both harness issues were
  corrected before the successful final run, without changing production logic.
- Real example retrieval UTC: 2026-10-04T19:37:23.842145+00:00 (2026-10-05 IST).
  1,003 price dates, 2022-01-03 to 2025-12-31; all quotes source-verified USD;
  1,002 common returns, zero missing/excluded dates; latest 756, 2022-12-27 to
  2025-12-31. Annualized volatility 0.08870411863114673; benefit
  0.3436269244566381; component sum 0.08870411863114672; share sum
  0.9999999999999999; 697 available rolling windows, 59 initial unavailable.
  SPY weight 0.35, annualized MRC 0.11015514543389708, CRC
  0.03855430090186398, risk share 0.434639354934376. SPY-only retrieval
  2026-10-04T19:37:24.929245+00:00: volatility 0.15357634044844243,
  benefit 0, risk share approximately 1, same counts/dates, four plots.
- Verification limits: native browser file-picker upload was not exercised;
  AppTest has no upload action, so bytes were injected at its uploader boundary.
  Browser separately verified the example rendering. Missing-data behavior is
  verified with synthetic fixtures, not gaps in the real sample. No provider,
  setup or implementation blocker remains. Package ranges allow later changes;
  provider revisions can change measured findings. No claimed business impact.
- Finance intuition/interview: SPY's covariance with the whole weighted portfolio
  makes 35% capital contribute 43.46% volatility share. A component in volatility
  pp differs from a share of total risk. Question: does MRC_SPY predict a funded
  transfer from TLT? Answer: first-order change is delta*(MRC_SPY-MRC_TLT), because
  both weights change. README contains the code trace and demonstration.
- No subagents, worktrees, commit, push, publish or deployment. Private notes,
  provider/cache and fresh environment remain ignored. `git diff --check` passed;
  `git check-ignore` confirmed fresh venv, verification script, single-asset cache,
  canonical cache/manifest and private role brief excluded. `git status --short`
  showed only the seven intended tracked files modified. Git emitted LF/CRLF
  notices and a denied global-ignore read; repository ignore checks still passed.
  Next action: rehearse README demo and interview explanation;
  no further feature implementation is pending.
