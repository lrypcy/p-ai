#!/usr/bin/env python3
"""
Technical indicator calculator for OHLCV stock data.

Reads CSV with columns: 日期/date, 开盘/open, 收盘/close, 最高/high, 最低/low, 成交量/volume

Usage:
    # Compute specific indicators from CSV
    python calc_indicators.py --input data.csv --indicators ma macd rsi boll

    # Compute all indicators
    python calc_indicators.py --input data.csv --indicators all

    # Output to file
    python calc_indicators.py --input data.csv --indicators all --output result.csv
"""

import argparse
import sys
from typing import Optional

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("pandas and numpy required. Install: pip install pandas numpy")
    sys.exit(1)


def ma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=span).mean()


def compute_macd(close: pd.Series, fast=12, slow=26, signal=9):
    """MACD indicator."""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    macd_bar = 2 * (dif - dea)
    return dif, dea, macd_bar


def compute_rsi(close: pd.Series, window=14) -> pd.Series:
    """Relative Strength Index."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return pd.Series(100 - (100 / (1 + rs)), name=f"rsi_{window}")


def compute_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n=9, m1=3, m2=3):
    """KDJ Stochastic Oscillator."""
    low_n = low.rolling(n).min()
    high_n = high.rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(span=m1, adjust=False).mean()
    d = k.ewm(span=m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def compute_bollinger(close: pd.Series, window=20, num_std=2):
    """Bollinger Bands."""
    middle = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, window=14) -> pd.Series:
    """Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = close.diff().map(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
    return (volume * direction).cumsum()


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all indicators and return a DataFrame with indicator columns appended."""
    result = df.copy()

    # Determine column names
    close_col = "收盘" if "收盘" in df.columns else "close"
    high_col = "最高" if "最高" in df.columns else "high"
    low_col = "最低" if "最低" in df.columns else "low"
    open_col = "开盘" if "开盘" in df.columns else "open"
    volume_col = "成交量" if "成交量" in df.columns else "volume"

    close = df[close_col]
    high = df[high_col]
    low = df[low_col]
    volume = df[volume_col]

    # Moving averages
    for w in [5, 10, 20, 30, 60]:
        result[f"ma{w}"] = ma(close, w)

    # MACD
    dif, dea, macd_bar = compute_macd(close)
    result["dif"] = dif
    result["dea"] = dea
    result["macd"] = macd_bar

    # RSI
    result["rsi6"] = compute_rsi(close, 6)
    result["rsi14"] = compute_rsi(close, 14)

    # KDJ
    k, d, j = compute_kdj(high, low, close)
    result["k"] = k
    result["d"] = d
    result["j"] = j

    # Bollinger
    upper, mid, lower = compute_bollinger(close)
    result["boll_upper"] = upper
    result["boll_mid"] = mid
    result["boll_lower"] = lower

    # ATR
    result["atr14"] = compute_atr(high, low, close)

    # OBV
    result["obv"] = compute_obv(close, volume)

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute technical indicators from OHLCV CSV")
    parser.add_argument("--input", "-i", required=True, help="Input CSV with OHLCV data")
    parser.add_argument("--output", "-o", help="Output CSV with indicators appended")
    parser.add_argument("--indicators", "-n", default="all",
                        help="Comma-separated: ma,macd,rsi,kdj,boll,atr,obv or 'all'")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

    if args.indicators == "all":
        result = compute_all(df)
    else:
        selected = [s.strip() for s in args.indicators.split(",")]
        close_col = "收盘" if "收盘" in df.columns else "close"
        high_col = "最高" if "最高" in df.columns else "high"
        low_col = "最低" if "最低" in df.columns else "low"
        volume_col = "成交量" if "成交量" in df.columns else "volume"

        result = df.copy()
        if "ma" in selected:
            for w in [5, 10, 20, 30, 60]:
                result[f"ma{w}"] = ma(df[close_col], w)
        if "macd" in selected:
            dif, dea, macd_bar = compute_macd(df[close_col])
            result["dif"] = dif
            result["dea"] = dea
            result["macd"] = macd_bar
        if "rsi" in selected:
            result["rsi6"] = compute_rsi(df[close_col], 6)
            result["rsi14"] = compute_rsi(df[close_col], 14)
        if "kdj" in selected:
            k, d, j = compute_kdj(df[high_col], df[low_col], df[close_col])
            result["k"] = k
            result["d"] = d
            result["j"] = j
        if "boll" in selected:
            u, m, l = compute_bollinger(df[close_col])
            result["boll_upper"] = u
            result["boll_mid"] = m
            result["boll_lower"] = l
        if "atr" in selected:
            result["atr14"] = compute_atr(df[high_col], df[low_col], df[close_col])
        if "obv" in selected:
            result["obv"] = compute_obv(df[close_col], df[volume_col])

    print(f"Result: {len(result)} rows, {len(result.columns)} columns")

    if args.output:
        result.to_csv(args.output, index=False)
        print(f"Saved to {args.output}")
    else:
        print("\nFirst 5 rows:")
        pd.set_option("display.max_columns", None)
        print(result.head())
        print(f"\n... {len(result)} rows total")


if __name__ == "__main__":
    main()
