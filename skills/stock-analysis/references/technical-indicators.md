# Technical Indicators

This reference covers computing common technical indicators from OHLCV data (columns: open, high, low, close, volume). All calculations use pandas and numpy.

The script `scripts/calc_indicators.py` provides reusable implementations.

## Moving Averages

```python
import pandas as pd

def ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()

# Usage
df["ma5"] = ma(df["close"], 5)
df["ma10"] = ma(df["close"], 10)
df["ma20"] = ma(df["close"], 20)
df["ma60"] = ma(df["close"], 60)
```

## MACD (Moving Average Convergence Divergence)

```python
def macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    macd_bar = 2 * (dif - dea)
    return dif, dea, macd_bar

df["dif"], df["dea"], df["macd"] = macd(df["close"])
```

**Interpretation:**
- DIF crosses above DEA → bullish (golden cross)
- DIF crosses below DEA → bearish (death cross)
- MACD histogram turns positive from negative → momentum shift

## RSI (Relative Strength Index)

```python
def rsi(close: pd.Series, window=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df["rsi6"] = rsi(df["close"], 6)
df["rsi14"] = rsi(df["close"], 14)
```

**Typical thresholds:** Overbought > 70, Oversold < 30

## KDJ (Stochastic Indicator)

```python
def kdj(high, low, close, n=9, m1=3, m2=3):
    low_n = low.rolling(n).min()
    high_n = high.rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(span=m1).mean()
    d = k.ewm(span=m2).mean()
    j = 3 * k - 2 * d
    return k, d, j

df["k"], df["d"], df["j"] = kdj(df["high"], df["low"], df["close"])
```

**Interpretation:** K > D and both rising → bullish; K crosses below D from above 80 → sell signal.

## Bollinger Bands

```python
def bollinger(close: pd.Series, window=20, num_std=2):
    middle = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower

df["boll_upper"], df["boll_mid"], df["boll_lower"] = bollinger(df["close"])
```

**Interpretation:** Price touching upper band → overbought; touching lower band → oversold; bands contracting → low volatility (potential breakout ahead).

## ATR (Average True Range)

```python
def atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window).mean()

df["atr14"] = atr(df["high"], df["low"], df["close"])
```

## Volume-Based Indicators

### OBV (On-Balance Volume)

```python
def obv(close, volume):
    return (volume * (close.diff() > 0).map({True: 1, False: -1})).cumsum()

df["obv"] = obv(df["close"], df["volume"])
```

### Volume Ratio (量比)

```python
# Volume ratio = current volume / average volume of last 5 days at same interval
# Simple version for daily data:
def volume_ratio(volume, window=5):
    return volume / volume.rolling(window).mean()

df["vr"] = volume_ratio(df["volume"])
```

### Volume-Weighted Average Price (VWAP)

```python
# VWAP is typically calculated intraday, but daily approximation:
df["vwap"] = (df["volume"] * df["close"]).cumsum() / df["volume"].cumsum()
```

## Combining Indicators

When generating analysis signals, combine multiple indicators rather than relying on any single one:

```python
# Example: strong bullish signal
bullish = (
    (df["close"] > df["ma20"]) &
    (df["dif"] > df["dea"]) &
    (df["rsi14"] > 50) &
    (df["close"] > df["boll_mid"])
)
```

## Performance Note

For batch computation across many stocks, use `scripts/calc_indicators.py` which is optimized for DataFrame operations.
