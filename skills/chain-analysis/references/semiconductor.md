# Semiconductor Industrial Chain (半导体产业链)

> Last updated: 2026-06-26 | Sources: SIA, IC Insights, TrendForce, SEMI, company annual reports, existing project analyses

## Chain Scale

| Metric | Global (2025) | China (2025E) | 2026E | 2027E | CAGR |
|--------|--------------|---------------|-------|-------|------|
| Semiconductor sales | $691B | ~$200B (30%, 70%+ import) | ~$720B | ~$770B | 8-10% |
| Wafer Fab Equipment (WFE) | $115B | ~$40B (35% of global) | ~$130B | ~$140B | 12% |
| Semiconductor Materials | $75B | ~$20B | ~$80B | ~$85B | 6% |
| Chip Design (Fabless) | $240B | ~$60B | ~$260B | ~$285B | 10% |
| Memory | $190B | ~$80B (consumption, <10% domestic) | ~$215B | ~$240B | 12% |
| Advanced Packaging | $45B | ~$12B | ~$52B | ~$60B | 15% |

> **Core driver**: AI算力需求爆发 + 国产替代加速 + 存储涨价周期

## Chain Topology

```
上游（支撑产业）                 中游（核心制造）                 下游（应用）
┌─────────────┐    ┌──────────────────────────┐   ┌──────────────┐
│   EDA/IP    │    │   IC 设计 (Fabless)       │   │   消费电子    │
│  ~$20B全球  │───▶│  ~$240B 全球               │──▶│  手机/PC/穿戴  │
│              │    │  海光/寒武纪/韦尔/兆易    │   │              │
├─────────────┤    ├──────────────────────────┤   ├──────────────┤
│   设备      │    │   晶圆制造 (Foundry)       │   │   AI/数据中心  │
│  ~$115B WFE  │───▶│  ~$130B 全球               │──▶│   GPU/HBM/Server│
│  北方华创    │    │  中芯国际/华虹/华润微     │   │              │
│  中微/拓荆   │    │                          │   ├──────────────┤
├─────────────┤    ├──────────────────────────┤   │   汽车电子    │
│   材料      │───▶│   封测 (OSAT)              │──▶│   IGBT/SiC/MCU │
│  ~$75B全球   │    │  ~$45B全球                │   │              │
│  沪硅/安集   │    │  长电/通富/华天           │   ├──────────────┤
│  彤程/雅克   │    │                          │   │   工业/IoT    │
└─────────────┘    └──────────────────────────┘   └──────────────┘
```

## Detailed Segment Analysis

### 1. EDA & IP (设计工具)

**Global scale**: ~$20B (EDA ~$12B, IP ~$8B)
**China share**: ~$2B (<3% of global EDA, 90%+ imported)
**Bottleneck**: 🔴 Critical — GAAFET EDA export controls restrict 3nm below

| Sub-segment | Global Leader | China Player | Stock Code | Self-Sufficiency |
|-------------|-------------|-------------|-----------|-----------------|
| Analog/mixed-signal EDA | Cadence | **华大九天** | 301269 | ~30% (analog only) |
| SPICE/simulation | Synopsys | **概伦电子** | 688206 | ~15% |
| DFM/yield | Mentor | **广立微** | 301095 | ~10% |
| Semiconductor IP | ARM | **芯原股份** | 688521 | ~5% |
| Embedded CPU IP | ARM | **国芯科技** | 688262 | ~10% |

**Key bottleneck items**: Digital full-flow EDA (digital), advanced-node simulation, 3nm GAA EDA
**Substitution timeline**: 28nm analog flow ~70% domestic by 2026E; digital full flow by 2028E

### 2. Semiconductor Equipment (设备)

**Global WFE**: ~$115B (2025)
**China WFE**: ~$40B (35% of global, 70%+ imported)
**Key catalyst**: DUV ban proposal (May 2026) + YMTC 50% domestic tooling milestone
**Core bottleneck**: 🔴 Critical — lithography, ion implant, high-end inspection

| Category | Global Leader | China Leader | Stock Code | 2025 Revenue | Self-Sufficiency |
|----------|-------------|-------------|-----------|-------------|-----------------|
| **Etch (刻蚀)** | Lam/TEL | **中微公司** | 688012 | ~¥70B (¥7B domestic) | CCP: 20% for 5nm+, ICP: 30% |
| **PVD/CVD/ALD** | AMAT | **北方华创** | 002371 | ~¥270B (total) | Broad coverage, 28nm+ capable |
| **PECVD/ALD** | AMAT/TEL | **拓荆科技** | 688072 | ~¥35B | 30% for mature nodes |
| **Clean (清洗)** | SCREEN/Lam | **盛美上海** | 688082 | ~¥40B | 25% |
| **CMP** | AMAT/Ebara | **华海清科** | 688120 | ~¥30B | 20% |
| **Track (涂胶显影)** | TEL | **芯源微** | 688037 | ~¥20B | 15% (ArFi track in validation) |
| **Inspection (检测)** | KLA | **中科飞测** | 688361 | ~¥8B | <10% for advanced |
| **Ion Implant (离子注入)** | Axcelis | **万业企业(凯世通)** | 600641 | ~¥9B | ~10% |
| **Lithography (光刻)** | ASML | **上海微电子** | Unlisted | — | ~90nm production, 28nm in dev |

**Critical bottleneck details**:
- **DUV immersion lithography**: SMEE 28nm浸没式DUV在产线验证中, 距ASML 1980i (可7nm)仍有较大差距
- **EUV lithography**: 完全无法获得, ASML被荷兰政府禁止对华出口
- **High-end metrology/inspection**: KLA 28nm以下量测设备占中国Fab CAPEX的8-10%, 国产替代率<10%
- **Ion implant**: 中束流国产化率~20%, 高能注入机几乎空白

### 3. Semiconductor Materials (材料)

**Global market**: ~$75B
**China market**: ~$20B (import 60%+)
**Characteristic**: 耗材属性, 客户认证周期长(1-3年), 一旦导入不轻易更换
**Trend**: YMTC/CXMT/SMIC产能扩张直接拉动材料需求

| Category | Global Leader | China Leader | Stock Code | Self-Sufficiency |
|----------|-------------|-------------|-----------|-----------------|
| **Silicon wafers** | 信越/SUMCO | **沪硅产业** | 688126 | 300mm: ~15% |
| | | **立昂微** | 605358 | |
| | | **中环股份** | 002129 | |
| **Photoresist (光刻胶)** | JSR/TOK | **彤程新材** | 603650 | KrF: ~20%, ArF: <5% |
| | | **南大光电** | 300346 | |
| **Electronic gases (电子特气)** | Air Liquide/Linde | **华特气体** | 688268 | ~30% (ASML/Cymer certified) |
| | | **金宏气体** | 688106 | |
| **Target (靶材)** | JX日矿/霍尼韦尔 | **江丰电子** | 300666 | ~15% (5nm certified) |
| **CMP Slurry** | Cabot/Fujimi | **安集科技** | 688019 | ~20% (14nm verified) |
| **CMP Pad** | DuPont/3M | **鼎龙股份** | 300054 | ~15% |
| **Precursor (前驱体)** | Merck/Entegris | **雅克科技** | 002409 | ~20% |
| **Wet chemicals (湿电子化学品)** | BASF/Kanto | **江化微** | 603078 | ~25% (G4/G5 grade) |

**Key bottleneck items**: ArF/EUV photoresist, high-purity silicon wafers for 3nm, advanced CMP slurry for GAA

### 4. Chip Design — Logic & SoC (逻辑芯片设计)

**Global scale**: ~$240B (Fabless IC design)
**China scale**: ~$60B (25% of global, 90% at 28nm+ mature nodes)

| Sub-segment | China Leader | Stock Code | Revenue (2025E) | Technology Node | Key Product |
|-------------|-------------|-----------|----------------|-----------------|-------------|
| **x86 CPU + DCU** | **海光信息** | 688041 | ~¥105B | 7nm | 海光x86 CPU + 深算DCU (类CUDA) |
| **AI training/inference** | **寒武纪** | 688256 | ~¥10B | 7nm | 思元系列AI加速卡 |
| **CIS (图像传感器)** | **韦尔股份** | 603501 | ~¥240B | 55nm-28nm | Omnivision, global #3 CIS |
| **NOR Flash + MCU** | **兆易创新** | 603986 | ~¥75B | 45nm-55nm | GD32 MCU, global Top 3 NOR |
| **RF front-end** | **卓胜微** | 300782 | ~¥55B | 55nm-28nm | RF Switch/LNA, domestic #1 |
| **FPGA** | **复旦微电** | 688385 | ~¥38B | 28nm | 千万门级FPGA |
| | **安路科技** | 688107 | ~¥9B | 28nm | PHOENIX系列 |
| **Optical comm chips** | **源杰科技** | 688498 | ~¥4B | 25G/50G EML | 高速激光器芯片 |
| **GPU (信创)** | **景嘉微** | 300474 | ~¥12B | 28nm | JM系列GPU |

**Design bottleneck**: Advanced-node design (<7nm) limited by EDA export controls and foundry access

### 5. Memory (存储芯片)

**Global market**: ~$190B (2025), expected ~$215B in 2026
**China consumption**: ~$80B (40%+ of global), domestic supply <10%
**Core cycle**: DRAM upcycle (+47.7% price in H1 2026)

| Sub-segment | Global Leader | China Player | Status | Scale |
|-------------|-------------|-------------|--------|-------|
| **DRAM** | Samsung/SK Hynix/Micron | **长鑫存储** (CXMT) | Unlisted, funded by GigaDevice | ~200K wpm (2026E), 17nm DDR5/LPDDR5X |
| **NAND Flash** | Samsung/Kioxia/WDC/Micron | **长江存储** (YMTC) | Unlisted | Xtacking 4.0 (~300L), 50% domestic tooling |
| **NOR Flash** | Winbond/Macronix | **兆易创新** | 603986 | Global #3, 45nm |
| **DRAM interface** | Rambus | **澜起科技** | 688008 | DDR5 RCD/DB global leader |
| **Memory module** | Kingston | **江波龙** | 301308 | Lexar+FORESEE dual brand |
| | | **佰维存储** | 688525 | R&D+packaging integrated |

**Bottleneck analysis** (NAND/DRAM):
- **DRAM**: CXMT at ~10-15% of Samsung's scale. Asynchronous to global leaders. Fab2 expansion under US equipment export restrictions.
- **NAND**: YMTC Xtacking is genuinely competitive (300L+), but capacity is ~5-7% of global. US entity list limits equipment access.

### 6. Foundry (晶圆代工)

**Global market**: ~$130B (2025, pure-play foundry)
**China scale**: ~$25B (SMIC+HuaHong+HuaRun+ Nexchip)

| Company | Stock Code | Process | Monthly Cap (300mm equiv) | Revenue | Key Clients |
|---------|-----------|---------|--------------------------|---------|-------------|
| **中芯国际** | 688981/0981.HK | 14nm FinFET → N+2 (eq. 7nm+) | ~200K (200mm eq = ~80K 300mm) | ~$9.5B | HiSilicon, Qualcomm (PMIC) |
| **华虹半导体** | 688347/1347.HK | 90nm–0.25µm (BCD/eNVM) | ~50K | ~$3B | Power semi, MCU, IOT |
| **华润微** | 688396 | 0.11µm–1.0µm (IDM+foundry) | ~70K (150/200mm) | ~$11B | Power, analog |
| **晶合集成** | 688249 | 150nm–55nm DDIC | ~25K | ~$1.5B | Display drivers |

**Bottleneck**: SMIC无法获得EUV, N+2 (7nm级) 良率和产能受限, 且美国DUV禁令提案可能进一步收紧

### 7. Power Semiconductor (功率半导体)

**Global market**: ~$65B (2025), China ~$20B
**Core demand driver**: NEV (IGBT/SiC) + AI server power (DrMOS/multiphase) + PV inverters
**Self-sufficiency**: IGBT ~25%, SiC MOS <10%, MOSFET ~40%

| Sub-segment | China Leader | Stock Code | Revenue | Position |
|-------------|-------------|-----------|---------|----------|
| **IGBT module** | **斯达半导** | 603290 | ~¥38B | China #1 in NEV IGBT modules |
| | **时代电气** | 688187 | ~¥230B (incl. rail) | Rail+grid IGBT leader |
| **SiC MOS** | **三安光电(三安集成)** | 600703 | ~¥170B (total) | SiC IDM: substrate→module |
| **MOSFET** | **华润微** | 688396 | ~¥110B (total) | Broadest power product line |
| | **新洁能** | 605111 | ~¥16B | Shielded-gate/ super-junction MOSFET |
| **Power IC** | **士兰微** | 600460 | ~¥100B | IDM, IGBT+IPM+SiC |
| **SiC substrate** | **天岳先进** | 688234 | ~¥16B | Global Top 3 SiC substrate |

**Bottleneck**: 8-inch SiC substrate (domestic yield <60% vs Wolfspeed 80%+), high-end IGBT7 equivalent

### 8. OSAT & Advanced Packaging (封测)

**Global market**: ~$45B (OSAT), growing 15%+ driven by AI/ Chiplet
**China market**: ~$15B (35% of global, but advanced packaging <15%)
**Key theme**: Chiplet + CoWoS等效方案 are the key path to bypass advanced node limitations

| Company | Stock Code | Global Rank | 2025 Revenue | Core Technology | Key Client |
|---------|-----------|-------------|-------------|-----------------|-------------|
| **长电科技** | 600584 | #3 | ~¥35B | Fan-out (eWLB), 2.5D/3D SiP, Chiplet (UCIe), TSV | Qualcomm, Apple, HiSilicon |
| **通富微电** | 002156 | #4 | ~¥28B | FCBGA/FCLGA, Chiplet, Fan-out | AMD (80%+ of its封测) |
| **华天科技** | 002185 | #6 | ~¥15B | TSV, Fan-out, SiP, Memory packaging | MediaTek, Qualcomm |
| **甬矽电子** | 688362 | Top 10 CN | ~¥4B | SiP, Fan-out, FCBGA, automotive | — |
| **晶方科技** | 603005 | — | ~¥1.5B | WLCSP (sensor/bio packaging) | — |
| **颀中科技** | 688352 | — | ~¥2B | DDIC packaging (COF/COP) | — |

**Bottleneck**: CoWoS-equivalent 2.5D interposer capacity, HBM TSV, FCBGA substrates for AI chips

### 9. Advanced Process Bottleneck Summary (卡脖子汇总)

| Item | Import Dep. | Key Barrier | China Alternative | Timeline |
|------|------------|-------------|-------------------|----------|
| **EUV Lithography** | 100% | Machine physics, supply chain | SMEE (28nm DUV in dev) | 2030+ for EUV |
| **High-end EDA (Digital)** | 95% | GAAFET export control | 华大九天 (28nm analog only) | 2028+ for full flow |
| **ArF Immersion Photoresist** | 90% | Resin synthesis, patent wall | 彤程新材/南大光电 (in validation) | 2027-2028 |
| **High-precision Inspection** | 90% | Optics + algorithms | 中科飞测 (28nm under validation) | 2027+ |
| **High-end Ion Implant** | 85% | Beamline technology | 凯世通 (中束流 only) | 2028+ |
| **12-inch Super Silicon** | 70% | Purity + crystal growth | 沪硅产业 (30K wpm, <5% for 3nm) | 2028+ |
| **CoWoS-equivalent** | 60% | Interposer + TSV yield | 长电科技/通富微电 (prototype phase) | 2027 |
| **Server CPU (High-end)** | 90% | x86 license + process | 海光信息 (x86 license受限, 7nm) | Ongoing |

## Key Companies by Segment

| Segment | Primary | Secondary | Tertiary |
|---------|---------|-----------|----------|
| EDA | 华大九天 301269 | 概伦电子 688206 | 广立微 301095 |
| IP | 芯原股份 688521 | 国芯科技 688262 | — |
| Equipment | 北方华创 002371 | 中微公司 688012 | 拓荆科技 688072 |
| Equipment 2 | 盛美上海 688082 | 华海清科 688120 | 芯源微 688037 |
| Inspection | 中科飞测 688361 | 精测电子 300567 | 华峰测控 688200 |
| Materials | 沪硅产业 688126 | 安集科技 688019 | 彤程新材 603650 |
| Materials 2 | 雅克科技 002409 | 江丰电子 300666 | 华特气体 688268 |
| Foundry | 中芯国际 688981 | 华虹公司 688347 | 华润微 688396 |
| Memory Design | 兆易创新 603986 | 澜起科技 688008 | 普冉股份 688766 |
| Memory Module | 江波龙 301308 | 佰维存储 688525 | 德明利 001309 |
| AI Chip | 海光信息 688041 | 寒武纪 688256 | 景嘉微 300474 |
| CIS | 韦尔股份 603501 | 格科微 688728 | 思特威 688213 |
| RF | 卓胜微 300782 | 唯捷创芯 688153 | 慧智微 688512 |
| Analog | 圣邦股份 300661 | 思瑞浦 688536 | 纳芯微 688052 |
| Power | 斯达半导 603290 | 时代电气 688187 | 士兰微 600460 |
| SiC | 天岳先进 688234 | 三安光电 600703 | — |
| OSAT | 长电科技 600584 | 通富微电 002156 | 华天科技 002185 |
| Tracking/Coating | 芯源微 688037 | — | — |
| Direct Writing | 芯碁微装 688630 | — | — |

## Cross-Chain Dependencies

- **Semiconductor → AI Computing**: AI chips (GPU/DCU/HBM) enabled by advanced process, packaging
- **Semiconductor → NEV**: IGBT/SiC power modules, MCUs, CIS for ADAS, SiC for OBC
- **Semiconductor Equipment → Semiconductor Memory**: YMTC/CXMT capacity expansion = equipment orders
- **Semiconductor Materials → Foundry**: All fabs consume materials continuously
- **EDA → IC Design**: No chip design possible without EDA tools
- **Advanced Packaging → AI Computing**: Chiplet/CoWoS critical for AI chip performance

## Recent Catalysts (Mid-2026)

| Event | Date | Impact |
|-------|------|--------|
| U.S. bipartisan DUV ban proposal | May 2026 | Equipment stocks surged; medium-term uncertainty for SMIC/YMTC |
| YMTC Fab3 50% domestic tooling milestone | Apr 2026 | Equipment orders visibility improved |
| NVIDIA Q1 FY2027 earnings beat | May 2026 | AI computing chain bullish; advanced packaging demand confirmed |
| CXMT DDR5 mass production ramp | 2026H1 | Memory design + equipment demand |
| SMEE 28nm immersion DUV entering validation | 2026H2 | Potential major breakthrough; catalyst for 张江高科 |
