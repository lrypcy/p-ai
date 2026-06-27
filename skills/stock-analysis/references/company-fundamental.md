# Company Fundamentals Analysis

This reference covers company-level fundamental data: financial statements, quarterly earnings, company profile, valuation metrics, and institutional holdings. All functions use AKShare (free, no API key).

## Company Profile (公司概况)

### Basic Info from East Money

```python
import akshare as ak

# Comprehensive company info — includes: name, industry, market cap, PE, total shares, etc.
info = ak.stock_individual_info_em(symbol="000001")

# Returns fields like:
# 总市值, 流通市值, 市盈率(动态), 市净率, 每股净资产, 每股收益
# 营业收入, 净利润, 所属行业, 上市时间, 总股本, 流通股本
```

### Detailed Company Registration Info

```python
# Registration info: registered address, city, province, business scope
# Note: function name may vary by AKShare version
# From cninfo (巨潮资讯)
profile = ak.stock_profile_cninfo(symbol="000001")
# Returns: 公司名称, 英文名称, 注册地址, 办公地址, 所属行业,
#          董事长, 总经理, 成立日期, 上市日期, 员工人数,
#          公司网址, 经营范围, 公司简介, 主营业务
```

### Xueqiu Detailed Profile

```python
# Detailed company info from Xueqiu
xq_info = ak.stock_individual_basic_info_xq(symbol="SZ000001")
# Returns: market cap, PE, PB, industry sector, location
```

Key fields and their Chinese names:

| Field | Chinese | Source |
|-------|---------|--------|
| Market cap | 总市值 | `stock_individual_info_em` |
| Market cap (float) | 流通市值 | `stock_individual_info_em` |
| PE (TTM) | 市盈率(动态) | `stock_individual_info_em` |
| PB | 市净率 | `stock_individual_info_em` |
| Industry | 所属行业 | `stock_individual_info_em` |
| City/Region | 所在城市/省份 | `stock_profile_cninfo` |
| Employee count | 员工人数 | `stock_profile_cninfo` |
| Business scope | 主营业务/经营范围 | `stock_profile_cninfo` |

## Financial Statements (财务报表)

### Quarterly Income Statement (季度利润表)

This is the key data source for quarterly profit analysis.

```python
# Quarterly income statement — shows revenue, cost, profit by quarter
income = ak.stock_financial_income_statement_by_report_em(symbol="000001")

# Key columns: 报告期(quarter), 营业收入(revenue), 营业总支出,
# 营业利润(operating profit), 利润总额, 净利润(net profit),
# 归属母公司净利润(net profit attr. to parent), 扣非净利润,
# 基本每股收益(EPS), 每股净资产
```

To get clean quarterly comparisons:

```python
def get_quarterly_profit(symbol: str) -> pd.DataFrame:
    """Get quarterly net profit data."""
    df = ak.stock_financial_income_statement_by_report_em(symbol)
    # Filter for quarterly reports (Q1, Q2, Q3, Q4)
    df = df[df["报告期"].str.contains(r"\d{4}-\d{2}-\d{2}", na=False)]
    df = df[["报告期", "营业收入", "营业利润", "净利润", "基本每股收益", "归属母公司净利润"]]
    return df
```

### Balance Sheet (资产负债表)

```python
# Quarterly balance sheet
balance = ak.stock_financial_balance_sheet_by_report_em(symbol="000001")
# Columns: 报告期, 流动资产, 固定资产, 总资产, 总负债,
#          归属母公司股东权益, 所有者权益, 资产负债率
```

### Cash Flow Statement (现金流量表)

```python
# Quarterly cash flow statement
cashflow = ak.stock_financial_cash_flow_by_report_em(symbol="000001")
# Columns: 报告期, 经营活动现金流净额, 投资活动现金流净额,
#          筹资活动现金流净额, 现金流净增加额
```

## Financial Indicators (财务指标)

```python
# Financial abstract — key indicators from Tonghuashun
abstract = ak.stock_financial_abstract_ths(symbol="000001")
# Includes: EPS, ROE, operating revenue growth, net profit growth rate,
#           gross margin, net margin, asset-liability ratio
```

## Profit Forecast & Earnings (盈利预测与业绩)

```python
# Profit forecast from analysts (东方财富)
forecast = ak.stock_profit_forecast_em(symbol="000001")
# Columns: 预测年度, 预测净利润, 预测EPS, 预测营业收入,
#          评级(买入/增持/中性), 机构名称, 预测日期

# Earnings performance / express report (业绩快报)
express = ak.stock_yjkb_em(symbol="000001")
# Shows actual vs forecasted earnings

# Performance forecast (业绩预告)
perf_forecast = ak.stock_yjyg_em(symbol="000001")
# Shows expected profit range, yoy change
```

## Dividend History (分红送转)

```python
# Historical dividend data
dividend = ak.stock_zh_a_dividend_em(symbol="000001")
# Columns: 公告日, 分红方案, 股权登记日, 除权除息日, 派息日
# Shows cash dividend per share, stock dividend ratio
```

## Institutional Holdings (机构持仓)

```python
# Institutional holdings overview
holdings = ak.stock_institute_hold_em(symbol="000001")
# Columns: 报告期, 机构数, 持仓量, 持仓市值, 占流通股比例

# Top 10 shareholders
top10 = ak.stock_shareholder_top10_em(symbol="000001")
# Columns: 股东名称, 持股数量, 持股比例, 股份类型, 变动方向

# Central bank / Social security fund holdings
social = ak.stock_institute_hold_detail_em(symbol="000001")

# Fund holdings of this stock
fund_hold = ak.stock_fund_hold_em(symbol="000001")
```

## Institutional Research Visits (机构调研)

```python
# Institutional research visit records
visits = ak.stock_institute_visit_em(symbol="000001")
# Shows which institutions visited, date, main topics discussed
# Useful to gauge institutional interest
```

## Profitability Analysis Helper

```python
def analyze_quarterly_profitability(symbol: str) -> dict:
    """Analyze quarterly profitability trends."""
    import akshare as ak

    info = ak.stock_individual_info_em(symbol)
    income = ak.stock_financial_income_statement_by_report_em(symbol)

    # Latest 4 quarters
    recent = income.head(4)

    # Calculate yoy growth
    if len(income) >= 8:
        yoy_revenue_growth = (recent.iloc[0]["营业收入"] / income.iloc[4]["营业收入"] - 1) * 100
        yoy_profit_growth = (recent.iloc[0]["净利润"] / income.iloc[4]["净利润"] - 1) * 100
    else:
        yoy_revenue_growth = None
        yoy_profit_growth = None

    return {
        "company_name": info.loc[info["item"] == "股票简称", "value"].values[0],
        "industry": info.loc[info["item"] == "行业", "value"].values[0],
        "market_cap": info.loc[info["item"] == "总市值", "value"].values[0],
        "pe_ratio": info.loc[info["item"] == "市盈率-动态", "value"].values[0],
        "latest_revenue": recent.iloc[0]["营业收入"],
        "latest_profit": recent.iloc[0]["净利润"],
        "latest_eps": recent.iloc[0]["基本每股收益"],
        "yoy_revenue_growth": yoy_revenue_growth,
        "yoy_profit_growth": yoy_profit_growth,
    }
```

## Valuation Metrics (估值指标)

The following can be extracted from `stock_zh_a_spot_em()` or `stock_individual_info_em()`:

| Metric | Description | Interpretation |
|--------|-------------|---------------|
| 总市值 | Total market cap | Large >100B, Mid 10-100B, Small <10B |
| 市盈率(动态) | PE TTM | Value <15, Average 15-30, Growth >30 |
| 市净率 | PB | Low <1.5, Medium 1.5-5, High >5 |
| 市销率 | PS | Revenue-based valuation |
| 市现率 | PCF | Cash flow-based valuation |
| 每股收益 | EPS (basic) | Higher = more profitable per share |
| 每股净资产 | BVPS | Book value per share |
| 净资产收益率 | ROE | >15% = excellent, >10% = good |
| 毛利率 | Gross margin | Higher = stronger pricing power |
| 净利率 | Net margin | Higher = more efficient operations |
