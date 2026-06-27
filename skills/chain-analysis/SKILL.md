---
name: chain-analysis
description: "Industrial chain analysis for Chinese equity markets. Covers semiconductor (半导体), storage/memory (存储产业链), new energy vehicle (新能源汽车), AI computing (AI算力+光互连) chains. ALL output MUST be interactive ECharts HTML reports with Chinese filenames. Provides chain scale/sizing with visual charts, upstream-downstream topology, core bottleneck identification (卡脖子), and key listed companies mapped to each chain node. Integrates with stock-analysis skill for company-level fundamental and technical deep-dive. Trigger when user asks to analyze a chain, generates HTML report."
---

# Chain Analysis — HTML Report Generator

## Core Principle

**ALL analysis output MUST be an interactive ECharts HTML report.** No plain text. No markdown tables. This applies **regardless of whether the user explicitly asked for a report** — every "analyze the X chain" or "what about Y chain" request generates an ad-hoc Python report script, runs it, and outputs an HTML file. 不得直接调用 skills/scripts/ 下的预置脚本来生成报告。

**报告文件名必须用中文。** 例如 `存储产业链.html` 而非 `storage_chain.html`。生成后告知用户路径并提示用浏览器打开。

**🚨 严格只生成用户指定的产业链。** 用户问"分析存储产业链"时，只执行 `--chain storage`；用户问"分析半导体产业链"时，只执行 `--chain semiconductor`。绝对不要同时生成其他产业链。每个请求只输出一个 HTML 文件。

**💡 支持任意产业链名称 — 不限于预定义列表。** 传入任何不在预定义列表中的链名称（如 `光伏`、`机器人`），系统会自动通过行业板块发现公司并生成报告。

**🚨 所有公司/市场数据必须实时采集，不得硬编码在脚本中。** 生成的脚本中通过 `import` 引入 `data_fetcher.py`（位于 `scripts/` 目录下）的 `discover_chain_companies()`（动态发现公司列表）+ `enrich_all()`（实时行情+K线+财务）或 `auto_discover_chain()`（任意链自动发现）来确保每次生成报告时数据准确有效。SECTOR_MAP / HIGHLIGHTS_MAP 作为产业分类观点模板可以保留，但公司代码和业务数据必须动态获取。

## 📐 产业链分析深度要求（MANDATORY — 8 个核心问题）

每个报告必须回答以下 8 个问题，贯穿总览概览和各细分环节。**分析要求**列定义分析深度，**报告呈现**列说明展示方式。

| # | 问题 | 分析要求 | 报告呈现 |
|---|------|---------|---------|
| 1 | 产业链有多大？分哪些环节？ | 定义上游→中游→下游全链路，标注各环节核心产品；全球+中国市场规模、CAGR | 仪表盘 9 宫格 + 市场规模图 + 一图流拓扑图（节点含国产化率🟢🟡🔴 + 国别缩写 + 卡脖子⚠️标识） |
| 2 | 全球竞争格局如何？ | 每个环节列出：领先国家/地区、对应全球龙头、市场份额或技术优势、进入壁垒。**必须做到"每个环节有国家/地区→公司映射"** | 全球竞争格局概览表（环节→国家→公司→份额），可用 ECharts 地图或热力图 |
| 3 | 哪些我们强？国产化率如何？ | 标注中国已形成优势的环节及全球份额、产能数据；对有国产替代的环节给出国产化率估算和替代进度（早期/中期/晚期）、与海外龙头的差距 | 各环节国产化率标识：🟢 >70% / 🟡 30-70% / 🟠 10-30% / 🔴 <10% |
| 4 | 卡脖子在哪里？ | 识别被卡环节：具体产品、垄断国家+公司+全球份额、有无国产替代及差距、断供风险。**必须区分"完全卡死"和"受限"** | 卡脖子全景雷达 + 海外垄断矩阵表（被卡环节→核心技术→垄断国家→公司→份额→国产替代现状）+ 瓶颈-公司暴露矩阵 |
| 5 | 龙头公司有哪些？市场集中度？ | Top N 排名（市值），计算 CR5 判断格局（寡头>60% / 中等30-60% / 分散<30%） | 水平条形图 Top 10 + 环形图 CR5 |
| 6 | 产业链财务画像如何？ | 按环节聚合：总市值、平均 PE、营收增速、毛利率、净利率、ROE；散点图展示营收-市值关系 | 分组柱状图 + PE 分布直方图 + 营收-市值散点 + 盈利能力图 + ROE 条形图 |
| 7 | 趋势怎么样？ | 利用 `qprofits` 展示 Top 6 多季度营收/利润走势 | 多季度折线图（判断上行/下行/分化） |
| 8 | 和哪些链关联？ | 上下游依赖链及关联方向 | 跨链导航列表 |

**两条数据线缺一不可：** 行业估算数据（回答"行业报告说多大"） + 实时公司数据（回答"实际上多大"）。

**数据来源要求：** 国产化率等优先从 Yole、IC Insights、TrendForce、行业白皮书、券商研报引用；无权威数据标注"估算"并说明依据。**严禁编造国产化率数字。**

## ⚠️ 核心原则：每家公司都必须有 Stock Analysis 深度分析

**产业链报告不直接生成任何个股分析内容。** 所有个股分析（K 线、技术指标、短期走势、客户结构、基本面等）**全部委托给 stock-analysis skill 完成**。chain-analysis 只负责：
1. 确定产业链拓扑、公司列表、卡脖子分析、国产化率等全链路内容
2. 对每家公司调用 stock-analysis 生成完整的个股分析 HTML
3. 将 stock-analysis 输出的 HTML 嵌入到产业链报告的各公司 Tab 中

### 工作流

```
chain-analysis (生成脚本)
  │
  ├── 1. 确定产业链拓扑 + 公司列表
  │     (discover_chain_companies / auto_discover_chain)
  │
  ├── 2. 生成产业链总览 HTML
  │     (15 个板块：仪表盘/市场结构/龙头排名/卡脖子雷达/跨链导航等)
  │
  ├── 3. 对每家公司 → 调用 stock-analysis skill
  │     │
  │     ├── 方式 A: 脚本中 import stock-analysis 模块，调用其函数生成个股 HTML 片段
  │     └── 方式 B: 执行 stock-analysis 的 stock_report.py 输出 HTML 文件
  │
  └── 4. 将 stock-analysis 输出的个股 HTML 嵌入产业链报告的各 Tab 页
        (每个公司一个独立 Tab，内容全部来自 stock-analysis)
```

### 🎯 总览 vs 个股的职责划分

**个股 Tab 必须嵌入 stock-analysis 生成的完整个股分析页面（含全部 sections：实时行情、K 线+4 指标、短期走势 3 列、客户分析 5 问、多季度财务、同花顺外链等），不得缩减为摘要卡片或提取部分字段。** 个股页面由 stock-analysis 全权负责，chain-analysis 只负责嵌入整合。

| 内容 | 由谁生成 | 说明 |
|------|---------|------|
| 产业链规模仪表盘 (9 宫格) | **chain-analysis** | 行业概览数据 |
| 市场结构分析图 (3 图) | **chain-analysis** | 市场规模、增速、价值分布 |
| 龙头公司市值排名 | **chain-analysis** | 链内 Top N 公司排名 |
| 细分环节实时数据聚合 | **chain-analysis** | 各环节市值/PE/营收对比 |
| PE 分布 / CR5 / 营收-市值矩阵 | **chain-analysis** | 全链财务画像 |
| 卡脖子全景雷达 + 暴露矩阵 | **chain-analysis** | 瓶颈分析专属 |
| 跨链依赖导航 | **chain-analysis** | 关联链列表 |
| **完整个股分析页面（含全部 section）** | **stock-analysis → 直接嵌入** | 与独立个股报告完全相同的 HTML 内容，逐公司嵌入 Tab 页 |

**关键原则：chain-analysis 生成的脚本中，个股 Tab 的内容必须来自 stock-analysis 的完整个股分析页面，嵌入时携带其全部 HTML/CSS/JS 结构。chain-analysis 不得在脚本中自行构造任何个股分析的 HTML 代码（K 线图、技术指标、短期走势、客户分析等），也不得对 stock-analysis 的输出做内容裁剪或摘要处理。**

### 实现方式

#### 方式 A（推荐）：chain-analysis 脚本中 import stock-analysis 模块，获取个股 HTML 片段

```python
# chain-analysis 生成脚本中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '.agents', 'skills', 'stock-analysis', 'scripts'))

from stock_analysis_core import generate_stock_card_html  # 假设 stock-analysis 提供此接口

# 对每家公司
company_tabs = ""
for comp in companies:
    code = comp["code"]
    # 调用 stock-analysis 生成该股的完整分析 HTML 片段
    stock_card_html = generate_stock_card_html(code)
    company_tabs += f'<div class="tab-content" id="tab-{code}">{stock_card_html}</div>'

# 总览 HTML + 各公司 Tab HTML → 拼成完整产业链报告
```

#### 方式 B：chain-analysis 脚本调用 stock-analysis 的 CLI 生成 HTML 文件，再加载嵌入

```python
import subprocess

STOCK_ANALYSIS_DIR = os.path.join(PROJECT_ROOT, '.agents', 'skills', 'stock-analysis')

for comp in companies:
    code = comp["code"]
    stock_outdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "stocks", code)
    os.makedirs(stock_outdir, exist_ok=True)
    
    subprocess.run([
        "python", f"{STOCK_ANALYSIS_DIR}/scripts/stock_report.py",
        "--symbol", code, "--html",
        "--output", f"{stock_outdir}/{code}_分析报告.html"
    ], check=True)
    
    # 读取生成的 HTML 文件内容，提取 <body> 部分嵌入产业链报告
    with open(f"{stock_outdir}/{code}_分析报告.html", "r", encoding="utf-8") as f:
        stock_html = f.read()
    # 提取 <body> 内容嵌入到对应 Tab
    company_tabs += f'<div class="tab-content" id="tab-{code}">{stock_body}</div>'
```

两种方式任选一种。**核心原则：chain-analysis 不自己编写任何个股分析的 HTML/JS 代码，全部从 stock-analysis 获取。**

### 必选功能清单（Chain Report 必须包含）

chain-analysis 负责生成的（总览内容）：

1. **产业链一图流** — 上游→中游→下游拓扑，含国产化率/卡脖子标识/国别缩写
2. **产业链规模仪表盘** — 9 宫格（全球市场、中国市场、CAGR、公司数、卡脖子数、平均进口依赖、总市值、平均 PE、平均营收增速）
3. **市场结构分析** — 市场规模图 + 增速对比 + 价值分布环图
4. **龙头公司市值排名** — ECharts 水平条形图 Top 10
5. **细分环节聚合** — 各环节市值/PE/营收增速/毛利率对比
6. **PE 分布 / CR5 / 营收-市值矩阵 / 盈利能力 / ROE 对比**
7. **卡脖子全景雷达 + 瓶颈暴露矩阵 + 跨链导航**
8. **全球竞争格局概览** — 领先国家/地区→公司映射表
9. **全报告公司名超链接互相跳转** — 所有公司名链接到对应股票 Tab
10. **调用 stock-analysis** — 对每家公司的个股分析 Tab 内容，通过调用 stock-analysis 生成并嵌入

stock-analysis 负责生成的（个股 Tab 内容）—— 必须嵌入完整个股分析页面，包含以下全部 section（与独立运行 stock-analysis 生成的个股报告完全相同）：

- **实时行情卡片** — 最新价、涨跌幅、市值、PE、换手率、行业位置
- **K 线图 + 4 指标网格** — K 线图 + MA 均线 + MACD 柱状图 + RSI + 成交量（4-grid ECharts）
- **短期走势 3 列布局** — 近一日/近一周/未来一周，每列含方向、涨跌幅、驱动因子(Short-term driver analysis)、胜率/赔率
- **客户结构 5 问分析** — 主要客户列表(集中度/C5)、供应链定位(是否绕不开)、客户质量(有支付能力)、客户趋势(增速/景气度)、替代风险
- **多季度财务趋势** — 营收/净利润/毛利率/ROE 多季度折线图
- **同花顺外链** — 一键跳转同花顺深度资料页
- 以上所有内容必须一次性由 stock-analysis 生成并返回，chain-analysis 不得分步调用多次获取不同片段

### 产业链报告 HTML 结构

```html
<!-- 总览 Tab（由 chain-analysis 生成） -->
<div class="tab-content active" id="tab-overview">
  <!-- 仪表盘、市场结构图、龙头排名、卡脖子雷达、全球竞争格局等 -->
</div>

<!-- 个股分析 Tab（每个公司一个，内容全部来自 stock-analysis） -->
<div class="tab-content" id="tab-600519">
  <!-- 由 stock-analysis 生成的个股分析 HTML -->
</div>
<div class="tab-content" id="tab-000001">
  <!-- 由 stock-analysis 生成的个股分析 HTML -->
</div>
```

### 参考实现

```python
import sys, os, json, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHAIN_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(CHAIN_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 项目根路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

# ── 1. 加载产业链数据 ──
sys.path.insert(0, os.path.join(PROJECT_ROOT, '.agents', 'skills', 'chain-analysis', 'scripts'))
from html_theme import CSS_COMMON, theme_css, THEMES
from data_fetcher import discover_chain_companies, enrich_all, CHAIN_TEMPLATES

# ── 2. 获取公司列表和实时数据 ──
companies = discover_chain_companies("storage")  # 示例链
enriched = enrich_all(companies)

# ── 3. 生成总览 HTML（chain-analysis 负责）──
overview_html = generate_overview_html(companies, enriched, ...)

# ── 4. 逐个调用 stock-analysis 生成个股 Tab 内容 ──
company_tabs = ""
for comp in companies:
    code = comp["code"]
    
    # 方式 B: 调用 stock-analysis CLI 生成独立 HTML
    stock_outdir = os.path.join(PROJECT_ROOT, 'reports', 'stocks', code)
    os.makedirs(stock_outdir, exist_ok=True)
    subprocess.run([
        "python", 
        f"{PROJECT_ROOT}/.agents/skills/stock-analysis/scripts/stock_report.py",
        "--symbol", code, "--html",
        "--output", f"{stock_outdir}/{code}_分析报告.html"
    ], check=True, capture_output=True)
    
    # 读取 stock-analysis 生成的 HTML
    with open(f"{stock_outdir}/{code}_分析报告.html", "r", encoding="utf-8") as f:
        stock_full = f.read()
    # 提取 stock-analysis 的 <style>（保证独立个股页面样式完整）和 <body> 内容
    import re
    styles = re.findall(r'<style[^>]*>.*?</style>', stock_full, re.DOTALL)
    stock_styles = "\n".join(styles)
    body_start = stock_full.find("<body>")
    body_end = stock_full.find("</body>")
    stock_body = stock_full[body_start+6:body_end] if body_start != -1 else stock_full
    # 将 stock-analysis 的样式包裹在 scoped div 中，避免污染产业链全局 CSS
    scoped_stock = f'<div data-stock-tab="{code}"><style>{stock_styles}</style>{stock_body}</div>'
    
    # 嵌入到产业链报告的个股 Tab（携带完整样式和内容）
    company_tabs += f'<div class="tab-content" id="tab-{code}">{stock_body}</div>'

# ── 5. 组装完整 HTML ──
html = f"""<!DOCTYPE html>
<html><head>
  <style>{CSS_COMMON}{theme_css(THEMES['storage'])}</style>
  <!-- Tab 切换 JS -->
</head><body>
  <div class="top-nav">
    <span class="cs active" onclick="switchTab('overview')">📊 总览</span>
    {" ".join(f'<span class="cs" onclick="switchTab(\'{c["code"]}\')">{c["name"]}</span>' for c in companies)}
  </div>
  <div class="tab-content active" id="tab-overview">{overview_html}</div>
  {company_tabs}
  <script>
    function switchTab(id) {{ /* tab 切换逻辑 */ }}
  </script>
</body></html>"""

output_path = os.path.join(CHAIN_DIR, "存储产业链.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ 产业链报告已生成: {output_path}")
```

这个参考实现中，**总览内容由 chain-analysis 生成，个股内容完全来自 stock-analysis 的输出**。两者通过 Tab 切换机制在同一个 HTML 中组织。

### ⚠️ 样式隔离：确保 stock-analysis 嵌入时样式完整且不冲突

嵌入 stock-analysis 的完整个股分析页面时，**除了提取 `<body>`，还必须提取其 `<head>` 中的 `<style>` 标签**，否则个股分析中的 ECharts 图表、布局、颜色等会全部丢失样式。处理方式：

1. **必须提取 stock-analysis 的 `<style>`** — 在参考实现的 step 4 中，使用正则提取所有 `<style>...</style>` 片段，拼接到 `<body>` 之前
2. **作用域隔离** — 将提取出的 stock-analysis 样式 + body 包裹在 `<div data-stock-tab="{code}">` 中。chain CSS 用 `:not([data-stock-tab])` 前缀确保不污染个股区域，stock-analysis 样式用 `[data-stock-tab="{code}"]` 前缀限定在各自 Tab 内（具体 scope 方式视 stock-analysis 的 CSS 复杂度而定；简单场景下可直接插入 `<style>` 标签，由 HTML 优先级规则保证正确渲染）
3. **CSS 变量覆盖** — stock-analysis 可能定义 `--accent` 等同名 CSS 变量。嵌入后其 `<style>` 应在 chain 的 `<style>` 之后加载，以保持 chain 主题优先级
4. **备用方案**：如果 CSS/JS 复杂度高导致样式隔离困难，可用 `<iframe>` 嵌入 stock-analysis 的独立 HTML 文件，天然隔离全部样式和脚本，但不支持跨框架 Tab 切换（需用 `postMessage` 通信）

**嵌入后的最终 HTML 结构：**

```html
<html>
<head>
  <style>/* chain 全局 CSS — 不受 stock-analysis 影响 */</style>
</head>
<body>
  <!-- 总览 Tab（chain-analysis 生成） -->
  <div class="tab-content active" id="tab-overview">...</div>

  <!-- 个股 Tab（每个公司一个，嵌入 stock-analysis 完整输出） -->
  <div class="tab-content" id="tab-600519">
    <div data-stock-tab="600519">
      <style>/* stock-analysis 为该股生成的样式，scope 在当前 Tab 内 */</style>
      <!-- stock-analysis 的 body 内容，含实时行情、K 线、短期走势 3 列、客户 5 问、财务趋势等 -->
    </div>
  </div>
  <div class="tab-content" id="tab-000001">...</div>

  <script>/* Tab 切换 JS */</script>
</body>
</html>
```

## 🐍 脚本生成规范（MANDATORY — 按需生成，不调用预置脚本）

**🚨 不得直接运行 `scripts/` 目录下的已有脚本来生成 HTML 报告。** 每次分析请求必须生成一个独立的、针对该产业链定制的 Python 脚本，放在输出目录中，再运行它。

### 为什么这样做？

1. **定制化需求** — 不同产业链的上游/中游/下游结构、数据维度和分析重点各不相同，一个通用脚本无法兼顾
2. **国产化率 / 卡脖子分析** — 这些分析需要针对每个产业链手动整理逻辑和数据来源，不能硬编码在通用脚本里
3. **可复现性** — 生成的脚本保留在输出目录，用户可自行重新运行或修改
4. **审计跟踪** — 每份报告对应一个生成脚本，逻辑完全透明

### 📁 输出目录规范

**如果用户没有指定输出目录，则在当前工作目录下创建 `reports/` 目录，并按以下结构存放本次分析的所有产物：**

```
reports/
├── 产业链分析/                     # 产业链分析统一目录
│   └── {chain_name}/               # 按产业链命名的子目录，如 存储/ 半导体/ PCB/
│       ├── scripts/                 # 生成的 ad-hoc Python 脚本
│       │   └── generate_{chain}.py
│       ├── data/                    # 中间数据（缓存的公司列表、行情快照等 JSON 文件）
│       │   ├── companies.json       # 链内公司列表
│       │   ├── enriched.json        # 实时行情+财务+K线快照
│       │   └── chain_definition.json
│       └── {chain_name}产业链.html  # 最终 HTML 报告
```

**目录创建规则：**
1. 使用 `os.makedirs(path, exist_ok=True)` 保证目录存在，不要依赖手动创建
2. 脚本自身放在 `reports/产业链分析/{chain}/scripts/` 下，HTML 和数据文件放在同级对应目录
3. 每次分析独立生成，**不应覆盖其他产业链的产物**
4. 如果用户指定了输出路径（如 `--output /some/path/report.html`），则尊重用户路径，但仍在该路径同级创建 `scripts/` 和 `data/` 子目录存放对应产物

### 脚本生成流程

```bash
# 1. 确定产业链定义和范围
# 2. 确定输出目录：用户指定 → 用指定路径；未指定 → 当前目录 reports/产业链分析/{chain}/
# 3. 创建目录结构：scripts/、data/、及 HTML 所在目录
# 4. 在 scripts/ 下生成 ad-hoc Python 脚本（命名：generate_{chain_id}_report.py，见下方脚本结构规范）
# 5. 脚本通过 import 引用 skills/scripts/ 下的共享模块（html_theme, data_fetcher）
# 6. 脚本中配置 stock-analysis 路径，通过 import 或 CLI 调用其个股分析能力
# 7. 脚本中包含该产业链特有的：链拓扑定义、国产化率数据、卡脖子分析、市场规模估算
# 8. 运行脚本：脚本内部对每家公司调用 stock-analysis 生成个股分析 HTML
# 8b. 提取 stock-analysis 输出 HTML 的 <body> 内容，嵌入产业链报告的各公司 Tab 页（参考下方参考实现的 Step 4）
# 9. 告知用户 HTML 文件路径、脚本路径、数据文件路径
```

### 脚本结构规范

生成的脚本必须遵循以下结构：

```python
#!/usr/bin/env python3
"""
generate_{chain_id}_report.py
生成 {chain_name} 产业链分析报告

Generated for: {user_request_context}
Generated at: {datetime}
"""

import sys
import os
import json

# ── 路径设置 ──
# 脚本路径: reports/产业链分析/{chain}/scripts/generate_{chain}.py
# 项目根: reports/产业链分析/{chain}/
# Skill 路径: <project>/.agents/skills/chain-analysis/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))             # reports/产业链分析/{chain}/scripts/
CHAIN_DIR = os.path.dirname(SCRIPT_DIR)                              # reports/产业链分析/{chain}/
DATA_DIR = os.path.join(CHAIN_DIR, "data")                           # reports/产业链分析/{chain}/data/
# 从 reports/产业链分析/{chain}/scripts/ 向上走 3 层到项目根，再进入 .agents/skills/chain-analysis/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  # 项目根目录
SKILL_DIR = os.path.join(PROJECT_ROOT, '.agents', 'skills', 'chain-analysis')
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

# ── 创建输出目录 ──
for d in [DATA_DIR]:
    os.makedirs(d, exist_ok=True)

from html_theme import CSS_COMMON, theme_css, THEMES
from data_fetcher import (
    CHAIN_TEMPLATES,
    discover_chain_companies,
    enrich_all,
    auto_discover_chain,
)

# ── 个股分析：配置 stock-analysis 路径（仅用于调用生成个股 HTML，不在 chain 中自行构造） ──
STOCK_ANALYSIS_DIR = os.path.join(PROJECT_ROOT, '.agents', 'skills', 'stock-analysis', 'scripts')
sys.path.insert(0, STOCK_ANALYSIS_DIR)

# ── 1. 产业链定义 ──
# 明确上下游拓扑、细分环节、核心产品
# 国产化率数据（标注来源，禁止编造）
# 卡脖子环节及严重程度

# ── 2. 实时数据获取 ──
# companies = discover_chain_companies("...")
# enriched = enrich_all(companies)

# ── 2b. 保存中间数据到 data/ 目录（便于调试和复用） ──
# with open(os.path.join(DATA_DIR, "companies.json"), "w", encoding="utf-8") as f:
#     json.dump(companies, f, ensure_ascii=False, indent=2)
# with open(os.path.join(DATA_DIR, "enriched.json"), "w", encoding="utf-8") as f:
#     json.dump(enriched, f, ensure_ascii=False, indent=2)

# ── 3. 构建 HTML（使用 html_theme 共享 CSS） ──
# ...

# ── 4. 写入 HTML 文件到 CHAIN_DIR（reports/产业链分析/{chain}/） ──
output_path = os.path.join(CHAIN_DIR, "{chain_name}产业链.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ 报告已生成: {output_path}")
print(f"📁 脚本: {__file__}")
print(f"📁 中间数据: {DATA_DIR}/")
```

### 可使用的共享模块（在 `scripts/` 下）

| 模块 | 用途 | 始终可用？ |
|------|------|-----------|
| `html_theme.CSS_COMMON` | 共享 CSS 设计系统 | ✅ 必须使用 |
| `html_theme.theme_css(theme)` | 主题色覆盖 | ✅ 必须使用 |
| `html_theme.THEMES` | 预定义主题色字典 | ✅ |
| `data_fetcher.discover_chain_companies(id)` | 按链 ID 发现公司列表 | ✅ |
| `data_fetcher.enrich_all(companies)` | 批量获取行情+K线+财务 | ✅ |
| `data_fetcher.build_stock_card_html(comp, enriched, sector_name)` | 个股分析卡 HTML | ✅ |
| `data_fetcher.auto_discover_chain(name)` | 任意产业链自动发现 | ✅ |
| `data_fetcher.CHAIN_TEMPLATES` | 产业链模板（含 segments、scale 等） | ✅ 参考用 |
| `data_fetcher.format_market_scale()` | 市场规模的字符串格式化 | ✅ |

### 脚本中必须 / 不得包含的内容

**必须包含：** 上方脚本模板已覆盖所有必要结构（文件头 + 路径配置 + 数据获取 + HTML 生成 + 路径告知）。生成脚本时遵循该模板即可。

**不得包含：**
1. **禁止硬编码公司行情数据** — PE、市值、股价等必须走 Tencent API 实时获取
2. **禁止直接复制大段已有脚本** — 可参考 `chain_report.py` 的模式，但必须根据当前产业链定制
3. **禁止在脚本中写死 CSS 样式** — 必须从 `html_theme` 导入共享 CSS

## ⚠️ 标签行规则（CRITICAL — 每个 HTML 只显示自己的标签）

**每个 HTML 报告的 `.cs-bar` 只显示当前产业链一个标签，不显示所有产业链选择器。** 用户只看一个链，不需要看到其他链的切换按钮。

```python
# ✅ 正确：只显示当前链
chain_label = f'<span class="cs active" style="cursor:default">{tmpl["icon"]} {tmpl["name"]}</span>'

# ❌ 错误：显示所有链的导航选择器
# chain_label = '<span class="cs">💾 存储</span><span class="cs">🔬 半导体</span>...' — 绝对禁止
```

---

### 总览 15 个核心板块（快速参考表）

| # | 板块 | 图类型 | 数据源 | 条件 | 一句话洞察 |
|---|------|--------|--------|------|-----------|
| 1 | 产业链规模仪表盘 | 9 宫格 HTML | 行业估算 + enriched | 始终 | 30 秒回答产业链有多大 |
| 2 | 市场结构分析 | 分组柱状图 + 柱状图 + 环图 | scale segments | 始终 | 全球 vs 中国各环节规模对比 |
| 3 | 龙头公司市值排名 | 水平条形图 Top 10 | Tencent mcap | 始终 | 谁最大？ |
| 4 | 细分环节实时聚合 | 分组柱状图/表 | enriched + segment | ≥2 segments | 哪个环节资本最看好/最赚钱/成长最快 |
| 5 | PE 分布直方图 | 柱状图 | company_stats pe | 始终 | 产业链整体估值分布（低估/泡沫） |
| 6 | 市场集中度 CR5 | 环形图 | company_stats mcap | 始终 | >60% 寡头 / 30-60% 中等 / <30% 分散 |
| 7 | 营收-市值矩阵 | 散点图 | company_stats | 始终 | 发现"营收大市值小"的潜在低估标的 |
| 8 | PE vs 成长矩阵 | 气泡散点 | company_stats | scatter 非空 | 成长股 vs 价值股 |
| 9 | 营收增速分布 | 环形饼图 | company_stats | 始终 | 高增长 vs 低增长占比 |
| 10 | 盈利能力分析 | 分组柱状图 | company_stats margin | ≥2 segments | 高附加值 vs 薄利多销环节 |
| 11 | ROE 对比 | 条形图 | company_stats roe | ≥2 segments | >15% 优质 / 8-15% 一般 / <8% 偏低 |
| 12 | 多季度营收趋势 | 折线图 Top 6 | qprofits | 有数据 | 上行周期/下行周期/分化 |
| 13 | 卡脖子全景雷达 | 雷达图 + 条形图 | CHAIN_ANALYSIS | bt_data 非空 | 整体卡脖子程度可视化 |
| 14 | 瓶颈-公司暴露矩阵 | 热力矩阵/文本 | bt + segment | bt_data 非空 | 哪些公司被哪些瓶颈卡 |
| 15 | 跨链依赖 & 导航 | HTML 列表 | CHAIN_ANALYSIS | 始终 | 关联链一览 |

**条件渲染规则：**
- bt_data 非空 → Layer 13 + Layer 14 + 时间线矩阵 + 瓶颈表
- scatter_data 非空 → Layer 8
- top_n 非空 → Layer 3 + Layer 9 + Layer 12
- seg_stats ≥2 segments → Layer 4 + Layer 10 + Layer 11

**实现参考：** 详细的 `company_stats` 构建、`seg_stats` 聚合、`trend_data` 多季度等数据准备代码见脚本模板（下方 🐍 脚本结构规范）。生成的脚本按此表对应数据源和条件调用 `data_fetcher` 模块即可。

### 主题色扩展

- 后 3 仪表盘用不同 top 边框色：`#38a169` / `#667eea` / `#e94560`
- 市场集中度 CR5 中心数字色：CR5>60% 用 `#e94560`，30-60% 用 `#f6ad55`，<30% 用 `#38a169`
- 营收-市值散点：对角线上方用 `#667eea`（溢价），下方用 `#e94560`（折价）
- 盈利能力对比：毛利率 `#667eea`，净利率 `#38a169`
- PE 分布柱状图颜色：`<0` 红色 `#e94560`，`15-30` 绿色 `#38a169`，其他用主题色
- 趋势折线图：前 6 家公司用色 `['#667eea','#e94560','#38a169','#f6ad55','#9f7aea','#63b3ed']`

## Task Router

| User Request | Action |
|-------------|--------|
| "分析下{XX}产业链" | 生成 `reports/产业链分析/{XX}/scripts/generate_{XX}_report.py` → 运行 → 输出 `reports/产业链分析/{XX}/{XX}产业链.html`（如 存储/半导体/新能源汽车/AI算力/光伏/机器人等） |
| "看看{XX}公司在这个链上的位置" | 在对应生成的脚本中添加该公司分析 → 重新运行 |
| "有哪些卡脖子环节" | 生成脚本中包含卡脖子章节 |
| "有哪些受益公司" | 生成脚本中包含公司表格章节 |

## 共享模块（scripts/ 目录下）

| 模块 | 用途 | 由谁引用 |
|------|------|---------|
| `scripts/html_theme.py` | 共享 CSS 设计系统 + 主题色定义，提供 `CSS_COMMON` / `theme_css()` / `THEMES` | 由生成的 ad-hoc 脚本 import |
| `scripts/data_fetcher.py` | 数据层：`discover_chain_companies()` / `enrich_all()` / `auto_discover_chain()` / `CHAIN_TEMPLATES` / `format_market_scale()`（⚠️ `build_stock_card_html()` 已弃用，个股 Tab 内容由 stock-analysis 生成） | 由生成的 ad-hoc 脚本 import |
| `scripts/chain_report.py` | 统一产业链报告生成器参考实现（**仅供阅读参考，不得直接调用**） | — |

## Data Context

- **Storage chain** (存储): DRAM/NAND晶圆制造(NOT listed), 芯片设计(兆易创新603986, 澜起科技688008, 北京君正300223, 东芯股份688110, 普冉股份688766), HBM先进封测(长电科技600584, 深科技000021, 通富微电002156), 存储模组(江波龙301308, 佰维存储688525, 德明利001309), 分销(香农芯创300475), 上游设备材料(中微公司688012, 拓荆科技688072, 华海清科688120, 芯源微688037, 华海诚科688535, 沪硅产业688126). 全球存储市场2026E ~$2,150B, AI驱动超级周期, DRAM合约价+90%+.

- **Semiconductor chain**: Full coverage of EDA/IP, equipment, materials, foundry, fabless IC design, memory, power semi, OSAT.

Source references stored in `references/` directory for additional detail. 注意：不得直接运行 `chain_report.py` 来生成报告，须生成 ad-hoc 脚本并按脚本生成规范执行。

## 🎨 统一风格规则（CRITICAL）

**所有 HTML 报告脚本必须共享 `html_theme.py` 中的设计系统，确保多报告生成时风格完全一致。**

### 核心规则

1. **CSS 必须来自 `html_theme.CSS_COMMON`** — 所有脚本不得自己写重复的 CSS，而是：
   ```python
   from html_theme import CSS_COMMON, theme_css, THEMES
   # 在 <style> 中：
   #   {theme_css(THEMES['chain_id'])}  — 主题色覆盖（CSS 变量）
   #   {CSS_COMMON}                       — 共享设计系统
   #   仅保留脚本特有的少量扩展
   ```

2. **主题色通过 CSS 变量控制** — 每个报告只设置 `:root { --accent: ...; --primary-from: ... }`，不写死任何颜色值

3. **现有主题定义在 `html_theme.THEMES` 中**：
   - `storage` — 深蓝 `#0a1628`
   - `semiconductor` — 深紫 `#0f0c29`
   - `new-energy-vehicle` — 深绿 `#0a2e1a`
   - `ai-computing` — 深紫 `#1a0a2e`
   - `glass_substrate` — 深紫 `#0f0c29`
   - `pcb` — 深蓝 `#0a1628`

4. **新增脚本不得自带独立 CSS** — 必须在 `<style>` 中优先引入 `theme_css()` + `CSS_COMMON`，再叠加脚本特有扩展

5. **CSS 类名遵守共享规范** — 不要发明新的类名体系，尽量复用（完整定义见 `html_theme.CSS_COMMON`）：
   - 区块: `.sec` / `.sec-hd` / `.sec-bd` / `.sec-desc`
   - 网格/卡片: `.sg`/`.si`/`.sl`+`.sv` | `.card-grid`/`.card-item` | `.co-card`/`.co-hd`/`.co-n`/`.co-c`/`.co-bd`
   - 图表: `.chart-box` / `.chart-box-sm`
   - 瓶颈/标签: `.bt-box`/`.bt-red`/`.bt-orange`/`.bt-yellow`/`.bt-green` | `.tag`/`.tag-red`/`.tag-orange`/`.tag-yellow`/`.tag-green`/`.tag-blue`
   - 导航/Tab: `.tab-content`/`.tab-content.active` | `.seg-nav`/`.sn`/`.top-nav`/`.cs-bar`/`.cs` | `.ctable` | `.co-link`/`.co-link-tag`

### 为什么要统一风格

- 用户同时看多份报告时，视觉一致性降低认知负担
- 减少冗余代码（原来 3 个脚本各自维护 100+ 行 CSS）
- 修改一处全局生效（颜色、间距、暗色模式等）
- 新增报告脚本只需定义数据 + 特有 HTML 结构，CSS 和 JS 从共享模块获取

## Important Notes

- Shared modules are in `scripts/` directory (html_theme.py, data_fetcher.py)
- **输出的目录结构：** 未指定输出目录时，在当前工作目录下创建 `reports/产业链分析/{chain}/`，其下分 `scripts/`（生成的脚本）、`data/`（中间数据 JSON）、及 HTML 文件
- **目录自动创建：** 生成脚本中使用 `os.makedirs(path, exist_ok=True)`，无需用户手动创建
- **三条产物路径都要告知用户：** HTML 报告路径 + 生成脚本路径 + 中间数据目录路径
- Python 依赖：生成的脚本需要 `akshare`（数据获取）、`pyecharts`（图表，如需在总览中直接使用 ECharts）。运行前确保 `pip install akshare pyecharts` 已执行。如果 stock-analysis 的 CLI 调用失败，也请确认 stock-analysis 侧依赖已安装
- Chain scale data from TrendForce/SIA/IC Insights — approximate, cross-check for precision
- Companies are mapped by primary revenue segment; some span multiple nodes
- Not investment advice
