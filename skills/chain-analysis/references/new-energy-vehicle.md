# New Energy Vehicle Industrial Chain (新能源汽车产业链)

> Last updated: 2026-06-26 | Sources: CPCA, CAAM, BNEF, TrendForce, company annual reports

## Chain Scale

| Metric | China (2025) | Global (2025) | 2026E | 2027E | Growth Driver |
|--------|-------------|--------------|-------|-------|--------------|
| NEV sales (units) | 35M (65% penetration) | 45M | 50M+ | 55M+ | Cost parity, charging infra, mandating |
| NEV market value (sales) | ¥4.5T (~$620B) | ~$900B | ~$1.1T | ~$1.3T | Mix shift to higher-value EVs |
| Power battery installations | 750 GWh | 1,200 GWh | 1,500 GWh | 1,800 GWh | NEV growth + avg battery size ↑ |
| Battery market value | ¥600B (~$80B) | ~$120B | ~$150B | ~$170B | LFP dominance, slight margin recovery |
| Charging infrastructure | 4M+ piles | 8M piles | 12M piles | 16M piles | Gov't mandate, NEV-pile ratio 2:1 |

> **Core drivers**: Price parity with ICE reached (2024-2025), intelligent driving as differentiator, export push

## Chain Topology

```
上游（原材料）          中游（核心部件）           下游（整车+服务）
┌──────────────┐    ┌──────────────────┐   ┌───────────────────┐
│  锂资源       │    │   电池制造         │   │   整车制造          │
│  天齐/赣锋    │───▶│  宁德时代/比亚迪   │──▶│  比亚迪/理想/蔚来   │
│  盐湖股份     │    │  中创新航/国轩     │   │  小鹏/塞力斯/长城   │
├──────────────┤    ├──────────────────┤   ├───────────────────┤
│  钴资源       │    │   电机/电控        │   │   充电/换电         │
│  华友/寒锐    │───▶│  汇川/方正/英搏尔  │──▶│  特锐德/盛弘        │
├──────────────┤    ├──────────────────┤   ├───────────────────┤
│  镍资源       │    │   热管理系统       │   │   AD/ADAS           │
│  格林美/华友   │───▶│  三花/银轮/拓普    │──▶│  德赛西威/中科创达  │
├──────────────┤    ├──────────────────┤   ├───────────────────┤
│  正极材料      │    │   智能座舱         │   │   后市场/回收        │
│  容百/当升/德方  │──▶│  德赛/华阳/均胜  │──▶│  格林美/天奇         │
├──────────────┤    ├──────────────────┤   └───────────────────┘
│  负极材料      │    │   功率半导体       │
│  贝特瑞/杉杉   │───▶│  斯达半导/时代电气 │
├──────────────┤    └──────────────────┘
│  电解液       │
│  天赐/新宙邦   │
├──────────────┤
│  隔膜         │
│  恩捷/星源     │
└──────────────┘
```

## Detailed Segment Analysis

### 1. Lithium Battery Chain (锂电池产业链)

**Global battery market**: ~$120B (2025), ~$150B (2026E)
**China dominance**: ~70%+ of global cell production, ~85%+ of anode/electrolyte/separator

#### 1.1 Upstream Raw Materials (上游原材料)

| Material | Global Scale | China Import Dep. | Key China Players | Stock Code | 2025 Revenue |
|----------|-------------|-------------------|-------------------|-----------|-------------|
| **Lithium (Li)** | ~$20B | 60% imported (brine/ore) | **天齐锂业** | 002466 | ~¥20B |
| | | | **赣锋锂业** | 002460 | ~¥30B |
| | | | **盐湖股份** | 000792 | ~¥15B (KCl+Li) |
| **Cobalt (Co)** | ~$12B | 95%+ imported (DRC) | **华友钴业** | 600516 | ~¥70B (total incl. Ni) |
| | | | **寒锐钴业** | 300618 | ~¥5B |
| **Nickel (Ni)** | ~$35B | 85%+ imported | **华友钴业** | 600516 | Included above |
| | | | **格林美** | 002340 | ~¥35B (recycling+precursor) |

**Bottleneck**: 🔴 Lithium resource (60% import dependency, Australia/Chile dominated). Cobalt 95%+ from DRC — geopolitical risk.

#### 1.2 Battery Materials (四大主材)

| Material | Global Share | China Leader | Stock Code | Capacity (2025) | Key Advantage |
|----------|-------------|-------------|-----------|-----------------|---------------|
| **Cathode (正极)** | ~$40B | **容百科技** | 688005 | 200K TPA high-Ni | Global #1 high-Ni cathode |
| | | **当升科技** | 300073 | 150K TPA | High-Ni exports |
| | | **德方纳米** | 300769 | 300K TPA LFP | #1 LFP cathode, BYD supplier |
| | | **华友钴业** | 600516 | 400K TPA | Precursor + cathode integration |
| **Anode (负极)** | ~$15B | **贝特瑞** | 835185 | 400K TPA | Global #1 anode |
| | | **杉杉股份** | 600884 | 200K TPA | #2 global, artificial graphite |
| | | **璞泰来** | 603659 | 150K TPA | Integrated (anode+coating) |
| **Electrolyte (电解液)** | ~$12B | **天赐材料** | 002709 | 600K TPA | Global #1, 6F+LiFSI integration |
| | | **新宙邦** | 300037 | 200K TPA | #2, high-voltage electrolyte |
| **Separator (隔膜)** | ~$10B | **恩捷股份** | 002812 | 10B sqm | Global #1 wet separator |
| | | **星源材质** | 300568 | 5B sqm | Top 3 global |

**Bottleneck analysis (材料)**:
- 🟠 High-Ni cathode (NCM 9系) precursor technology: China advanced, global #1
- 🟢 LFP cathode: China dominates, little bottleneck
- 🟢 Anode: China dominates (>85% global supply)
- 🟡 Electrolyte LiFSI: 天赐leads, some patent barriers
- 🟡 Wet separator base film: 恩捷global #1, but高端涂覆膜仍有gap

#### 1.3 Battery Cell Manufacturing (电池制造)

**Global**: ~$80B cell revenue (2025)
**China dominance**: CATL alone ~35% global market share

| Company | Stock Code | 2025 Revenue | Capacity | Market Share | Key Clients |
|---------|-----------|-------------|----------|-------------|-------------|
| **宁德时代** | 300750 | ~¥450B | 700 GWh | 35% global, 45% China | Tesla, BMW, NIO, Xpeng, Geely |
| **比亚迪 (弗迪电池)** | 002594 | ~¥350B (auto incl.) | 350 GWh | 15% global | BYD self-use + external (Tesla, Toyota) |
| **中创新航** | 03931.HK | ~¥35B | 100 GWh | 5% global | GAC, Xpeng,长安 |
| **国轩高科** | 002074 | ~¥30B | 80 GWh | 4% global | VW (largest shareholder), NIO |
| **亿纬锂能** | 300014 | ~¥50B | 120 GWh | 3% global | BMW, Mercedes, JLR |
| **欣旺达** | 300207 | ~¥60B (total) | 80 GWh | 2% global | HEV/PHEV focus, Renault, Nissan |

**Bottleneck**: 🟢 China leads global battery cell manufacturing. Key gap: solid-state battery tech (丰田, Samsung SDI ahead).
**Solid-state timeline**: Semi-solid (CATL/国轩 2026-2027), full solid-state (2028+).

#### 1.4 Battery Recycling (电池回收)

| Company | Stock Code | Capacity | Technology |
|---------|-----------|----------|------------|
| **格林美** | 002340 | 250K TPA | Hydrometallurgical + precursor |
| **天奇股份** | 002009 | 100K TPA | Dismantling + recycling |
| **赣锋锂业** | 002460 | 100K TPA LCE | Battery-grade Li recycling |

### 2. NEV Components (关键部件)

#### 2.1 Drive Motor & Controller (电机电控)

| Company | Stock Code | Revenue | Product | Position |
|---------|-----------|---------|---------|----------|
| **汇川技术** | 300124 | ~¥80B (total) | NEV motor controller, SiC inverter | #1 in NEV电控 (>20% share) |
| **方正电机** | 002196 | ~¥8B | Drive motor, e-axle | Top 5 domestic |
| **英搏尔** | 300681 | ~¥6B | Motor + controller integrated | Mid-market NEV focus |
| **大洋电机** | 002249 | ~¥20B (total) | Drive motors, BSG | Diversified, NEV ~30% revenue |

**Bottleneck**: 🟡 SiC-based high-voltage (800V) drive inverter: 斯达半导/时代电气 rapidly catching up
**Trend**: 800V architecture → SiC MOS取代IGBT in main inverter (2026-2028)

#### 2.2 Thermal Management (热管理)

| Company | Stock Code | Revenue | Product | Position |
|---------|-----------|---------|---------|----------|
| **三花智控** | 002050 | ~¥30B (NEV) | Electronic expansion valve, cooling plate | Global #1 in NEV热管理组件 |
| **银轮股份** | 600218 | ~¥15B (NEV) | Battery cooling, heat pump | Top 3 domestic |
| **拓普集团** | 601689 | ~¥25B (NEV) | Integrated thermal module,底盘 | Vertically integrated chassis+tier1 |
| **盾安环境** | 002011 | ~¥5B (NEV) | Thermal expansion valve | Expanded from HVAC |

#### 2.3 Intelligent Chassis (智能底盘)

| Company | Stock Code | Product | Position |
|---------|-----------|---------|----------|
| **伯特利** | 603596 | EBP (电子制动助力), EPB | #1 in EPB domestic, wire control brake leader |
| **德赛西威** | 002920 | IPU01/IPU02 high-performance computing | #1 in ADAS domain controller |
| **中科创达** | 300496 | Smart cockpit OS, ADAS middleware | Software leader |
| **经纬恒润** | 688326 | ADAS controller, V2X | Tier 1 full stack |
| **华阳集团** | 002906 | HUD,座舱域控,电子外后视镜 | HUD #1 domestic |

### 3. NEV OEM (整车)

| Company | Stock Code | 2025 NEV Sales | Positioning | Key Advantage |
|---------|-----------|---------------|-------------|---------------|
| **比亚迪** | 002594 / 1211.HK | 5.5M | Full-range (¥7-100万) | Vertical integration, DM-i hybrid, Blade battery |
| **理想汽车** | 2015.HK / LI | 1.5M | Premium SUV (¥25-60万) | Range extender + pure EV, intelligent cabin |
| **蔚来** | 9866.HK / NIO | 0.5M | Premium (¥30-60万) | Battery swap, NIO House, NIO Phone |
| **小鹏** | 9868.HK / XPEV | 0.4M | Smart EV (¥15-40万) | XNGP (city ADAS), AI-driven |
| **塞力斯(AITO)** | 601127 | 0.6M | Premium (¥25-60万) | Huawei inside (ADS, HarmonyOS) |
| **长城汽车** | 601633 / 2333.HK | 1.0M | SUV/Pickup (¥10-40万) | Hi4 hybrid, Tank/Haval brands |
| **长安汽车** | 000625 | 1.5M | Mass-market (¥5-30万) | Deepal, Avatr, CHN cooperation |
| **广汽** | 601238 / 2238.HK | 0.9M | Mass+premium | Aion (埃安) pure EV, Hyper brand |
| **上汽** | 600104 | 1.2M | Mass-market | IM Motors (智己), export leader |

**Industry dynamics** (2025-2026):
- **Price war**: BYD DM-i 5.0 launched at parity with ICE; competitors forced to follow
- **Profitability**: Only BYD, 理想 are profitable in NEV. 蔚来/小鹏 still loss-making
- **Export surprise**: China exported 2.5M NEVs in 2025 (BYD led with 1M+ exports)
- **EU tariffs**: EU imposed 17.4-38.1% tariffs on Chinese EVs (2025), slowed but did not stop exports

### 4. Charging Infrastructure (充电基础设施)

| Company | Stock Code | Product | Position |
|---------|-----------|---------|----------|
| **特锐德** | 300001 | EV charging network (特来电) | #1 in public charging piles (25%+ share) |
| **盛弘股份** | 300693 | Charging module, supercharging station | Top 3 in charging module |
| **科士达** | 002518 | Charging pile, energy storage | Vertically integrated |
| **通合科技** | 300491 | Charging module (20-40kW) | Core power module supplier |

**Bottleneck**: 🟢 Charging infrastructure is not bottleneck — more a capex game. Grid capacity at peak is emerging bottleneck.

### 5. NEV Chain Summary — Bottleneck Map

| Bottleneck Item | Import Dep. | Key Barrier | China Alternative | Timeline |
|----------------|------------|-------------|-------------------|----------|
| **High-end SiC substrate** | 80% | Crystal growth yield (<60% vs W/S 80%+) | 天岳先进/天科合达 | 2027-2028 |
| **High-voltage IGBT7** | 50% | Design + process/IP | 斯达半导(7th gen in validation) | 2027 |
| **LiDAR SPAD array** | 70% | Sony独占 high-end SPAD | 禾赛/速腾(自研 chip) | 2026-2027 |
| **ADAS high-end SoC** | 90% | NVIDIA Drive Thor/Ori | 华为昇腾MDC, 地平线J6 | 2027+ |
| **Lithium resource** | 60% | Overseas mine control | 赣锋/天齐 overseas mine + recycling | Ongoing |
| **Solid-state battery** | Technology gap | 丰田/Samsung SDI领先 3-5年 | CATL/国轩 (semi-solid 2026) | 2028+ |

## Key Listed Companies by Segment

| Segment | Primary | Secondary | Tertiary |
|---------|---------|-----------|----------|
| Battery cell | 宁德时代 300750 | 比亚迪 002594 | 亿纬锂能 300014 |
| Lithium | 赣锋锂业 002460 | 天齐锂业 002466 | — |
| Cobalt/Nickel | 华友钴业 600516 | 格林美 002340 | — |
| Cathode | 容百科技 688005 | 德方纳米 300769 | 当升科技 300073 |
| Anode | 贝特瑞 835185 | 杉杉股份 600884 | 璞泰来 603659 |
| Electrolyte | 天赐材料 002709 | 新宙邦 300037 | — |
| Separator | 恩捷股份 002812 | 星源材质 300568 | — |
| Motor/Controller | 汇川技术 300124 | 方正电机 002196 | 英搏尔 300681 |
| Thermal Mgmt | 三花智控 002050 | 银轮股份 600218 | 拓普集团 601689 |
| Intelligent Chassis | 德赛西威 002920 | 伯特利 603596 | 经纬恒润 688326 |
| ADAS Software | 中科创达 300496 | — | — |
| NEV OEM | 比亚迪 002594 | 理想汽车 2015.HK | 塞力斯 601127 |
| Charging | 特锐德 300001 | 盛弘股份 300693 | — |
| Recycling | 格林美 002340 | 天奇股份 002009 | — |

## Cross-Chain Dependencies

- **NEV → Lithium Battery**: The only reason battery exists at this scale
- **NEV → Power Semiconductor**: IGBT/SiC per vehicle value ~¥2,000-5,000
- **NEV → Semiconductor (CIS)**: ADAS cameras drive CIS demand
- **NEV → AI Computing**: Autonomous driving compute power required
- **NEV → Charging Infra**: EV adoption and charging network are mutually reinforcing
