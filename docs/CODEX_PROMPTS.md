# Codex prompts — exact 12-feature MVP

Use one milestone prompt per coding turn. Complete and verify that milestone;
then review its diff and finance explanation before starting the next one.
The earlier broader implementation prompts are superseded by this file.

## M1 — first prompt: portfolio CSV and market data
```text
Read AGENTS.md, PROJECT_SPEC.md, PLAN.md, docs/METHODOLOGY.md and
 docs/DATA_CONTRACT.md. This is my two-day Portfolio Risk Attribution Engine.
Implement M1 only, following the exact 12-feature scope.

Inspect my environment and use the project venv. Implement portfolio CSV loading
and validation, shared historical-price downloader, explicit CLI wrapper, local
cache and provenance. Holdings must come from CSV; do not hardcode five assets.
Handle quote currency, one-ticker downloads, unavailable symbols and stale cache
explicitly. Download real adjusted prices if permitted. Never substitute fabricated
data. Add offline validation tests with the existing synthetic price fixture.
Run checks, update PLAN.md with actual results and explain portfolio weights versus
price data and the adjustment convention. Do not implement extra features or the UI.
```

## M2 — returns and volatility metrics
```text
Read the current project documents and inspect the completed M1 code. Implement
M2 only: daily returns, annualized asset volatility, daily covariance and correlation
matrices, total portfolio volatility and 60-day rolling portfolio volatility.
Follow the common-sample, missing-data, ddof and annualization conventions. Add
known-answer tests, portfolio-volatility versus weighted-return-std reconciliation,
one-asset shapes, constant assets and rolling-gap tests. Run them, update PLAN.md,
and explain covariance versus correlation with a small numerical example. Do not
add tail risk, drawdown, stress tests, reports or any feature outside PROJECT_SPEC.md.
```

## M3 — risk attribution
```text
Implement M3 only: marginal contribution, component contribution, percentage
contribution and the specified diversification benefit. Keep pure functions separate
from the UI and align ticker labels before arithmetic. Test known numerical answers,
component-sum and share-sum identities, negative components, zero weights, zero
portfolio volatility, singular covariance and reordered input columns. Run tests,
update PLAN.md, and explain why 50% of capital can account for 80% of portfolio
volatility in the documented two-asset example. Do not add factor/group attribution
or an optimizer.
```

## M4 — Streamlit dashboard
```text
Implement M4 as a single-page Streamlit dashboard. Support a portfolio CSV upload
or explicit bundled example, validate weights, and provide an explicit historical
price download/refresh action with cache reuse. Display all requested metrics and
matrices, with correct units, dates, provenance and warnings. Create exactly the
four requested plots: allocation, correlation heatmap, signed risk contribution
by asset, and rolling portfolio volatility. Call the tested engine rather than
copying finance formulas into the UI. Invalid CSVs and stale caches must show useful
messages. Verify the full flow using real data, update PLAN.md and explain how one
CSV row maps to a risk contribution. Do not add exports, reports or new metrics.
```

## M5 — correctness and completion
```text
Review the project against every item in the 12-feature MVP and its calculation/data
contracts. Fix concrete correctness issues and add targeted tests where necessary.
Run the offline suite, verify a fresh setup, the CSV-to-download-to-dashboard flow,
one-asset input, missing-data handling, and all four plots. Record precisely what
was tested and any blockers. Replace the starter README with actual run commands,
assumptions and one measured finding. Capture working dependency/Python versions.
Write a short demo and interview explanation tied to my actual code, plus two CV
bullets only for completed features. Keep these in the README, not a report pipeline.
Update PLAN.md and START_HERE.md to reflect reality. Do not add features, deploy or push.
```

## Resume in a fresh session
```text
Read AGENTS.md, PROJECT_SPEC.md, PLAN.md, docs/METHODOLOGY.md and
 docs/DATA_CONTRACT.md. Inspect actual code/test status, summarize the next unfinished
milestone, then implement it within the exact 12-feature MVP. Preserve completed
work, do not rebuild from scratch, and update PLAN.md with verified results.
```

## Understand the implementation
```text
Explain the function just implemented using a tiny numerical example. Walk through
inputs, calculations, units and limitations, distinguishing finance assumptions
from coding choices. Ask me three short questions to check understanding. Do not
edit files during this explanation.
```
