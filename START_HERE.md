# Start here — focused 12-feature MVP

This revised starter replaces the earlier broader plan. It covers portfolio CSV
loading, historical prices, returns, volatility, risk attribution, diversification
benefit and four Streamlit visualizations. See PROJECT_SPEC.md for the exact list.
It is a starter scaffold, not an implemented financial engine.

## 1. What you need
- Python 3.11 or 3.12, Git, an editor and Codex access.
- Internet for package installation and initial historical-data acquisition.
- Approximately 12 focused hours across two days, including verification and learning.

Use either your existing WSL setup or native Windows, keeping the project and its
virtual environment in the same environment. Do not share a Windows venv with WSL.
For Codex installation, follow the [official CLI setup](https://developers.openai.com/codex/cli).
Start it in this project folder and use an available sign-in method. No OpenAI API
key is needed by this application because it makes no LLM calls.

## 2. Extract and set up
Extract the revised ZIP into a fresh folder to avoid leaving old scenario/config
files behind. Open the inner portfolio-risk-attribution folder containing AGENTS.md.
If you already implemented any code, keep that existing repository and ask Codex
to reconcile the new specification with it; do not overwrite completed work blindly.
The following commands are for a fresh starter checkout.

### WSL / Linux / macOS
```bash
python3 --version
git init
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,data]"
python scripts/check_starter.py
python -m streamlit run app.py
```
Use python3.11 or python3.12 to create the venv if python3 is older than 3.11.
Install the matching venv support package if your WSL Python reports it missing.

### Windows PowerShell
```powershell
py -3.11 --version
git init
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,data]"
.\.venv\Scripts\python.exe scripts/check_starter.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Use py -3.12 instead if that is your installed version. Use the same venv Python
for later tests. These commands do not require PowerShell script activation.
Stop Streamlit with Ctrl+C. The current page is explicitly a placeholder.

Create an initial Git checkpoint after setup:
```bash
git add .
git commit -m "Add focused portfolio risk attribution starter"
```
Configure your own Git author name/email first if needed. Provider caches and the
private role brief are excluded by .gitignore; the sample portfolio CSV is included.

## 3. Start coding with Codex
Launch `codex` in this folder, or open it in your Codex editor client. No special
MCP server, custom skills or configuration files are necessary.
Codex reads AGENTS.md; its instructions refer to the other project documents.
No `/init` is needed because AGENTS.md already exists.

1. Read PROJECT_SPEC.md yourself and inspect data/portfolio.csv.
2. Paste the M1 prompt from docs/CODEX_PROMPTS.md.
3. Review the changes and verification result; ask for a small numerical explanation.
4. Check the PLAN.md update and create a Git checkpoint.
5. Continue with M2, M3, M4 and M5. Use the resume prompt if starting a new session.

Milestones are portfolio/data, metrics, attribution, dashboard, and final validation.
Do not request the entire application in one prompt. Keep the saved time for
understanding the calculations and preparing an explanation of actual results.

## 4. Important files
| File | Purpose |
|---|---|
| AGENTS.md | Persistent instructions and strict scope boundaries |
| PROJECT_SPEC.md | Exact 12-feature list and completion criteria |
| PLAN.md | Two-day schedule and resumable progress log |
| docs/METHODOLOGY.md | Formula conventions and independent numerical examples |
| docs/DATA_CONTRACT.md | Portfolio CSV, settings, download/cache and module contracts |
| docs/CODEX_PROMPTS.md | Updated prompts M1–M5, resume and learning prompts |
| data/portfolio.csv | Example ticker/weight portfolio |
| config/settings.json | Dates, currency and estimation settings; no holdings |
| docs/ROLE_ALIGNMENT_PRIVATE.md | Private JD mapping, excluded from Git |
| pyproject.toml, src/, app.py | Installable scaffold and placeholder dashboard |

## 5. Current state and verification
The starter includes documents, CSV/configuration, a tiny synthetic price fixture
and a standard-library configuration checker. Real market-data download, financial
functions, their pytest tests and the four-plot dashboard are not yet implemented.
The initial checker validates the scaffold only; it is not a financial test suite.

Dependency ranges are initial constraints, not a tested lockfile. After M5 works
in a clean virtual environment, record the tested Python and package versions.
Keep calculated findings and demo instructions in README.md; no report engine is
required. All 12 requested features remain in scope, including rolling volatility.

Official setup references used in the original starter (checked 2026-10-03):
- [Codex CLI](https://developers.openai.com/codex/cli)
- [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
