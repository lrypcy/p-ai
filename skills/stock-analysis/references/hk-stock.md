# Hong Kong Stock Market Data (港股)

## Stock Code Conventions

| Exchange | Format | Example | Notes |
|----------|--------|---------|-------|
| HKEX Main Board | 5 digits | `00700` (Tencent) | Leading zero required |
| HKEX GEM | 5 digits starting with 08xxx | `08367` | — |

Pass code as-is to AKShare functions. No prefix needed.

## Real-Time Quotes

### Full Market Snapshot

```python
import akshare as ak

# All HK stocks real-time — ~2500 stocks, ~30s
df = ak.stock_hk_spot_em()
```

Returns columns: 序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收

### Individual Stock

```python
# Real-time via Sina
spot = ak.stock_hk_spot(symbol="00700")
```

## Historical K-Line Data

### Daily

```python
df = ak.stock_hk_hist(
    symbol="00700",          # 5-digit code
    period="daily",          # "daily" | "weekly" | "monthly"
    start_date="20240101",
    end_date="20260101",
    adjust="qfq"             # "" = none, "qfq" = 前复权, "hfq" = 后复权
)
```

### Minute Bars

```python
df = ak.stock_hk_hist_min_em(
    symbol="00700",
    period="5",              # 1 | 5 | 15 | 30 | 60
    start_date="2025-06-01 09:30:00",
    end_date="2025-06-26 16:00:00",
    adjust=""
)
```

## AH Cross-Listed Stocks (A+H 股)

```python
# All AH pairs with price comparison
ah = ak.stock_zh_ah_spot_em()

# AH premium index
ah_premium = ak.stock_zh_ah_name_em()
```

## Stock Connect (沪深港通)

```python
# North-bound (北上资金) — foreign capital into A-shares
north_net = ak.stock_em_hsgt_north_net_flow_in(indicator="沪股通")
north_acc = ak.stock_em_hsgt_north_acc_flow_in(indicator="北上")

# South-bound (南下资金) — Chinese capital into HK stocks
south_net = ak.stock_em_hsgt_south_net_flow_in(indicator="沪股通")
south_acc = ak.stock_em_hsgt_south_acc_flow_in(indicator="南下")

# Individual stock holding details via Stock Connect
# North-bound holdings
north_hold = ak.stock_hsgt_individual_em(market="沪股通", symbol="600519")
# South-bound holdings
south_hold = ak.stock_hsgt_individual_em(market="港股通", symbol="00700")
```

Note: `indicator` parameter choices — `"沪股通"`, `"深股通"`, `"北上"` for north-bound; `"沪股通"`, `"深股通"`, `"南下"` for south-bound.

## HK Index Data

```python
# Hang Seng Index family
hsi = ak.stock_hk_index_daily_em(symbol="HSI")         # 恒生指数
hscei = ak.stock_hk_index_daily_em(symbol="HSCEI")     # 国企指数
hstech = ak.stock_hk_index_daily_em(symbol="HSTECH")   # 恒生科技指数
```

## HK Stock Fundamentals (港股基本面)

```python
# HK stock company info
info = ak.stock_hk_individual_info_em(symbol="00700")
# Returns: 股票代码, 股票简称, 总市值, 流通市值, 市盈率,
#          市净率, 每股收益, 每股净资产, 所属行业

# AH premium/discount (A+H溢价率)
ah = ak.stock_zh_ah_premium_em()
# Shows A-share vs H-share price comparison
```

## HK Quarterly Financial Reports (港股财务报表)

```python
# HK stock quarterly/annual financial reports
# Income statement
hk_income = ak.stock_hk_financial_income_statement_by_report_em(symbol="00700")
# Returns: 报告期, 营业收入, 营业利润, 净利润, 每股收益

# Balance sheet
hk_balance = ak.stock_hk_financial_balance_sheet_by_report_em(symbol="00700")

# Cash flow
hk_cashflow = ak.stock_hk_financial_cash_flow_by_report_em(symbol="00700")

# Financial indicators
hk_financial = ak.stock_hk_financial_abstract_ths(symbol="00700")
# Returns: EPS, ROE, gross margin, net margin, etc.
```

## HK Stock News (港股新闻)

```python
# HK stock-related news
hk_news = ak.stock_hk_news_em(symbol="00700")
# Returns: 新闻标题, 发布时间, 文章来源
```

## HK Order Book & 委比

```python
# HK stock bid/ask
hk_bid_ask = ak.stock_hk_bid_ask_em(symbol="00700")
# Returns: 买一价~买五价, 买一量~买五量, 卖一价~卖五价, 卖一量~卖五量
```

## Important Notes for HK Data

- **Currency**: All prices are in HKD; volume in shares; turnover in HKD
- **Trading hours**: 09:30–12:00, 13:00–16:00 HKT
- **Data delay**: East Money HK quotes have ~15-minute delay
- **Stock Connect data**: South-bound flow data starts from 2014 (Shanghai Connect) and 2016 (Shenzhen Connect)
- **Leading zeros**: Always include leading zeros for HK codes (e.g., `"00700"` not `"700"`)
