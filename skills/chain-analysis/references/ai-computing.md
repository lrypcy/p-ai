# AI Computing & Optical Interconnect Industrial Chain (AI算力+光互连产业链)

> Last updated: 2026-06-26 | Sources: Gartner, IDC, TrendForce, Omdia, NVIDIA earnings, company annual reports

## Chain Scale

| Metric | Global (2025) | China (2025) | 2026E | 2027E | CAGR |
|--------|--------------|-------------|-------|-------|------|
| AI server & infrastructure | ~$280B | ~$55B | ~$350B | ~$430B | 25% |
| GPU/AI accelerator TAM | ~$120B | ~$8B (domestic) | ~$165B | ~$210B | 30% |
| Optical transceiver market | ~$15B | ~$4B | ~$20B | ~$26B | 30% |
| High-speed interconnect (DAC/AEC) | ~$8B | ~$2B | ~$11B | ~$15B | 35% |
| AI inference market | ~$40B | ~$8B | ~$60B | ~$85B | 45% |
| Data center cooling | ~$12B | ~$3B | ~$16B | ~$21B | 30% |

> **Core driver**: LLM parameter explosion (GPT-4+: 1.8T params → GPT-5: 8T+), AI agent deployment, inference scaling

## Chain Topology

```
上游（核心部件）             中游（硬件系统）             下游（应用）
┌────────────────┐    ┌─────────────────┐   ┌──────────────────────┐
│  GPU/AI芯片      │    │  AI服务器         │   │  大模型/应用          │
│  NVIDIA / AMD   │───▶│  工业富联/浪潮    │──▶│  百度文心/阿里通义    │
│  海光/寒武纪     │    │  中科曙光/紫光    │   │  字节豆包/智谱       │
├────────────────┤    ├─────────────────┤   ├──────────────────────┤
│  HBM/高带宽存储   │    │  交换机/路由器     │   │  AI Agent/自动驾驶    │
│  SK Hynix/Samsung│──▶│  华为/中兴       │──▶│  智能驾驶/机器人     │
│  长鑫(DRAM)      │    │  锐捷/菲菱科思   │   │                      │
├────────────────┤    ├─────────────────┤   ├──────────────────────┤
│  光模块/光器件    │    │  光互连/线缆      │   │  AI云服务            │
│  中际旭创/新易盛  │──▶│  CPO/NPO模块     │──▶│  阿里云/腾讯云/字节   │
│  天孚通信         │    │  高速背板/PCB    │   │  运营商云            │
├────────────────┤    ├─────────────────┤   └──────────────────────┘
│  高速PCB/封装基板 │    │  散热/液冷       │
│  沪电/深南/生益   │───▶│  英维克/高澜    │
├────────────────┤    └─────────────────┘
│  服务器电源       │
│  麦格米特/欧陆通  │
└────────────────┘
```

## Detailed Segment Analysis

### 1. GPU / AI Accelerator (AI算力芯片)

**Global market**: ~$120B (2025), NVIDIA ~85% market share
**China market**: Domestic AI chips ~$8B (90%+ for Huawei Ascend ecosystem)
**Bottleneck**: 🔴 Critical — high-end GPU access restricted by US export controls

| Company | Stock Code | Product | Process | Compute (FP8) | Position |
|---------|-----------|---------|---------|---------------|----------|
| **NVIDIA** | NVDA | H200 / B200 / GB300 | 4nm (TSMC) | 4-10 PFLOPS | Global #1, 85%+ share |
| **AMD** | AMD | MI350 / MI400 | 4nm (TSMC) | 2-5 PFLOPS | #2 in data center GPU |
| **海光信息** | 688041 | 深算DCU (K100/K200) | 7nm (SMIC N+2) | ~0.5-1 PFLOPS | #1 domestic, x86/ROCm compatible |
| **寒武纪** | 688256 | 思元590/690 | 7nm | ~0.5 PFLOPS | #2 domestic, diversified accelerator |
| **华为昇腾** | Unlisted | Ascend 910C/920 | 7nm (SMIC) | ~1 PFLOPS | #1 in China market share (private) |
| **景嘉微** | 300474 | JM91 series | 28nm | Limited | GPU for 信创/desktop |

**Bottleneck details**:
- US export controls limit NVIDIA H100/B200 sales to China (China-specific H20 reduced to 80% performance)
- SMIC N+2 (7nm eq.) yield estimated at ~60-70% vs TSMC 4nm >90%
- CUDA ecosystem lock-in: NVIDIA's software moat (CUDA 12M+ developers) larger than hardware
- ROCm adaptation by 海光 (deep compute) is key to domestic substitution

### 2. HBM & High-Bandwidth Memory (高带宽存储)

**Global HBM market**: ~$25B (2025), ~$35B (2026E)
**Suppliers**: SK Hynix (~50%), Samsung (~40%), Micron (~10%)
**China position**: CXMT (长鑫) developing HBM-class DRAM, 2-3 generations behind

| Item | Detail |
|------|--------|
| **HBM3E leader** | SK Hynix with MR-MUF process |
| **HBM4 (expected 2026)** | 16-24 layers, 1TB/s+ bandwidth |
| **China alternative** | CXMT DDR5 → HBM2e class (2027E) |
| **Key A-share linkage** | **雅克科技** (HBM前驱体), **华海诚科** (HBM underfill), **兴森科技** (FCBGA载板) |

### 3. Optical Transceiver & Optical Interconnect (光模块与光互连)

**Global optical transceiver market**: ~$15B (2025), ~$20B (2026E)
**Key theme**: 800G → 1.6T transition, CPO/NPO emergence

#### 3.1 Optical Module Companies

| Company | Stock Code | 2025 Revenue | Key Technology | Key Client | Global Position |
|---------|-----------|-------------|---------------|-------------|-----------------|
| **中际旭创** | 300308 | ~¥40B | 800G/1.6T OSFP, SiPh, CPO | NVIDIA, Google, Amazon | #1 global (35%+ 800G share) |
| **新易盛** | 300502 | ~¥20B | LPO (linear-drive), 400G/800G | AWS, Meta | Top 3 global |
| **光迅科技** | 002281 | ~¥8B (optics) | Full chain (chip→module), telecom | Huawei, ZTE | #1 domestic telecom |
| **华工科技** | 000988 | ~¥12B (optics) | 400G/800G, SiPh, optical engine | Chinese cloud | Top 5 domestic |
| **联特科技** | 301205 | ~¥4B | 800G, CWDM, data center | — | Mid-tier |

#### 3.2 Optical Components & Precision Optics

| Company | Stock Code | Product | Position |
|---------|-----------|---------|----------|
| **天孚通信** | 300394 | Optical engine, FA/MT, cold lens, WDM | Global #1 in精密光器件, CPO核心供应商 |
| **源杰科技** | 688498 | 25G/50G/100G EML laser chip | #1 domestic高速激光器芯片 |
| **长光华芯** | 688048 | High-power laser chip (InP, GaAs) | Top 3 domestic |
| **仕佳光子** | 688313 | AWG chip, PLC splitter | #1 domestic AWG |
| **光库科技** | 300620 | Thin-film lithium niobate (TFLN) modulator | Only TFLN fab in China |
| **腾景科技** | 688195 | Precision optics (filter, lens, mirror) | Mid-tier precision optics |
| **太辰光** | 300570 | High-density optical connector, MPO | Top 3 domestic connector |

#### 3.3 Technology Evolution — Key Investment Bottleneck

| Technology | Position | Bottleneck | China Maturity |
|-----------|----------|------------|---------------|
| **800G (current gen)** | Widely deployed | Emitter + DSP 功耗 | Fully capable (中际旭创 leads) |
| **1.6T (2026-2027)** | Early deployment | 200G/lane optics, CPO transition | 中际旭创, 天孚通信 leading |
| **CPO (Co-packaged)** | R&D/Prototype | Optical engine + ASIC co-packaging, thermal | 天孚通信 in NVIDIA ecosystem |
| **LPO (Linear-drive)** | Limited deployment | No DSP → SI challenge, interoperability | 新易盛 leads, but penetration debated |
| **TFLN Modulator** | R&D | Film uniformity, volume manufacturing | 光库科技, limited scale |

**Bottleneck**: 🔴 High-speed EML laser chip (100G/lane) — 源杰科技 still 1-2 years behind global leaders (Lumentum, Broadcom). VCSEL array for CPO virtually absent in China.

### 4. AI Server & Hardware (AI服务器)

**Global AI server**: ~$140B (2025), ~$180B (2026E)
**Supply chain**: Design by NVIDIA/AMD → Manufactured by ODM (广达, 工业富联) → Sold to cloud providers

| Company | Stock Code | Revenue | Role | Position |
|---------|-----------|---------|------|----------|
| **工业富联** | 601138 | ~¥600B (total) | NVIDIA AI server ODM | #1 in AI server ODM (>30% share) |
| **浪潮信息** | 000977 | ~¥100B (total) | AI server system integration | #1 domestic AI server brand |
| **中科曙光** | 603019 | ~¥50B | HPC/AI server, domestic chips | 海光information ecosystem |
| **紫光股份** | 000938 | ~¥80B (total) | Server + switch + storage | Full stack |
| **华勤技术** | 603296 | ~¥100B (total) | AI server ODM | Emerging |

### 5. High-Performance PCB & Packaging Substrate (PCB与封装基板)

**Global PCB market**: ~$80B (2025), server/AI PCB: ~$20B
**Key trend**: Higher layer count, ultra-low loss materials, FCBGA carrier localization

| Company | Stock Code | AI PCB Revenue | Product | Key Client |
|---------|-----------|--------------|---------|-------------|
| **沪电股份** | 002463 | ~¥20B+ | High-speed server PCB, AI accelerator board | NVIDIA (direct supplier) |
| **深南电路** | 002916 | ~¥18B+ | PCB + FCBGA substrate (载板) | CSPs, network OEMs |
| **生益科技** | 600183 | ~¥30B (total) | High-speed CCL (覆铜板, low loss) | #1 domestic CCL, AI PCB enabler |
| **兴森科技** | 002436 | ~¥6B | PCB + FCBGA substrate (prototype) | AI chip customer validation |
| **胜宏科技** | 300476 | ~¥12B | HD PCB, server PCB | — |

**Bottleneck**: 🟠 FCBGA载板 (needed for GPU/CPU packaging) — 深南电路/兴森科技 in validation phase, import dependency >80%

### 6. Data Center Cooling (数据中心散热)

| Company | Stock Code | Product | Position |
|---------|-----------|---------|----------|
| **英维克** | 002837 | Liquid cooling (cold plate, immersion) | #1 in AI data center liquid cooling |
| **高澜股份** | 300499 | Water cooling system for HPC | Top 3 |
| **申菱环境** | 301018 | Precision air conditioning, liquid cooling | — |

**Bottleneck**: 🟡 High-power GPU thermal management (>1000W/chip). China liquid cooling competitive.

### 7. AI Computing Chain — Bottleneck Summary

| Bottleneck Item | Import Dep. | Key Barrier | China Alternative | Timeline |
|----------------|------------|-------------|-------------------|----------|
| **High-end GPU (CUDA ecosystem)** | 98% | Process + software (CUDA) | 海光DCU (ROCm adaptation) | 2027+ to reach parity |
| **HBM3E/HBM4** | 99% | TSV + MR-MUF process | 长鑫 (HBM2e class 2027E) | 2028+ |
| **100G/lane EML laser** | 85% | Epitaxy + process consistency | 源杰科技 (50G in production) | 2027 |
| **CPO optical engine** | 70% | Active alignment, thermal | 天孚通信 (in NVIDIA ecosystem) | 2026-2027 |
| **FCBGA carrier substrate** | 80% | Fine line, laser drill | 深南/兴森 (客户验证中) | 2027 |
| **High-end switch chip** | 90% | CMOS process >5nm | 华为 (自用), 盛科通信 | Limited commercial |
| **Server BIOS/firmware** | 60% | IP/compatibility | 中科曙光/浪潮 (partial) | Ongoing |

## Key Companies by Segment

| Segment | Primary | Secondary | Tertiary |
|---------|---------|-----------|----------|
| AI Chip (Domestic) | 海光信息 688041 | 寒武纪 688256 | 景嘉微 300474 |
| Optical Module | 中际旭创 300308 | 新易盛 300502 | 光迅科技 002281 |
| Optical Components | 天孚通信 300394 | 源杰科技 688498 | 光库科技 300620 |
| Optical Precision | 仕佳光子 688313 | 腾景科技 688195 | 太辰光 300570 |
| AI Server | 工业富联 601138 | 浪潮信息 000977 | 中科曙光 603019 |
| High-speed PCB | 沪电股份 002463 | 深南电路 002916 | 生益科技 600183 |
| PCB Carrier | 兴森科技 002436 | 深南电路 002916 | — |
| Liquid Cooling | 英维克 002837 | 高澜股份 300499 | — |
| Server Power | 麦格米特 002851 | 欧陆通 300870 | — |

## Cross-Chain Dependencies

- **AI Computing → Semiconductor (GPU/HBM)**: Hardware supply
- **AI Computing → Optical Module (CPO/NPO)**: 800G→1.6T→CPO transition directly enabled by optical module innovation
- **AI Computing → PCB (沪电/深南)**: AI accelerator board demand
- **AI Computing → Semiconductor Equipment**: SMIC capacity expansion needed for domestic AI chips
- **AI Computing → NEV (Autonomous Driving)**: ADAS compute requirements drive AI chip demand from automotive
- **AI Computing → Data Center Infrastructure**: Cooling, power, networking all required

## Recent Catalysts (Mid-2026)

| Event | Date | Impact |
|-------|------|--------|
| NVIDIA Q1 FY2027 earnings beat | May 2026 | AI infra capex trajectory confirmed; 中际旭创/天孚通信 surged |
| US further GPU export restrictions | Apr 2026 | Restricted more variants; domestic AI chip stocks (海光/寒武纪) volatile |
| China 5-year AI plan | Mar 2026 | ¥300B AI infrastructure fund announced; 中科曙光/浪潮 benefited |
| CPO ecosystem progress (NVIDIA) | Ongoing | 天孚通信 in CPO supply chain; catalyst pending |
