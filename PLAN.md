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
- [ ] M1 completed with CSV portfolio and real market-data cache.
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
Completed: revised planning files, CSV example, settings, package skeleton,
placeholder app, synthetic fixture and scaffold checker. The original scenarios
config and reports folder have been removed. No market data or financial engine
has been implemented. Next: START_HERE.md, then M1 in docs/CODEX_PROMPTS.md.

## Milestone log — fill after each stage
- Stage/status:
- Files changed:
- Commands and actual results:
- Finance concept understood:
- Decisions or blockers:
- Next action:
