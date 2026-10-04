"""Explicit M1 download/cache CLI. Relative paths resolve from repository root."""

import argparse
import sys

from portfolio_risk.data import (
    DataError, download_prices, load_cache, load_portfolio, load_settings, save_cache,
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", default="data/portfolio.csv")
    parser.add_argument("--settings", default="config/settings.json")
    parser.add_argument("--cache-dir", default="data/processed")
    parser.add_argument("--assume-usd", action="store_true", help="Confirm USD only where source currency is unknown; never override known non-USD quotes.")
    parser.add_argument("--load-cache", action="store_true", help="Validate and load matching cache offline, with no network calls.")
    args = parser.parse_args(argv)
    try:
        weights = load_portfolio(args.portfolio)
        settings = load_settings(args.settings)
        start, end = settings["download_start"], settings["download_end_exclusive"]
        names = list(weights.index)
        if args.load_cache:
            data = load_cache(names, start, end, args.cache_dir)
        else:
            data = download_prices(names, start, end, assume_usd=args.assume_usd)
            save_cache(data, args.cache_dir)
            data = load_cache(names, start, end, args.cache_dir)
        p = data.provenance
        print(f"Portfolio: {len(weights)} holdings; decimal weight sum={weights.sum():.10f}")
        print(f"Source: {p['source']}; yfinance {p['provider_version']}; Python {p['python_version']}")
        print(f"Retrieved UTC: {p['retrieved_at_utc']}")
        print(f"Adjusted prices: {p['row_count']} union dates, {p['actual_first_date']} through {p['actual_last_date']}")
        print(f"Adjustment: {p['adjustment']}")
        print(f"Missing prices: {p['missing_values']}")
        print(f"Currency: {p['currency_verification']}")
        for warning in p["warnings"]:
            print(f"WARNING: {warning}")
        print("M1 price-data verification only; usable returns and financial metrics are M2.")
        return 0
    except (DataError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
