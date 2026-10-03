# Portfolio Risk Attribution Engine — agent instructions

## Read first
Read PROJECT_SPEC.md, PLAN.md, docs/METHODOLOGY.md and docs/DATA_CONTRACT.md
before implementation. Use START_HERE.md for environment setup. These files
contain the context; no previous chat is required.

## Goal and scope
Build the exact 12-feature MVP in PROJECT_SPEC.md within two days for a Nomura
Credit Risk Exposure Management application. The user knows programming and is
learning the finance methodology. Complete the requested milestone and verify it.

- Workflow: portfolio CSV -> historical prices -> returns/covariance -> volatility
  attribution -> four visualizations in Streamlit.
- Stack: Python 3.11+, NumPy, pandas, Streamlit, Plotly and pytest. Use yfinance
  only in the explicit download adapter, outside the pure calculation functions.
- Portfolio holdings and weights come from CSV, never a hardcoded JSON allocation.
  data/portfolio.csv is an example, not a fixed five-asset engine constraint.
- Long-only, fully invested, USD-quoted instruments; defaults in config/settings.json.
- Scope is ONLY the user's 12 features. Do not add stress testing, historical
  scenario replay, VaR/ES, drawdown, HHI, report generation, exports, group/factor
  attribution, day-on-day monitoring, optimizers, ML or LLM features.
- No backend service, database, authentication, React or deployment requirement.
- This project demonstrates portfolio volatility analysis. Do not call it a
  counterparty-credit, PFE, initial-margin or regulatory-capital model.
- Use one sequential workflow. Do not add subagents or worktrees.

## Implementation
- Pure financial functions belong in src/portfolio_risk/; UI belongs in app.py.
- Align assets by ticker before arithmetic. Validate inputs. Never silently
  normalize weights, fill missing prices/returns with zero, interpolate prices,
  clip negative risk contributions, or invent market data.
- Use decimal returns internally and percentages only in presentation. Label
  annualized volatility, marginal/component units and percentage risk shares.
- Follow docs/METHODOLOGY.md for ddof, annualization, missing data and zero-risk cases.
- Add focused offline known-answer tests for numerical correctness and meaningful
  invalid-input cases. Keep provider network calls out of tests and app reruns.
- Show data source, actual dates, observation count and assumptions in the app.
- Prefer simple functions and structured results over frameworks. Do not fabricate
  output to hide errors. Undefined results must be visibly unavailable with a reason.
- Keep the private role brief, credentials, environments and market-data cache out
  of public Git commits. Preserve existing user work.

## Commands
- Setup: `python -m pip install -e ".[dev,data]"`
- Scaffold validation: `python scripts/check_starter.py`
- Financial tests after implementation: `python -m pytest -q`
- Dashboard: `python -m streamlit run app.py`
- Initial status: only the starter exists; financial functions remain unimplemented.

## Handoff
After each milestone, record actual results, decisions and next action in PLAN.md.
Explain the finance intuition and one interview question tied to the actual code.
Distinguish scaffold verification from financial-engine verification. Never claim
unrun tests, completed features, measured findings or business impact without evidence.
Finish independent work if blocked and record the blocker. Do not publish or push
unless requested. The earlier broader scope is superseded by this 12-feature MVP.
