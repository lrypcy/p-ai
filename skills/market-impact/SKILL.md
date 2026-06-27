---
name: market-impact
description: "Cross-market impact analysis: searches A-share (大A), Korean (KOSPI), and US (S&P 500/Nasdaq) market news, identifies which A-share sectors/industry chains are positively or negatively affected, and generates a structured HTML report with stock-analysis company deep-dives."
---

# Market Impact Analysis: Cross-Market Sentiment & Sector Impact

## Overview

This skill analyzes how events in **China A-shares (大A)**, **Korean stock market (KOSPI/KOSDAQ)**, and **US stock market (S&P 500/Nasdaq)** affect A-share sectors and industry chains, then generates a structured report with company deep-dives.

## Workflow

```
Search Market News → Identify Key Events → Map to A-Share Sectors → Classify Impact (利好/利空) → Company Deep-Dive → Generate Report
```

### Step 1: Search Market News

Search for the latest news across three markets:

| Market | Search Queries (examples) |
|--------|--------------------------|
| **A股 (大A)** | `A股 今日要闻 板块 资金流向`, `A股 热点板块 2026`, `沪深 重大政策` |
| **韩国股市** | `KOSPI 今日 半导体 出口`, `韩国 经济 政策 影响 A股`, `한국 증시 코스피` |
| **美股** | `S&P 500 sector performance`, `Nasdaq AI semiconductor`, `US China trade policy` |

Use `websearch` or equivalent search tools. Focus on:
- Macro events (interest rate decisions, trade policies, geopolitics)
- Sector-specific news (semiconductor, EV, AI, battery, solar, etc.)
- Major company earnings/guidance changes
- Supply chain disruptions or breakthroughs

### Step 2: Identify Key Events & Impact

For each market, extract:
- **Event**: What happened (e.g., "US announces new AI chip export restrictions")
- **Direction**: Positive or negative for which A-share sectors
- **Mechanism**: How the impact transmits (e.g., "price linkage", "supply chain", "competitive substitution", "policy spillover")

Common transmission channels:

| Channel | Description | Example |
|---------|-------------|---------|
| 价格联动 (Price linkage) | Commodity/raw material prices affect both markets | Oil, copper, lithium |
| 供应链 (Supply chain) | One market's company is supplier/customer | Korean semiconductor → Chinese smartphone |
| 政策外溢 (Policy spillover) | US policy impacts China directly | Export controls, tariff changes |
| 竞争替代 (Competitive substitution) | Companies in different markets compete | Chinese EV vs Korean battery |
| 情绪传导 (Sentiment contagion) | Risk-on/risk-off across global markets | Rate decisions, recession fears |
| 技术协同 (Technology synergy) | Cross-market tech collaboration | AI chip design → PCB manufacturing |

### Step 3: Map to A-Share Sectors

Build a sector impact matrix:

```python
# Data structure for sector impact
sectors = [
    {
        "name": "半导体 (Semiconductor)",
        "impact": "利好" or "利空" or "中性",
        "confidence": "高/中/低",
        "events": ["US export controls on AI chips to China", "Korean memory price recovery"],
        "mechanism": "供应链 · 政策外溢",
        "explanation": "US export controls accelerate domestic substitution (国产替代) in semiconductor equipment and EDA; Korean memory price recovery benefits Chinese packaging and testing companies.",
        "companies": [
            {"code": "002371", "market": "sz", "name": "北方华创", "reason": "半导体设备国产替代核心标的"},
            {"code": "688012", "market": "sh", "name": "中微公司", "reason": "刻蚀设备龙头"},
        ]
    },
    # ...
]
```

### Step 4: Classify Impact

For each sector, determine:
- **利好 (Bullish/Positive)**: A-share companies benefit from the event
- **利空 (Bearish/Negative)**: A-share companies are harmed
- **中性 (Neutral)**: Mixed or uncertain impact

Use evidence from the searched news to support each classification. Attach citation references.

### Step 5: Company Deep-Dive

For each sector, identify 2-5 key A-share listed companies. Use the `stock-analysis` skill to fetch their real-time data and financials:

```bash
# Reference: stock-analysis skill usage
python .agents/skills/stock-analysis/scripts/fetch_kline.py --symbols 002371,688012 --market a
```

The report generator script provides two modes:

#### Mode 1: From events JSON file

```bash
python .agents/skills/market-impact/scripts/market_impact_report.py \
    --events events.json \
    --output market_impact_report.html
```

#### Mode 2: Interactive AI-assisted (no JSON file needed)

```bash
python .agents/skills/market-impact/scripts/market_impact_report.py \
    --output market_impact_report.html
```

In Mode 2, the script will output prompts for the AI to fill in the market overview text and sector data interactively.

### Input Data Format (JSON)

The script reads an `events.json` file with this structure:

The script reads an `events.json` file with this structure:

```json
{
  "report_title": "跨市场影响分析报告: 2026-06",
  "report_date": "2026-06-26",
  "market_overview": {
    "a_share": "A股近期走势及热点...",
    "korea": "韩国股市近期动态...",
    "us": "美股近期动态..."
  },
  "sectors": [
    {
      "name": "半导体",
      "impact": "利好",
      "confidence": "高",
      "events": ["US export controls on AI chips"],
      "mechanism": "供应链 · 政策外溢",
      "explanation": "详细分析...",
      "companies": [
        {"code": "002371", "market": "sz", "name": "北方华创", "reason": "国产替代核心标的"}
      ]
    }
  ]
}
```

### Output

Generates an HTML report with:
- **Market overview** section for A/Korean/US markets
- **Sector impact matrix** (利好/利空/中性 with color coding)
- **Company deep-dive cards** with real-time data, financials, K-line charts, and news
- **Per-tab filtered references**
- **Clickable company links** (like PCB chain analysis report)

## Integration with Related Skills

| Skill | Usage |
|-------|-------|
| `stock-analysis` | Fetches real-time stock data, financials, K-line, and news for each mentioned company |
| `chain-analysis` | Provides industry chain topology context when analyzing sector impacts |

## Triggers

This skill activates when the user asks:
- "分析今天全球市场对A股板块的影响"
- "美股/韩国股市波动对A股哪些板块利好利空"
- "跨市场影响分析"
- "市场情绪对A股产业链的影响"
- "生成跨市场影响报告"
- "/market-impact"
