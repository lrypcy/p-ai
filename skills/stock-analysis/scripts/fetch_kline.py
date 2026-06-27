#!/usr/bin/env python3
"""
Batch K-line data fetcher for China A-shares and Hong Kong stocks.

Uses AKShare (free, no API key required).

Usage:
    # Fetch daily data for A-share stocks
    python fetch_kline.py --symbols 000001,600519,300750 --market a --period daily --start 20240101 --end 20260101

    # Fetch daily data for HK stocks
    python fetch_kline.py --symbols 00700,09988,03690 --market hk --period daily --start 20240101 --end 20260101

    # Fetch minute data
    python fetch_kline.py --symbols 000001 --market a --period 5 --start "2025-06-01 09:30:00" --end "2025-06-26 15:00:00"

    # Output to CSV
    python fetch_kline.py --symbols 000001 --market a --period daily --start 20240101 --end 20260101 --output data.csv

Output format:
    - Directory `output/` with one CSV per symbol
    - Or single CSV with --output flag
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("pandas is required. Install: pip install pandas")
    sys.exit(1)

try:
    import akshare as ak
except ImportError:
    print("akshare is required. Install: pip install akshare")
    sys.exit(1)


def fetch_a_share(symbol: str, period: str, start: str, end: str, adjust: str = "qfq") -> pd.DataFrame:
    """Fetch A-share historical K-line data."""
    period_map = {
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
    }
    p = period_map.get(period, period)

    # Minute data uses a different function
    if period in ("1", "5", "15", "30", "60"):
        return ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            start_date=start,
            end_date=end,
            adjust="" if period == "1" else adjust,
        )

    return ak.stock_zh_a_hist(
        symbol=symbol,
        period=p,
        start_date=start,
        end_date=end,
        adjust=adjust,
    )


def fetch_hk_stock(symbol: str, period: str, start: str, end: str, adjust: str = "qfq") -> pd.DataFrame:
    """Fetch Hong Kong stock historical K-line data."""
    period_map = {
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
    }
    p = period_map.get(period, period)

    if period in ("1", "5", "15", "30", "60"):
        return ak.stock_hk_hist_min_em(
            symbol=symbol,
            period=period,
            start_date=start,
            end_date=end,
            adjust="",
        )

    return ak.stock_hk_hist(
        symbol=symbol,
        period=p,
        start_date=start,
        end_date=end,
        adjust=adjust,
    )


def main():
    parser = argparse.ArgumentParser(description="Batch fetch stock K-line data")
    parser.add_argument("--symbols", required=True, help="Comma-separated stock codes")
    parser.add_argument("--market", choices=["a", "hk"], default="a", help="Market: a = A-share, hk = Hong Kong")
    parser.add_argument("--period", default="daily", help="K-line period: daily/weekly/monthly or 1/5/15/30/60 for minutes")
    parser.add_argument("--start", default="20240101", help="Start date (YYYYMMDD or YYYY-MM-DD HH:MM:SS for minute)")
    parser.add_argument("--end", default="20260101", help="End date")
    parser.add_argument("--adjust", default="qfq", help="Adjust: ''=none, qfq=前复权, hfq=后复权")
    parser.add_argument("--output", help="Output CSV path (single file, first symbol only)")
    parser.add_argument("--outdir", default="output", help="Output directory for per-symbol files")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",")]
    fetcher = fetch_a_share if args.market == "a" else fetch_hk_stock

    results = {}
    for sym in symbols:
        print(f"Fetching {sym}...", end=" ", flush=True)
        try:
            df = fetcher(sym, args.period, args.start, args.end, args.adjust)
            if df is not None and len(df) > 0:
                results[sym] = df
                print(f"{len(df)} rows")
            else:
                print("empty result")
        except Exception as e:
            print(f"error: {e}")

    if not results:
        print("No data fetched.")
        return

    # Output
    if args.output:
        first_sym = symbols[0]
        if first_sym in results:
            results[first_sym].to_csv(args.output, index=False)
            print(f"Saved to {args.output}")
    else:
        outdir = Path(args.outdir)
        outdir.mkdir(exist_ok=True)
        for sym, df in results.items():
            path = outdir / f"{sym}_{args.period}.csv"
            df.to_csv(path, index=False)
            print(f"Saved {path}")


if __name__ == "__main__":
    main()
