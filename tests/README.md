# Offline milestone tests

The fixture prices_synthetic.csv contains four rows of synthetic, hand-check prices
for abstract tickers A and B. It is not market data and does not satisfy the
252-observation dashboard minimum. Small unit tests can use it directly.

Required financial cases and expected answers are in docs/METHODOLOGY.md. Add
pytest tests during M1–M3. M1's `test_data.py` validates portfolio input, price
schema, explicit downloader flags, one-ticker/MultiIndex extraction, currency
confirmation/rejection, cache matching/integrity, failed refresh/write recovery
and CLI/path behavior. Provider calls are mocked; test caches are temporary and
never replace the real market-data cache. Run with the project venv:
`python -m pytest -q`. No live network access is required.

M2's `test_metrics.py` checks hand-calculated returns, ddof=1 volatility and
covariance, correlation, annualization, fixed-weight portfolio volatility and
its reconciliation with weighted-return standard deviation. It also covers
one-asset matrix shapes, ticker reordering, zero weights, constant assets,
singular/invalid covariance, tiny-negative-variance diagnostics, missing prices,
the latest common-return lookback and dashboard minimum, and 60-row rolling
windows with gaps and recovery. Tests construct only labeled synthetic histories;
the real cache is untouched. Correlations for constant assets and rolling windows
with insufficient/gapped history must remain NaN, never fabricated zeros.

The initial scripts/check_starter.py only validates the
starter files, CSV, settings and Python syntax; it does not test a financial engine.
