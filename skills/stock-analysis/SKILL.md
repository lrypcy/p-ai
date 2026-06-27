---
name: stock-analysis
description: "China & Hong Kong stock market analysis skill. Provides data acquisition, technical analysis, and market research for A-shares (沪深), Hong Kong stocks (港股), and related markets using AKShare (free, no API key). Use when the user asks to: analyze stocks, fetch K-line data, compute technical indicators, research A-share/HK market trends, screen stocks by conditions, check north-bound/south-bound capital flows, or perform quantitative analysis on Chinese equity markets."
---

# Stock Analysis: China & Hong Kong Markets

## Core Principle

**ALL stock analysis MUST produce an interactive ECharts HTML report.** This applies **regardless of whether the user explicitly asked for a report** — every "analyze stock X", "what's the outlook for Y", or "who are Z's customers" request generates an ad-hoc Python report script, runs it, and outputs an HTML file. No plain text answers, no markdown tables.

**输出位置：** 用户未指定路径时，统一存放到当前目录 `reports/stocks/{symbol}/`。

## Overview

This skill enables data-driven analysis of China A-shares (上海/深圳/北京交易所) and Hong Kong stocks (HKEX). It leverages **AKShare** — a free, open-source Python library (20k+ GitHub stars) — to fetch real-time quotes, historical K-lines, financial statements, capital flow data, and macro indicators. No API keys or registration required.

**Core data source**: AKShare (`pip install akshare`) aggregates data from East Money, Sina Finance, Xueqiu, and other public Chinese financial portals.

## Quick Start

```python
import akshare as ak

# A-share daily OHLCV (前复权)
df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                        start_date="20240101", end_date="20260101", adjust="qfq")

# Hong Kong stock daily OHLCV
df_hk = ak.stock_hk_hist(symbol="00700", period="daily",
                          start_date="20240101", end_date="20260101", adjust="qfq")

# Real-time A-share market quotes (all stocks)
spot = ak.stock_zh_a_spot_em()
```

## Task Categories

### 1. Data Acquisition

Select the reference file based on market:

| Market | Reference | Key Functions |
|--------|-----------|---------------|
| A-shares | `references/a-share.md` | `stock_zh_a_hist`, `stock_zh_a_spot_em`, `stock_zh_a_hist_min_em` |
| A-share bid/ask & 委比 | `references/a-share.md` (Order Book section) | `stock_bid_ask_em` |
| A-share live intraday | `references/a-share.md` (Live Intraday section) | `stock_zh_a_live_em`, `stock_intraday_sina` |
| A-share company news | `references/a-share.md` (Company News section) | `stock_news_em`, `stock_comment_detail_scrd_focus_em` |
| Hong Kong | `references/hk-stock.md` | `stock_hk_hist`, `stock_hk_spot_em`, `stock_hk_hist_min_em` |
| HK fundamentals | `references/hk-stock.md` (HK Fundamentals section) | `stock_hk_individual_info_em`, `stock_zh_ah_premium_em` |
| HK financial reports | `references/hk-stock.md` (HK Financial Reports section) | `stock_hk_financial_*_by_report_em` |
| Macroeconomics | `references/market-analysis.md` | `macro_china_*`, `stock_em_hsgt_*` |

### 2. Technical Analysis

See `references/technical-indicators.md` for calculations including:
- Moving averages (MA), MACD, RSI, KDJ
- Bollinger Bands, ATR
- Volume-based indicators
- `scripts/calc_indicators.py` for reusable computation

### 3. Company Fundamentals

See `references/company-fundamental.md` for:
- Company profile — name, industry, city, employee count, business scope
- Quarterly financial statements — income statement, balance sheet, cash flow
- Profitability analysis — ROE, EPS, revenue/profit trends, YoY growth
- Dividend history and institutional holdings
- Valuation metrics — market cap tiers, PE/PB interpretation
- **客户结构分析 → 详见 Section 6 🏭 客户结构分析（必须）**

### 4. Market Analysis & Workflow

See `references/market-analysis.md` for:
- North-bound / South-bound capital flow through Stock Connect (沪深港通)
- Sector capital flow analysis (板块资金流向)
- Top stocks screener
- Market sentiment and news analysis
- **Comprehensive scoring system** — technical (40%) + fundamental (40%) + sentiment (20%)
- **Buy/Hold/Sell recommendation engine** with confidence levels

### 5. Company IR Website Scraping — 财报/澄清/重要公告

In addition to financial data APIs, scrape the company's official investor relations (IR) website to get official, first-hand information (最新财报、澄清公告、业绩预告、重大合同、股权激励、分红送转等) not yet reflected in aggregated data sources.

**Why this matters:**
- Financial APIs (AKShare / East Money) can be 1-2 quarters behind for qualitative info
- Company announcements only appear on official IR pages first
- Cross-reference official data with API data to detect discrepancies

**What to scrape:** IR → 业绩公告（最新财报）、公告（澄清/重大合同/股权激励）、投资者关系（问答/纪要）、利润分配（分红方案）。

**How to find IR pages:** Search `site:{company_domain} 投资者关系` or use common patterns: `www.{pinyin}.com.cn/tzzgx/` (SH), `www.{pinyin}.com/investor/` (SZ), `www.{company}.com/en/investors/` (HK). Use `requests` + `BeautifulSoup` or OpenCode's `webfetch` tool.

**When to use:** Always for single-stock deep-dive; for chain-level analysis (many stocks), prioritize top 3-5 companies.

### Available Scripts（参考用 — 不得直接执行，见下方 🐍 脚本生成规范）

| Script | Purpose |
|--------|---------|
| `scripts/fetch_kline.py` | Batch fetch K-line data for multiple symbols |
| `scripts/calc_indicators.py` | Compute technical indicators from OHLCV |
| `scripts/stock_report.py` | Comprehensive one-stock analysis report (HTML/JSON) |

⚠️ These are **reference implementations only**. Each analysis must generate an ad-hoc script per the spec below.

### 🐍 脚本生成规范（MANDATORY — 按需生成，不调用预置脚本）

**每次个股分析生成一个独立的 ad-hoc Python 脚本到输出目录，再运行它。** 不得直接执行 `scripts/` 下的预置脚本。

#### 📁 输出目录规范

未指定输出路径时，在当前目录创建 `reports/stocks/{symbol}/`：

```
reports/stocks/{symbol}/
├── scripts/generate_{symbol}_report.py
├── data/{kline,indicators,fundamentals,short_term_outlook,customer_analysis}.json
└── {symbol}_{name}_分析报告.html
```

目录用 `os.makedirs(path, exist_ok=True)` 自动创建。如果用户指定了 `--output`，在指定路径同级创建 `scripts/` 和 `data/`。

#### 脚本结构规范

```python
#!/usr/bin/env python3
"""generate_{symbol}_report.py — {symbol} {name} 个股分析报告"""

import sys, os, json
import akshare as ak
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(STOCK_DIR, "data")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
SKILL_DIR = os.path.join(PROJECT_ROOT, '.agents', 'skills', 'stock-analysis')
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
os.makedirs(DATA_DIR, exist_ok=True)

# ── 1. 获取数据 ──
# kline = ak.stock_zh_a_hist(symbol, ...)
# info = ak.stock_individual_info_em(symbol)
# 保存到 data/kline.json / data/fundamentals.json

# ── 2. 计算技术指标 ──
# MA / MACD / RSI → 保存到 data/indicators.json

# ── 3. 短期走势分析 ──
# 近一日/近一周/未来一周 → 保存到 data/short_term_outlook.json

# ── 4. 客户结构分析 ──
# 网络搜索 + 年报 → 保存到 data/customer_analysis.json

# ── 5. 构建 HTML ──
# 使用 ECharts 交互式图表

# ── 6. 写入 HTML ──
output_path = os.path.join(STOCK_DIR, "{symbol}_{name}_分析报告.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ 报告已生成: {output_path}")
print(f"📁 脚本: {__file__}")
print(f"📁 中间数据: {DATA_DIR}/")
```

**禁止：** 硬编码行情数据（必须实时获取）、写死 CSS 样式（如需共用参考 chain-analysis 的 `html_theme.py` 模式）。

### 6. 🏭 客户结构分析（重要客户 / 供应链定位）（MANDATORY）

**每只个股的分析必须包含其客户结构分析**，说明该公司打入了哪些公司的供应链、主要客户是谁、客户集中度如何。这是判断该公司在产业链中话语权和发展潜力的关键维度。

**为什么重要：**
- 客户质量反映了公司的产品力和行业地位（如打入苹果/特斯拉/英伟达供应链 vs 只服务小厂商）
- 客户集中度影响经营风险（过度依赖单一大客户 = 高风险）
- 客户结构变化是股价的先行指标（新获得大客户 = 增长信号，丢失大客户 = 预警信号）
- 结合 chain-analysis skill，同一产业链内上下游客户关系可以交叉验证

#### 数据来源与采集方法

| 方法 | 说明 | 优先级 |
|------|------|--------|
| **网络搜索** | 通过 `websearch` 搜索 `"{公司名} 客户"`、`"{公司名} 打入 供应链"`、`"{公司名} 主要客户"`、`"{公司名} 供货"` 等关键词 | ⭐ 首选 — 覆盖最新动态 |
| **公司年报/公告** | 搜索公司年报中"前五大客户"章节（上市公司必须披露前五大客户销售额及占比） | ⭐ 必做 — 权威数据 |
| **IR 投资者关系页面** | 见 Section 5，客户信息通常在"业务概览"或"公司简介"中 | ✅ |
| **行业研报** | 搜索 `"{公司名} 研报 客户"`，券商报告常有大客户及份额分析 | ✅ |
| **供应链新闻** | 搜索 `"{公司名} 获得 订单"`、`"{公司名} 成为 供应商"`、`"{公司名} 供应链"` | ✅ |

#### 分析框架（报告输出内容）

每个个股分析报告必须包含以下客户分析内容：

```
┌──────────────────────────────────────────────────┐
│  🏭 客户结构分析                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  主要客户（Top 3-5）                               │
│  ┌──────────┬──────────┬────────┬──────────────┐ │
│  │ 客户名称  │ 所属行业  │ 收入占比 │ 合作关系说明  │ │
│  ├──────────┼──────────┼────────┼──────────────┤ │
│  │ 客户A     │ 消费电子  │ 25%    │ 长期供应商    │ │
│  │ 客户B     │ 新能源车  │ 15%    │ 2025年新进入  │ │
│  │ 客户C     │ 半导体    │ 10%    │ 通过认证阶段  │ │
│  └──────────┴──────────┴────────┴──────────────┘ │
│                                                  │
│  客户集中度：Top 3 占比 50% → 中度集中           │
│  风险提示：对客户A 依赖度较高(25%)                │
│                                                  │
│  供应链定位：                                     │
│  ▸ 该公司的产品/服务在客户产业链中的位置           │
│  ▸ 是否独家供应商？竞争壁垒如何？                   │
│  ▸ 客户切换成本高/低？                             │
│                                                  │
│  客户结构变化（近期动态）：                         │
│  ▸ 2026Q1: 新进入客户B供应链，预计年增收 2 亿      │
│  ▸ 2025Q4: 获得客户A 二期订单，份额从 15%→25%    │
│                                                  │
│  与产业链分析的交叉验证：                           │
│  ▸ 该公司在 chain-analysis 中归入"XX环节"         │
│  ▸ 其客户多为该环节的"下游"企业                    │
│  ▸ 上下游关系与产业链拓扑一致/存在差异             │
└──────────────────────────────────────────────────┘
```

#### 必须回答的 5 个问题

| # | 问题 | 具体要求 |
|---|------|---------|
| 1 | **主要客户是谁？** | 列出 Top 3-5 客户的名称、所属行业、收入占比。数据尽量从公司年报/公告获取，也可通过网络搜索交叉验证 |
| 2 | **打入了哪些知名公司的供应链？** | 这是最重要的切入点。明确说明：是否进入苹果/特斯拉/英伟达/华为/比亚迪/宁德时代等知名龙头的供应链？何时进入？供应什么产品/服务？份额如何？**如有新闻佐证必须引用** |
| 3 | **客户集中度如何？风险高吗？** | 前五大客户收入占比 <30% = 分散低风险，30-50% = 中度集中，>50% = 高度依赖需警惕。若依赖单一大客户 >30% 必须标注风险 |
| 4 | **客户结构近期有什么变化？** | 近一年是否有新增大客户？是否丢失了重要客户？客户订单是否在增长/萎缩？ |
| 5 | **该公司在客户供应链中的定位和壁垒？** | 是核心供应商还是备选？是否有技术/认证壁垒（如车规认证、苹果 MFi 认证）？客户切换成本高不高？ |

#### 与 chain-analysis 的联动

当在产业链分析（chain-analysis）中调用个股分析时，客户结构分析必须与产业链拓扑图交叉验证：
- 该公司的客户是否对应产业链的下游环节？
- 上下游关系在产业链拓扑中是否合理？
- 如果客户不在产业链公司列表中，说明该公司可能覆盖了更广的领域

#### 在 HTML 报告中的呈现

- 客户结构分析放在**基本面卡片之后、短期走势分析之前**，作为"业务深度"板块
- 用表格展示 Top 客户：客户名（可点击链接到对应公司的个股分析卡，如有）、行业、收入占比、合作时间、供应产品
- 知名客户用 🏆 标记，新进入客户用 🆕 标记，流失客户用 ⚠️ 标记
- 客户集中度用柱状图或饼图可视化
- **必须引用数据来源**：年报披露、新闻报道、研报等，不可凭空编造客户信息

### 7. 📈 短期走势分析（近一日 / 近一周 / 未来一周）

**核心目标：** 对个股的近期走势和未来短期方向做出综合判断，**所有结论必须有数据支撑 + 网络信息交叉验证**，不能仅凭技术指标空泛判断。该分析适合放在个股深度分析报告的前部，作为"先看短期方向，再看长期价值"的导航。

#### 布局架构（三栏式）

```
┌─────────────────────────────────────────────────────────────┐
│  📈 短期走势分析（综合网络信息评价）                        │
├─────────────────┬───────────────────┬───────────────────────┤
│  近一日走势      │  近一周走势        │  未来一周展望          │
│  Yesterday/Today │  Past Week         │  Next Week Outlook    │
├─────────────────┼───────────────────┼───────────────────────┤
│  ▸ 当日涨跌幅     │  ▸ 周涨跌幅        │  ▸ 关键价位            │
│  ▸ 成交量异动     │  ▸ 周K线形态       │   支撑位 / 阻力位      │
│  ▸ 资金流向       │  ▸ 行业板块对比    │  ▸ 即将发生事件        │
│   主力净流入/流出  │  ▸ 一周新闻时间线   │   业绩披露/解禁/分红    │
│  ▸ 关键新闻       │  ▸ 北向/南向资金   │  ▸ 板块催化剂/风险     │
│   盘前/盘后重大事件│  ▸ 技术指标信号    │  ▸ 网络情绪评价        │
│  ▸ 分时图异动节点  │   MACD/RSI周线    │   新闻舆情/股吧/研报   │
│                   │                    │                       │
│  ═══════════════  │  ════════════════  │  ═══════════════════  │
│  综合判断 ↴        │                    │  综合展望 ↴           │
│  偏多/偏空/震荡    │                    │  上涨/下跌/震荡 + 概率 │
└─────────────────┴───────────────────┴───────────────────────┘
```

#### 各栏位详细数据要求

##### 栏 1：近一日走势

| 数据项 | 来源 | 说明 |
|--------|------|------|
| 当日涨跌幅 & 成交量 | `stock_zh_a_spot_em` / Tencent API | 相比前 5 日均量判断是否放量/缩量 |
| 日内分时走势 | `stock_intraday_sina` 或 `stock_zh_a_hist_min_em` (5min) | 标注关键时间点的拉升/跳水 |
| 资金流向 | `stock_individual_fund_flow` (个股资金流) | 主力净流入/超大单/大单/中单/小单分布 |
| 最新新闻 | `stock_news_em` / 网络搜索 | 当日或盘后最新 3-5 条重要新闻，标注正面/负面/中性 |
| 龙虎榜 (如有) | `stock_lhb_detail_em` | 游资/机构买入卖出情况 |
| 委比/盘口 | `stock_bid_ask_em` | 实时买卖盘力度对比 |

**近一日综合判断：** 根据以上数据给出结论 → 强势/弱势/震荡，用 emoji 标识（🔥强势 / ⚠️弱势 / ➡️震荡）

##### 栏 2：近一周走势

| 数据项 | 来源 | 说明 |
|--------|------|------|
| 周涨跌幅 & 周成交量 | `stock_zh_a_hist` 取最近 5 个交易日 | 对比前一周的量价变化 |
| 周 K 线形态 | 5 日 K 线合并判断 | 阳包阴/乌云盖顶/十字星/突破等形态识别 |
| 行业板块同期表现 | `stock_board_industry_hist_em` | 该股所属行业板块周涨跌幅，对比个股是否跑赢板块 |
| 一周重要公告/新闻 | `stock_news_em` + 网络搜索 | 按时间线列出本周重要事件 |
| 资金周度变化 | `stock_individual_fund_flow` 按日汇总 | 本周每日主力净流入合计 vs 上周 |
| 北向/南向资金 | `stock_hsgt_north_net_flow_in_em` (如适用) | 北向资金本周对该股的持股变化 |
| 技术指标 | `calc_indicators.py` 或手动计算 | MACD 金叉/死叉、RSI 超买/超卖、KDJ 信号 |

**近一周综合判断：** 该股本周相对于大盘和板块的表现评级 → 领涨/跟涨/滞涨/领跌

##### 栏 3：未来一周展望

| 数据项 | 来源 | 说明 |
|--------|------|------|
| 关键支撑/阻力位 | 最近 20-60 日 K 线高低点 + 均线位置 | MA5/MA10/MA20/MA60 及前高前低 |
| 即将发生的事件 | `stock_comment_detail_scrd_focus_em` + 网络搜索 | 业绩预告披露日、股东大会、解禁日、除权除息、机构调研等 |
| 板块催化剂 | 行业新闻、政策动态、研报摘要 | 该板块未来一周是否有政策/事件催化 |
| 网络情绪评价 | 综合新闻舆情 + 股吧热度 + 研报评级变化 | **必须包含以下三个维度的交叉验证：**<br>① **新闻舆情** — 搜索近 3 日公司相关新闻，统计正面/负面/中性比例<br>② **股吧/论坛情绪** — 搜索股吧/雪球等平台讨论热度及情绪倾向（可通过网络搜索关键词 `"{股票名称} 股吧 讨论"` 或 `"{股票名称} 雪球"` 获取样本）<br>③ **研报评级变化** — 近一周是否有券商发布研报、评级上调/下调/维持 |
| 技术面预测 | 基于当前技术指标推演 | 若 RSI 超买+放量滞涨 → 回调风险；若 MACD 金叉+放量突破 → 上涨延续 |
| 综合展望 | 上述所有维度的加权汇总 | **明确结论 + 概率**：如"未来一周震荡偏多（65%概率上涨），关键看能否站稳 MA60" |

#### 网络信息评价的具体实施方法

**不能只依赖财务数据，必须主动搜索网络信息来交叉验证。** 具体做法：

```python
# 伪代码流程
def synthesize_short_term_outlook(symbol: str, name: str):
    # 1. 获取技术数据
    df_daily = ak.stock_zh_a_hist(symbol, period="daily", ...)  # 近一周K线
    df_min = ak.stock_zh_a_hist_min_em(symbol, period="5")       # 近一日分钟线
    fund_flow = ak.stock_individual_fund_flow(stock=symbol, market="sh")  # 资金流向
    
    # 2. 获取新闻和网络信息（通过 websearch 工具）
    news_results = websearch(f"{name} {symbol} 最新新闻 公告 2026")
    sentiment = analyze_news_sentiment(news_results)  # 正面/负面/中性
    
    # 3. 获取板块表现
    board_info = ak.stock_board_industry_hist_em(symbol=所属板块, ...)
    
    # 4. 综合判断
    outlook = {
        "one_day": { "trend": "...", "reason": "...", "confidence": "高/中/低" },
        "one_week": { "trend": "...", "reason": "...", "confidence": "高/中/低" },
        "next_week": { "outlook": "...", "probability": "65%", "key_levels": {...}, "risks": [...] },
    }
    return outlook
```

#### HTML 报告中的呈现规范

如果生成 HTML 报告，三栏用 CSS Grid 布局（`grid-template-columns: 1fr 1fr 1fr`），每栏独立卡片：

- 每栏标题行用该栏主题色：🔵近一日 = `#667eea` / 🟢近一周 = `#38a169` / 🟣未来一周 = `#9f7aea`
- 综合判断行用加粗 + 背景色高亮：上涨用 `#dcfce7` 绿底、下跌用 `#fee2e2` 红底、震荡用 `#fef3c7` 黄底
- 网络情绪部分用三个小指示灯：🟢正面偏多 / 🟡中性 / 🔴负面偏空
- 数据来源标注在每个数值右下角小字（如 "来源：东方财富"）

#### 与现有分析模块的关系

- **短期走势分析** 是现有基本面分析和技术分析的**补充和延伸**，不是替代
- 放在报告前部（总览之后、基本面之前），作为"短期方向导航"
- 如果短期展望与中长期基本面矛盾（如短期超买但基本面优秀），**必须明确指出矛盾并解释**

### Task Router Quick Reference

| User Request | Action |
|-------------|--------|
| "Analyze stock 000001" | 生成完整 HTML 报告（客户结构分析 + 短期走势分析）：在 `reports/stocks/000001/scripts/` 下生成 ad-hoc 脚本 → 运行 → 输出 HTML + 中间数据 |
| "000001 的客户有哪些 / 打入谁供应链" | 按客户结构分析(§6) 执行：网络搜索 + 年报查询 Top 客户、供应链定位、客户结构变化 |
| "000001 有没有打入苹果/特斯拉供应链" | 按客户结构分析搜索特定客户：`"{公司名} {客户名} 供应链 供应商"` |
| "short-term outlook / 短期走势 / 最近怎么看 000001" | 按短期走势分析(§7) 执行：获取近一日/近一周数据 + 网络信息搜索 → 合成三栏判断 → 输出 HTML |
| "未来一周 000001 怎么看" | 聚焦未来一周展望栏：关键价位、即将发生事件、网络情绪评价、综合展望 |
| "Buy or sell? / Recommend 000001" | 综合评估（基本面 + 短期走势 + 客户结构）→ 评分 → 输出 HTML |

## Important Notes

- **Data delay**: Real-time quotes from East Money have ~15s delay; Sina source ~3-15s
- **Rate limiting**: Frequent calls to Sina sources may trigger IP bans; prefer East Money sources (suffix `_em`) for reliability
- **Date format**: Historical queries use `YYYYMMDD` string format
- **Adjust flags**: `""` = no adjustment, `"qfq"` = forward-adjusted (前复权), `"hfq"` = backward-adjusted (后复权). For quantitative analysis, use `"hfq"`
- **Output directory**: 所有个股分析报告默认输出到当前目录 `reports/stocks/{symbol}/`；可使用 `--output` 指定自定义路径
- **Purpose**: All data is for academic research only; not investment advice
- **Installation**: `pip install akshare` (requires Python >= 3.9, 64-bit)

## References

- AKShare documentation: https://akshare.akfamily.xyz/
- AKShare GitHub: https://github.com/akfamily/akshare
