"""Validate starter artifacts, not the as-yet-unimplemented finance engine."""

import ast
import csv
import json
import math
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    required = [
        "AGENTS.md", "START_HERE.md", "PROJECT_SPEC.md", "PLAN.md", "README.md",
        "docs/METHODOLOGY.md", "docs/DATA_CONTRACT.md", "docs/CODEX_PROMPTS.md",
        "app.py", "src/portfolio_risk/__init__.py", "tests/README.md",
    ]
    for name in required:
        require((ROOT / name).is_file(), f"Missing required file: {name}")

    with (ROOT / "pyproject.toml").open("rb") as handle:
        metadata = tomllib.load(handle)
    require(metadata["project"]["requires-python"] == ">=3.11", "Check Python requirement")
    settings = json.loads((ROOT / "config/settings.json").read_text())
    require(settings["base_currency"] == "USD", "MVP currency must be USD")
    require(settings["lookback_returns"] >= settings["min_observations"] >= 252,
            "Invalid observation settings")
    require(2 <= settings["rolling_window"] <= settings["lookback_returns"],
            "Invalid rolling window")
    require(settings["trading_days"] == 252, "Annualization contract requires 252")
    start = date.fromisoformat(settings["download_start"])
    end = date.fromisoformat(settings["download_end_exclusive"])
    require(start < end, "Invalid download dates")
    require(not {"holdings", "portfolio_value", "confidence", "scenarios"} & settings.keys(),
            "Out-of-scope or duplicated configuration")

    with (ROOT / "data/portfolio.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == ["ticker", "weight"], "Expected ticker,weight CSV")
        holdings = list(reader)
    require(bool(holdings), "Portfolio CSV must not be empty")
    tickers = [row["ticker"].strip() for row in holdings]
    require(all(tickers) and len(tickers) == len(set(tickers)), "Missing or duplicate tickers")
    weights = [float(row["weight"]) for row in holdings]
    require(all(math.isfinite(w) and w >= 0 for w in weights), "Invalid weight")
    require(math.isclose(sum(weights), 1, rel_tol=0, abs_tol=1e-8), "Weights must sum to 1")

    with (ROOT / "tests/fixtures/prices_synthetic.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == ["date", "A", "B"], "Unexpected fixture schema")
        rows = list(reader)
    require(len(rows) == 4, "Expected four synthetic fixture rows")
    for row in rows:
        date.fromisoformat(row["date"])
        require(all(math.isfinite(float(row[t])) and float(row[t]) > 0 for t in ("A", "B")),
                "Invalid fixture price")
    for name in ["app.py", "src/portfolio_risk/__init__.py", "scripts/check_starter.py"]:
        ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)
    print("PASS: starter files, TOML, portfolio CSV, settings, fixture and Python syntax.")
    print("Scaffold check only. No market-data or financial-engine verification performed.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, SyntaxError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
