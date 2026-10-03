# Tests to add during implementation

The fixture prices_synthetic.csv contains four rows of synthetic, hand-check prices
for abstract tickers A and B. It is not market data and does not satisfy the
252-observation dashboard minimum. Small unit tests can use it directly.

Required financial cases and expected answers are in docs/METHODOLOGY.md. Add
pytest tests during M1–M3. The initial scripts/check_starter.py only validates the
starter files, CSV, settings and Python syntax; it does not test a financial engine.
