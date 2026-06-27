# Chain Analysis Methodology

## Analysis Framework

Every industrial chain analysis follows a structured 6-step framework:

### Step 1: Chain Definition & Boundary

Define the chain scope and segment it into upstream / midstream / downstream / adjacent sub-chains.

**Example — Semiconductor:**
```
上游 (Materials & Equipment) → 中游 (Design, Manufacturing, Packaging) → 下游 (Applications)
```

### Step 2: Market Sizing

For each segment, collect:
- **Global TAM** (Total Addressable Market) in USD/CNY
- **China market share** (% of global)
- **Growth rate** (CAGR 3Y/5Y)
- **Key drivers** (technology, policy, demand)

Data sources in priority order:
1. Industry associations (SIA, CPCA, CAAM, CFA)
2. Research firms (TrendForce, IC Insights, Gartner, IDC, Omdia)
3. Company annual reports (segment revenue → back-calculate market share)
4. Government white papers (工信部, NDRC)
5. Brokerage research (CICC, CITIC, Guotai Junan)

### Step 3: Topology Mapping

For each segment, map:
- **Value flow direction**: What inputs go into what processes
- **Cost structure**: Which segment captures the most value
- **Technology nodes**: Key processes and their criticality
- **Substitution paths**: Alternative technologies/materials

### Step 4: Bottleneck Identification (卡脖子)

For each chain, identify:
- **Items**: Specific materials, equipment, components, or software
- **Import dependency**: % of China's consumption that is imported
- **Self-sufficiency trajectory**: Current → 2027E → 2030E
- **Why it is hard**: Technical barriers, patent walls, certification cycles
- **Who is leading substitution**: Domestic companies with breakthroughs

Bottleneck severity classification:

| Level | Description | Import Dependency | Example |
|-------|-------------|------------------|---------|
| 🔴 Critical | No domestic substitute, complete import reliance | >90% | EUV lithography, high-end EDA |
| 🟠 Severe | Domestic options exist but far behind on performance | 50-90% | High-end光刻胶, 12-inch硅片 |
| 🟡 Moderate | Domestic options competitive at mature nodes | 20-50% | CMP materials, 8-inch silicon wafers |
| 🟢 Low | Domestic supply sufficient for most demand | <20% | 封装基板, 功率器件 (mature) |

### Step 5: Company Mapping

Map listed companies to each chain node.

For each company, record:
- **Stock code**: A-share (6-digit) or HK (5-digit)
- **Position in chain**: Which segment(s), specific product lines
- **Market share**: In its primary product category
- **Revenue dependency**: % of revenue from this chain
- **Competitive moat**: Technology, scale, customer lock-in, regulatory
- **Stock-analysis link**: Ready to be passed to `stock-analysis/stock_report.py`

### Step 6: Cross-Chain Dependencies

Identify how chains interlock:

```
Semiconductor → AI Computing (chips enable AI)
Lithium Battery → NEV (batteries enable EVs)
Semiconductor Equipment → Semiconductor (equipment enables fabs)
Advanced Packaging (Semiconductor) → AI Computing (HBM/Chiplet)
```

## Data Collection Procedure

When the user asks to analyze a chain:

```
1. Check if the chain is in our coverage (SKILL.md table)
2. Load the appropriate reference file
3. For latest data, use AKShare / web search to update:
   - Current stock prices of key companies
   - Recent quarterly earnings
   - News about policy/regulatory changes
   - Bottleneck breakthroughs
4. Generate report:
   - Structured text analysis (for quick reference)
   - Interactive HTML report (for presentation)
5. For individual companies, switch to stock-analysis skill
```

## Scoring a Chain Node

Each node in the chain can be scored on:

| Dimension | Weight | Metrics |
|-----------|--------|---------|
| Market Attractiveness | 25% | TAM growth rate, profit margins, barriers to entry |
| China Position | 20% | China market share, domestic firms' share, policy support intensity |
| Bottleneck Severity | 20% | Import dependency, tech gap years, number of substitute options |
| Investment Readiness | 20% | Number of listed A-share companies, market cap, liquidity |
| Growth Momentum | 15% | YoY growth, capacity expansion plans, demand tailwinds |

## Stock Deep-Dive Integration

When analyzing a specific company from chain context:

```python
# Pseudocode for the integration
def analyze_company_in_chain(chain_name, stock_symbol):
    # Step 1: Get chain context
    chain_data = load_chain_reference(chain_name)

    # Step 2: Find company's position in chain
    position = chain_data.find_company(stock_symbol)

    # Step 3: Run stock analysis (calls stock-analysis skill)
    stock_result = run_stock_report(stock_symbol)

    # Step 4: Combine into chain+stock composite view
    return {
        "chain_position": position,
        "bottleneck_relevance": position.bottleneck_score,
        "company_analysis": stock_result
    }
```

The `chain_report.py` script implements this integration automatically via `data_fetcher.enrich_all()`.
