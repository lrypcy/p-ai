# A-Share Market Data (A股)

## Stock Code Conventions

| Exchange | Prefix | Example | Format |
|----------|--------|---------|--------|
| Shanghai | SH/600/601/603/688 | 600519 | 6 digits |
| Shenzhen | SZ/000/001/002/300 | 000001 | 6 digits |
| Beijing | BJ/8xx/9xx | 830799 | 6 digits |
| STAR Board (科创板) | 688xxx | 688981 | 688 prefix |
| ChiNext (创业板) | 300xxx | 300750 | 300/301 prefix |

Market prefix is **not needed** in AKShare functions — just pass the 6-digit code.

## Real-Time Quotes

### Full Market Snapshot (preferred source — East Money)

```python
import akshare as ak

# All A-shares (沪深京) — ~5800 stocks, ~70s
df = ak.stock_zh_a_spot_em()

# Exchange-specific
df_sh = ak.stock_sh_a_spot_em()         # Shanghai
df_sz = ak.stock_sz_a_spot_em()         # Shenzhen
df_bj = ak.stock_bj_a_spot_em()         # Beijing
df_cy = ak.stock_cy_a_spot_em()         # ChiNext
df_kc = ak.stock_kc_a_spot_em()         # STAR Board
df_new = ak.stock_new_a_spot_em()       # New stocks
```

Returns columns: 序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收, 量比, 换手率, 市盈率, 市净率

### Individual Stock Detail

```python
# Basic info
info = ak.stock_individual_info_em(symbol="000001")

# Real-time quote from Xueqiu
xq = ak.stock_individual_spot_xq(symbol="000001")

# Level 2 market data (五档盘口)
bid_ask = ak.stock_bid_ask_em(symbol="000001")
```

### Index Quotes

```python
# All index real-time quotes
indices = ak.stock_zh_index_spot_em(symbol="上证系列指数")
# choices: "沪深重要指数", "上证系列指数", "深证系列指数", "中证系列指数"

# Individual index daily history
sh_index = ak.stock_zh_index_daily_em(symbol="sh000001")  # 上证指数
sz_index = ak.stock_zh_index_daily_em(symbol="sz399001")  # 深证成指
cy_index = ak.stock_zh_index_daily_em(symbol="sz399006")  # 创业板指
```

## Historical K-Line Data

### Daily / Weekly / Monthly

```python
df = ak.stock_zh_a_hist(
    symbol="000001",         # 6-digit code
    period="daily",          # "daily" | "weekly" | "monthly"
    start_date="20240101",   # YYYYMMDD
    end_date="20260101",
    adjust="qfq"             # "" = none, "qfq" = 前复权, "hfq" = 后复权
)
```

Returns columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 换手率

### Minute Bars

```python
df = ak.stock_zh_a_hist_min_em(
    symbol="000001",
    period="5",              # 1 | 5 | 15 | 30 | 60 (minutes)
    start_date="2025-06-01 09:30:00",  # datetime format
    end_date="2025-06-26 15:00:00",
    adjust=""                # 1min data does not support adjustment
)
```

Note: 1-minute data only returns the last 5 trading days with no adjustment.

### Multiple Data Sources

| Source | Function | Characteristics |
|--------|----------|-----------------|
| East Money | `stock_zh_a_hist` | Fast, reliable, recommended |
| Sina | `stock_zh_a_daily` | May have IP limits on high frequency |
| Tencent | `stock_zh_a_hist_tx` | Stable, fewer features |

## Financial Statements

```python
# Balance sheet
bs = ak.stock_financial_balance_sheet_by_report_em(symbol="000001")

# Income statement
inc = ak.stock_financial_income_statement_by_report_em(symbol="000001")

# Cash flow
cf = ak.stock_financial_cash_flow_by_report_em(symbol="000001")

# Financial indicators (ROE, EPS, etc.)
indicators = ak.stock_financial_abstract_ths(symbol="000001")
```

## Special Categories

```python
# ST / risk-warned stocks
st = ak.stock_zh_a_st_em()

# IPO new stocks
new = ak.stock_zh_a_new_em()

# Delisted stocks
delisted = ak.stock_zh_a_stop_em()

# Concept boards
concepts = ak.stock_board_concept_name_em()

# Industry boards
industries = ak.stock_board_industry_name_em()
```

## Block Trades (大宗交易)

```python
block = ak.stock_block_trade_em(symbol="000001", start_date="2024-01-01", end_date="2026-06-26")
```

## Short Selling (融资融券)

```python
# Individual stock margin data
margin = ak.stock_margin_detail_em(symbol="000001", date="20250620")

# Market aggregate margin data
market_margin = ak.stock_margin_spot_em()
```

## Level 2 Market Data & 委比 (Order Book)

委比 = (委托买入量 - 委托卖出量) / (委托买入量 + 委托卖出量) × 100%

Range: -100% (full sell pressure) to +100% (full buy pressure).

```python
# Bid/ask quote (五档盘口)
bid_ask = ak.stock_bid_ask_em(symbol="000001")
# Returns columns: 最新价, 涨跌幅, 买一价~买五价, 买一量~买五量,
#                  卖一价~卖五价, 卖一量~卖五量
```

Compute 委比 from bid/ask data:

```python
def compute_weibi(bid_ask_df: pd.DataFrame) -> float:
    """Compute 委比 (entrust ratio) from bid/ask data."""
    buy_vol = sum(bid_ask_df.iloc[0][f"买{i}量"] for i in range(1, 6))
    sell_vol = sum(bid_ask_df.iloc[0][f"卖{i}量"] for i in range(1, 6))
    if buy_vol + sell_vol == 0:
        return 0.0
    return (buy_vol - sell_vol) / (buy_vol + sell_vol) * 100
```

## Volume Ratio (量比)

量比 = current minute volume / average minute volume over last 5 days at same time.

```python
# The full market snapshot includes 量比 directly:
spot = ak.stock_zh_a_spot_em()
# Column "量比" is already computed

# For individual stock, from bid/ask or spot data:
individual_spot = ak.stock_bid_ask_em(symbol="000001")
# Also available in the 实时行情 data
```

## Live Intraday Data (盘中实时)

```python
# Live intraday quotes — updated in real-time during trading hours
live = ak.stock_zh_a_live_em(symbol="000001")
# Returns: 时间, 现价, 涨跌幅, 成交量, 成交额, 均价

# Intraday minute data (当日分时)
intraday = ak.stock_intraday_sina(symbol="sz000001", date="20250626")
# Returns: 时间, 价格, 均价, 成交量, 成交额

# Intraday from East Money
intraday_em = ak.stock_intraday_em(symbol="000001")
```

## Company News (公司新闻)

```python
# Stock-specific news from East Money
news = ak.stock_news_em(symbol="000001")
# Returns: 新闻标题, 发布时间, 新闻内容, 文章来源

# Stock comment / sentiment
comment = ak.stock_comment_detail_scrd_focus_em(symbol="000001")
# Shows investor focus/sentiment data
```
