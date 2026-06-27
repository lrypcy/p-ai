# Market Analysis Methods

This reference covers market-level analysis beyond individual stock data — capital flows, sector rotation, sentiment, and screening.

## Capital Flow Analysis (资金流向)

### North-Bound / South-Bound (沪深港通)

Stock Connect flows are the primary channel for cross-border capital between mainland China and Hong Kong.

```python
import akshare as ak

# 北向资金 — foreign capital flowing into A-shares
# Daily net inflow
north_sh = ak.stock_em_hsgt_north_net_flow_in(indicator="沪股通")
north_sz = ak.stock_em_hsgt_north_net_flow_in(indicator="深股通")
north_total = ak.stock_em_hsgt_north_net_flow_in(indicator="北上")

# Cumulative net inflow
north_acc = ak.stock_em_hsgt_north_acc_flow_in(indicator="北上")

# 南向资金 — Chinese capital flowing into HK stocks
south_sh = ak.stock_em_hsgt_south_net_flow_in(indicator="沪股通")
south_sz = ak.stock_em_hsgt_south_net_flow_in(indicator="深股通")
south_total = ak.stock_em_hsgt_south_net_flow_in(indicator="南下")

# Individual stock north-bound holdings
holdings = ak.stock_hsgt_industry_em(market="沪股通")
```

### Sector Capital Flow (板块资金流向)

```python
# Industry sector capital flow (行业板块资金流)
industry_flow = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
# choices for indicator: "今日", "3日", "5日", "10日"
# choices for sector_type: "行业资金流向", "概念资金流向"

# Concept sector capital flow
concept_flow = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="概念资金流向")
```

### Individual Stock Capital Flow (个股资金流向)

```python
# Capital flow for a specific stock
flow = ak.stock_individual_fund_flow(stock="000001", market="sz")
# market: "sh" for Shanghai, "sz" for Shenzhen, "bj" for Beijing
```

## Industry & Concept Sector Analysis

```python
# List all concept boards
concepts = ak.stock_board_concept_name_em()

# List all industry boards
industries = ak.stock_board_industry_name_em()

# Constituents of a concept board
concept_stocks = ak.stock_board_concept_cons_em(symbol="人工智能")

# Constituents of an industry board
industry_stocks = ak.stock_board_industry_cons_em(symbol="半导体")

# Concept board historical trend
concept_hist = ak.stock_board_concept_hist_em(symbol="人工智能", start_date="20240101", end_date="20260101")
```

## Stock Screening (选股)

### Technical Screeners

```python
# Top gainers/losers
# Use the full market snapshot and filter:
spot = ak.stock_zh_a_spot_em()
top_gainers = spot.nlargest(20, "涨跌幅")
top_volume = spot.nlargest(20, "成交额")

# Limit-up / Limit-down stocks (涨停跌停)
zt_pool = ak.stock_zt_pool_em()                  # Today's limit-up pool
zt_previous = ak.stock_zt_pool_previous_em()      # Previous session limit-up
zt_continuous = ak.stock_zt_pool_strong_em()      # Consecutive limit-up
zt_dt = ak.stock_zt_pool_dtgc_em()               # Limit-up with gap

# New highs in last N days
new_high = ak.stock_zt_pool_continuous_em()       # New high stocks
```

### Financial Screeners

```python
# Financial report abstract — fundamentals
abstract = ak.stock_financial_abstract_ths(symbol="000001")
# Includes: EPS, ROE, operating revenue growth, net profit growth

# Profit forecast (盈利预测)
forecast = ak.stock_profit_forecast_em(symbol="000001")

# Institutional research visits (机构调研)
visits = ak.stock_institute_visit_em(symbol="000001")
```

## Limit-Up / Limit-Down Analysis (龙虎榜)

```python
# Daily top trading records (龙虎榜)
lhb = ak.stock_lhb_detail_em(symbol="000001")

# LHB statistics
lhb_stats = ak.stock_lhb_stock_statistic_em(symbol="000001")

# LHB by date
lhb_date = ak.stock_lhb_trader_statistic_em(trade_date="20250620")
```

## Market Sentiment

```python
# Investor sentiment index
sentiment = ak.stock_market_activity_em()

# Margin trading overview
margin = ak.stock_margin_szse_summary()  # Shenzhen margin summary

# New stock subscription data
subscription = ak.stock_ipo_info_em(symbol="000001")
```

## Macroeconomic Indicators

```python
# GDP
gdp = ak.macro_china_gdp()

# CPI
cpi = ak.macro_china_cpi()

# PPI
ppi = ak.macro_china_ppi()

# PMI
pmi = ak.macro_china_pmi()

# Money supply (M0, M1, M2)
m2 = ak.macro_china_money_supply()

# Interest rate (LPR, SHIBOR)
lpr = ak.macro_china_lpr()
shibor = ak.macro_china_shibor()
```

## Stock News & Market Sentiment

### Individual Stock News

```python
# Company-specific news
news = ak.stock_news_em(symbol="000001")
# Returns: 标题, 内容, 发布时间, 文章来源

# Hot search / trending stocks
hot = ak.stock_hot_search_baidu()  # Baidu hot search
hot_rank = ak.stock_hot_rank_em()  # East Money hot ranking
```

### Market Sentiment

```python
# Market activity overview
activity = ak.stock_market_activity_em()
# Shows: rising/falling stocks, limit up/down counts, total volume

# Investor sentiment index
sentiment = ak.stock_comment_detail_scrd_focus_em(symbol="000001")
```

## Comprehensive Stock Analysis & Scoring Workflow

The following workflow produces a structured analysis with buy/hold/sell recommendation.

### 1. Data Collection Phase

Collect all data for a single stock:

```python
import akshare as ak
import pandas as pd
import numpy as np

def collect_stock_data(symbol: str) -> dict:
    """Collect all data needed for comprehensive analysis."""

    # Company profile
    info = ak.stock_individual_info_em(symbol)

    # K-line data (1 year)
    kline = ak.stock_zh_a_hist(symbol, period="daily",
                                start_date="20250101", end_date="20260626",
                                adjust="qfq")

    # Quarterly financial statements
    income = ak.stock_financial_income_statement_by_report_em(symbol)

    # Bid/ask for 委比
    bid_ask = ak.stock_bid_ask_em(symbol)

    # News
    news = ak.stock_news_em(symbol)

    # Profit forecast
    forecast = ak.stock_profit_forecast_em(symbol)

    return {
        "info": info, "kline": kline, "income": income,
        "bid_ask": bid_ask, "news": news, "forecast": forecast
    }
```

### 2. Technical Scoring

Score 0-5 on technical factors (5 = most bullish):

| Criterion | Score 0-1 | Score 2-3 | Score 4-5 |
|-----------|-----------|-----------|-----------|
| MA alignment | All MA bearish | Mixed | MA5 > MA10 > MA20 |
| MACD | DIF < DEA, below 0 | Crossing | DIF > DEA, rising |
| RSI (14) | >70 or <30 | 30-40 or 60-70 | 40-60 |
| Volume | Shrinking significantly | Stable | Increasing with price |
| Bollinger | Close below lower band | Middle band | Close above mid, trending up |
| KDJ | K < D, both falling | Mixed | K > D, both rising |

```python
def score_technical(kline: pd.DataFrame) -> dict:
    """Score technical indicators 0-5."""
    c = kline["收盘"]
    ma5 = c.rolling(5).mean()
    ma20 = c.rolling(20).mean()
    latest = kline.iloc[-1]

    score = {"ma_score": 0, "macd_score": 0, "rsi_score": 0,
             "volume_score": 0, "total": 0}

    # MA score
    if latest["收盘"] > ma5.iloc[-1] > ma20.iloc[-1]:
        score["ma_score"] = 4
    elif latest["收盘"] > ma20.iloc[-1]:
        score["ma_score"] = 3
    elif latest["收盘"] > ma5.iloc[-1]:
        score["ma_score"] = 2
    else:
        score["ma_score"] = 1 if latest["收盘"] > ma20.iloc[-1] else 0

    # RSI score (approximate)
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - 100 / (1 + gain / loss)
    rsi_val = rsi.iloc[-1]
    if 40 <= rsi_val <= 60:
        score["rsi_score"] = 4
    elif 30 <= rsi_val < 40 or 60 < rsi_val <= 70:
        score["rsi_score"] = 3
    else:
        score["rsi_score"] = 0 if rsi_val > 70 else 1

    # Volume score
    vol_ma5 = kline["成交量"].rolling(5).mean()
    if kline["成交量"].iloc[-1] > vol_ma5.iloc[-1] * 1.5:
        score["volume_score"] = 4
    elif kline["成交量"].iloc[-1] > vol_ma5.iloc[-1]:
        score["volume_score"] = 3
    else:
        score["volume_score"] = 2

    score["total"] = sum([score["ma_score"], score["rsi_score"],
                          score["volume_score"]])
    return score
```

### 3. Fundamental Scoring

Score 0-5 on fundamental factors (5 = best):

| Criterion | Score 0-1 | Score 2-3 | Score 4-5 |
|-----------|-----------|-----------|-----------|
| PE ratio | >60 or negative | 15-30 | <15 |
| Profit growth | Negative YoY | 0-15% | >15% |
| ROE | <5% | 5-15% | >15% |
| Revenue growth | Negative | 0-10% | >10% |
| Market cap | Micro <2B | Mid 10-100B | Large >100B |

```python
def score_fundamental(info: pd.DataFrame, income: pd.DataFrame) -> dict:
    """Score fundamental indicators 0-5."""
    score = {"pe_score": 0, "profit_score": 0, "roe_score": 0, "total": 0}

    # PE scoring
    try:
        pe = float(info.loc[info["item"] == "市盈率-动态", "value"].values[0])
        if 0 < pe < 15:
            score["pe_score"] = 4
        elif pe < 30:
            score["pe_score"] = 3
        elif pe < 60:
            score["pe_score"] = 2
        else:
            score["pe_score"] = 1
    except:
        score["pe_score"] = 2

    # Profit growth (YoY)
    if len(income) >= 2:
        latest_profit = income.iloc[0]["净利润"]
        prev_profit = income.iloc[1]["净利润"]
        if prev_profit and prev_profit != 0:
            growth = (latest_profit - prev_profit) / abs(prev_profit) * 100
            if growth > 15:
                score["profit_score"] = 4
            elif growth > 0:
                score["profit_score"] = 3
            elif growth > -15:
                score["profit_score"] = 2
            else:
                score["profit_score"] = 1

    score["total"] = sum([score["pe_score"], score["profit_score"]])
    return score
```

### 4. Market Sentiment Scoring

```python
def score_sentiment(bid_ask: pd.DataFrame, news: pd.DataFrame) -> dict:
    """Score market sentiment factors."""

    # 委比 from bid/ask
    buy_vol = sum(bid_ask.iloc[0][f"买{i}量"] for i in range(1, 6))
    sell_vol = sum(bid_ask.iloc[0][f"卖{i}量"] for i in range(1, 6))
    weibi = (buy_vol - sell_vol) / (buy_vol + sell_vol) * 100 if (buy_vol + sell_vol) > 0 else 0

    # Sentiment score
    score = {"weibi": weibi, "weibi_score": 0,
             "news_count": len(news) if news is not None else 0}

    if weibi > 20:
        score["weibi_score"] = 4
    elif weibi > 0:
        score["weibi_score"] = 3
    elif weibi > -20:
        score["weibi_score"] = 2
    else:
        score["weibi_score"] = 1

    return score
```

### 5. Final Recommendation

```python
def generate_recommendation(tech_score: float, fund_score: float,
                            sent_score: float) -> tuple:
    """Generate buy/hold/sell recommendation based on composite score.

    Returns: (recommendation, confidence)
    """
    composite = (tech_score * 0.4 + fund_score * 0.4 + sent_score * 0.2)

    if composite >= 4.0:
        return ("买入 (Buy)", "Strong")
    elif composite >= 3.0:
        return ("增持 (Accumulate)", "Moderate")
    elif composite >= 2.0:
        return ("持有 (Hold)", "Neutral")
    elif composite >= 1.0:
        return ("减持 (Reduce)", "Cautious")
    else:
        return ("卖出 (Sell)", "Strong")
```

### Complete Report Template

```python
def generate_stock_report(symbol: str) -> str:
    """Generate a complete stock analysis report."""

    data = collect_stock_data(symbol)
    tech = score_technical(data["kline"])
    fund = score_fundamental(data["info"], data["income"])
    sent = score_sentiment(data["bid_ask"], data["news"])
    rec, conf = generate_recommendation(tech["total"]/3, fund["total"]/2, sent["weibi_score"])

    report = f"""
=====================================
股票分析报告 | {symbol}
=====================================

【公司概况】
- 名称: {extract_info(data["info"], "股票简称")}
- 行业: {extract_info(data["info"], "行业")}
- 市值: {extract_info(data["info"], "总市值")} 亿
- PE: {extract_info(data["info"], "市盈率-动态")}
- PB: {extract_info(data["info"], "市净率")}

【技术面评分】({tech['total']}/15)
- MA排列: {tech['ma_score']}/5
- RSI评分: {tech['rsi_score']}/5
- 量价评分: {tech['volume_score']}/5

【基本面评分】({fund['total']}/10)
- PE评分: {fund['pe_score']}/5
- 盈利增长: {fund['profit_score']}/5

【市场情绪】
- 委比: {sent['weibi']:.1f}%
- 新闻热度: {sent['news_count']} 条

【综合建议】
推荐操作: {rec}
信心程度: {conf}

⚠️ 本报告基于公开数据自动生成，仅供参考，不构成投资建议。
    """
    return report
```

## Analysis Workflow Pattern

A typical market analysis workflow:

1. **Get macro context**: Check GDP, PMI, M2 trends — determine economic cycle phase
2. **Check capital flow**: North-bound net inflow/outflow direction — foreign sentiment
3. **Sector rotation**: Top capital inflow sectors — identify market hotspots
4. **Screen stocks**: Apply filters (volume, price action, fundamentals) within selected sectors
5. **Individual analysis**: Deep dive using the comprehensive scoring system above
6. **Recommendation**: Generate buy/hold/sell based on composite score
