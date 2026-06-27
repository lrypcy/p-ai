#!/usr/bin/env python3
"""
Industrial Chain Analysis Report Generator — HTML Only.

Generates interactive ECharts HTML reports for ANY industrial chain.
Predefined chains (storage, semiconductor, new-energy-vehicle, ai-computing,
glass-substrate, pcb) have curated segment structure and bottleneck analysis.
Any other chain name triggers auto-discovery via industry boards.

Usage:
    # List predefined chains
    python chain_report.py --list

    # Generate report for a predefined chain
    python chain_report.py --chain semiconductor --output reports/semi.html

    # Auto-discover any chain (not in predefined list)
    python chain_report.py --chain 光伏 --output reports/光伏产业链.html
    python chain_report.py --chain 机器人 --output reports/机器人产业链.html

    # Show a specific company's position in chain
    python chain_report.py --chain storage --company 688525
"""

import argparse
import json
import os
import sys
from datetime import datetime

from html_theme import CSS_COMMON, theme_css, THEMES

from data_fetcher import (
    CHAIN_TEMPLATES,
    discover_chain_companies,
    enrich_all,
    format_market_scale,
    build_stock_card_html,
    auto_discover_chain,
)


# ── Chain Analysis Templates ──────────────────────────────────────────────
# These contain ONLY analytical content (segment descriptions, bottleneck
# analysis, cross-chain relationships). Company data is discovered dynamically
# via data_fetcher at report generation time.
# ═══════════════════════════════════════════════════════════════════════════

CHAIN_ANALYSIS = {
    "storage": {
        "bottleneck_summary": [
            {"item": "DRAM晶圆制造", "import_dep": "97%", "barrier": "规模仅三星~10%, 设备出口管制", "china_alt": "长鑫存储(CXMT) 19nm DDR5/LPDDR5X", "timeline": "2028+ 替代加速"},
            {"item": "NAND晶圆制造", "import_dep": "87%", "barrier": "美国实体清单限制设备采购", "china_alt": "长江存储(YMTC) Xtacking 300L+", "timeline": "2028+ 可期"},
            {"item": "HBM 制造", "import_dep": "99%", "barrier": "TSV+MR-MUF封装, 良率低", "china_alt": "长鑫HBM3 2026H2量产; 长电已量产HBM3E封测", "timeline": "2027-2028 初步替代"},
            {"item": "HBM 封测", "import_dep": "90%", "barrier": "3D堆叠+TSV+混合键合", "china_alt": "长电HBM3E量产(良率98.5%); 深科技(沛顿)通过NVIDIA验证", "timeline": "已突破, 放量中"},
            {"item": "存储主控芯片", "import_dep": "85%", "barrier": "群联/慧荣台企主导", "china_alt": "德明利自研主控; 江波龙自研主控超8000万颗部署", "timeline": "2027+ OEM导入"},
            {"item": "刻蚀/薄膜/CMP设备", "import_dep": "80%", "barrier": "先进工艺验证壁垒", "china_alt": "中微/拓荆/华海清科 批量交付", "timeline": "逐步突破中"},
            {"item": "ArF光刻胶(存储)", "import_dep": ">95%", "barrier": "树脂合成+专利墙", "china_alt": "南大光电/彤程新材 客户验证中", "timeline": "2027-2028"},
        ],
        "cross_chain": [
            "存储 → AI Computing: HBM是AI GPU核心配套, AI服务器DRAM+SSD用量激增",
            "存储 → 消费电子: AI手机/AI PC/AI眼镜推动NOR Flash/LPDDR容量升级",
            "存储 → 汽车电子: 智能驾驶/座舱带动车规级SRAM/DRAM/NOR需求, 单车价值量$50→$300+",
            "存储 → 半导体设备: 长鑫/长存扩产直接拉动刻蚀/薄膜/CMP/清洗设备订单",
        ],
    },
    "semiconductor": {
        "bottleneck_summary": [
            {"item": "EUV光刻机", "import_dep": "100%", "barrier": "整机物理+供应链", "china_alt": "SMEE (28nm DUV开发中)", "timeline": "2030+ for EUV"},
            {"item": "高端数字EDA", "import_dep": "95%", "barrier": "GAAFET出口管制", "china_alt": "华大九天(28nm analog only)", "timeline": "2028+ full flow"},
            {"item": "ArF浸没式光刻胶", "import_dep": "90%", "barrier": "树脂合成+专利墙", "china_alt": "彤程/南大(客户验证中)", "timeline": "2027-2028"},
            {"item": "高精度量测设备", "import_dep": "90%", "barrier": "光学+算法", "china_alt": "中科飞测(28nm验证中)", "timeline": "2027+"},
            {"item": "12英寸大硅片(先进制程)", "import_dep": "70%", "barrier": "纯度+晶体生长", "china_alt": "沪硅(30K/月, <5% for 3nm)", "timeline": "2028+"},
            {"item": "高能离子注入机", "import_dep": "85%", "barrier": "束流技术", "china_alt": "凯世通(中束流only)", "timeline": "2028+"},
        ],
        "cross_chain": [
            "Semiconductor → AI Computing: AI芯片(GPU/DCU/HBM)依赖先进制程和封装",
            "Semiconductor → NEV: IGBT/SiC功率模块、MCU、CIS for ADAS",
            "Semiconductor → PV: 光伏逆变器功率器件、IGBT模块",
        ],
    },
    "new-energy-vehicle": {
        "bottleneck_summary": [
            {"item": "高端智驾SoC", "import_dep": "90%", "barrier": "NVIDIA Orin/Thor垄断", "china_alt": "华为昇腾MDC, 地平线J6", "timeline": "2027+"},
            {"item": "8寸SiC衬底", "import_dep": "80%", "barrier": "晶体生长良率(<60%)", "china_alt": "天岳先进/天科合达", "timeline": "2027-2028"},
            {"item": "锂资源", "import_dep": "60%", "barrier": "海外矿产控制", "china_alt": "赣锋/天齐海外矿+回收", "timeline": "ongoing"},
            {"item": "LiDAR SPAD芯片", "import_dep": "70%", "barrier": "Sony独占", "china_alt": "禾赛/速腾自研chip", "timeline": "2026-2027"},
            {"item": "固态电池", "import_dep": "N/A", "barrier": "丰田/Samsung SDI领先3-5年", "china_alt": "CATL/国轩半固态2026", "timeline": "2028+"},
        ],
        "cross_chain": [
            "NEV → Lithium Battery: 电池是NEV核心成本(占整车~40%)",
            "NEV → Power Semiconductor: IGBT/SiC单车价值¥2,000-5,000",
            "NEV → AI Computing: 自动驾驶算力需求驱动AI芯片",
            "NEV → Semiconductor (CIS): ADAS多摄像头驱动CIS需求",
        ],
    },
    "laser": {
        "bottleneck_summary": [
            {"item": "高功率激光芯片(EEL)", "import_dep": "80%", "barrier": "Lumentum/II-VI主导, 6寸GaAs工艺", "china_alt": "长光华芯/炬光科技 量产100W+单管", "timeline": "2026-2027"},
            {"item": "超快激光器(飞秒)", "import_dep": "75%", "barrier": "锁模技术+增益介质一致性", "china_alt": "德龙激光/华工科技 工业级量产", "timeline": "2027"},
            {"item": "高功率光纤激光器(>10kW)", "import_dep": "40%", "barrier": "泵浦源+大模场光纤", "china_alt": "锐科激光/杰普特 全球第二梯队", "timeline": "已突破"},
            {"item": "高端医美/光刻激光", "import_dep": "90%", "barrier": "医疗认证+品牌壁垒", "china_alt": "华工科技/大族激光 布局中", "timeline": "2028+"},
        ],
        "cross_chain": [
            "激光 → PCB: 激光钻孔是HDI/封装基板核心工艺",
            "激光 → 半导体: TGV激光打孔+晶圆切割+SiC退火",
            "激光 → 新能源: 锂电激光焊接(P极/Q极)是刚需",
            "激光 → 医美: 皮秒/CO2激光国产替代空间大",
        ],
    },
    "ai-computing": {
        "bottleneck_summary": [
            {"item": "高端GPU (CUDA生态)", "import_dep": "98%", "barrier": "先进制程+CUDA生态", "china_alt": "海光DCU (ROCm适配)", "timeline": "2027+ parity"},
            {"item": "HBM3E/HBM4", "import_dep": "99%", "barrier": "TSV+MR-MUF工艺", "china_alt": "长鑫 (HBM2e 2027E)", "timeline": "2028+"},
            {"item": "100G/lane EML激光器", "import_dep": "85%", "barrier": "外延+工艺一致性", "china_alt": "源杰科技(50G量产)", "timeline": "2027"},
            {"item": "FCBGA高端载板", "import_dep": "80%", "barrier": "精细线路, 激光钻孔", "china_alt": "深南/兴森(验证中)", "timeline": "2027"},
            {"item": "CPO光引擎量产", "import_dep": "70%", "barrier": "有源对位+散热", "china_alt": "天孚通信 (NVIDIA生态)", "timeline": "2026-2027"},
        ],
        "cross_chain": [
            "AI Computing → Semiconductor: AI芯片依赖先进制程(TSMC/SMIC)和HBM",
            "AI Computing → Optical Module: 800G→1.6T→CPO直接驱动光模块创新",
            "AI Computing → NEV: 自动驾驶算力需求拉动AI芯片汽车市场",
            "AI Computing → PCB: AI加速器板层数和材料要求大幅提升",
        ],
    },
}


# ── HTML Template ─────────────────────────────────────────────────────────

def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_html(chain_id: str) -> str:
    """Generate complete interactive ECharts HTML report for ANY chain.
    
    For predefined chains (storage, semiconductor, etc.) uses optimized templates.
    For unknown chains, auto-discovers structure via AKShare industry boards.
    All stock data (prices, financials, K-line) is fetched from live APIs.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # ── Resolve chain template (predefined or auto-discover) ──
    if chain_id in CHAIN_TEMPLATES:
        tmpl = CHAIN_TEMPLATES[chain_id]
        print(f"[Data] Using predefined template: {tmpl['name']}")
        companies = discover_chain_companies(chain_id, max_companies=25)
        analysis = CHAIN_ANALYSIS.get(chain_id, {})
    else:
        print(f"[Data] Auto-discovering chain: {chain_id}")
        tmpl, companies = auto_discover_chain(chain_id)
        analysis = {}
        CHAIN_TEMPLATES[chain_id] = tmpl
    
    print(f"[Data] Discovered {len(companies)} companies")
    
    # ── Fetch market scale data ──
    scale = format_market_scale(chain_id)
    
    # ── Enrich all companies with live data ──
    enriched = enrich_all(companies)
    
    # ── Build scale ECharts config ──
    scale_names, scale_global, scale_china = [], [], []
    for s in scale.get("segments", []):
        scale_names.append(s.get("name", ""))
        scale_global.append(s.get("global", ""))
        scale_china.append(s.get("china", ""))
    
    scale_chart_json = json.dumps({
        "names": scale_names,
        "global": scale_global,
        "china": scale_china,
    }, ensure_ascii=False)
    
    # ── Build segments HTML with clickable company names ──
    seg_nav = ""
    segments_html = ""
    for i, seg in enumerate(tmpl["segments"]):
        companies_rows = ""
        for comp in companies:
            code = comp.get("code", "")
            market = comp.get("market", "")
            ed = enriched.get(code, {})
            biz = ed.get("business", "暂无数据")
            mcap_s = ed.get("mcap_s", "N/A")
            is_tradable = market in ("sh", "sz", "hk", "bj") and (
                (code.endswith(".HK") and code.replace(".HK", "").isdigit()) or
                (code.isdigit() and len(code) == 6)
            )
            if is_tradable:
                name_html = f'<a href="javascript:void(0)" onclick="switchTab(\'{code}\')" class="co-link">{comp["name"]}</a>'
            else:
                name_html = f'<span style="font-weight:600">{comp["name"]}</span>'
            companies_rows += f"""
<tr>
    <td style="font-weight:600">{name_html}</td>
    <td><code>{code}</code></td>
    <td style="color:#718096">{biz}</td>
    <td style="text-align:right;color:#718096;white-space:nowrap">{mcap_s}</td>
</tr>"""
        
        seg_nav += f'<a href="#seg-{i}" class="sn">{seg["emoji"]} {seg["name"]}</a>'
        bt = seg.get("bottleneck", "")
        if bt.startswith("🔴"):
            bt_class = "bt-red"
        elif bt.startswith("🟠"):
            bt_class = "bt-orange"
        else:
            bt_class = "bt-yellow"
        
        segments_html += f"""
<div class="sec" id="seg-{i}">
    <div class="sec-hd"><h2>{seg['emoji']} {i+1}. {seg['name']}</h2></div>
    <div class="sec-bd">
        <p class="sec-desc">{seg['description']}</p>
        {('<div class="bottleneck-tag ' + bt_class + '">' + bt + '</div>') if bt else ''}
        <table class="ctable">
            <thead><tr><th>公司</th><th>代码</th><th>核心业务</th><th>市值</th></tr></thead>
            <tbody>{companies_rows}</tbody>
        </table>
    </div>
</div>"""
    
    # ── Build per-stock analysis cards ──
    print("[Data] Building stock analysis cards (shared template)...")
    stock_cards_html = ""
    stock_code_list = []
    stock_subnav_html = "".join(f'<a href="javascript:void(0)" onclick="switchTab(' + "'" + f'{comp["code"]}' + "'" + f')" class="sn">{comp["name"]}</a>' for comp in companies)
    
    # Build company → sector lookup
    comp_seg_map = {}
    for comp in companies:
        comp_seg_map[comp["code"]] = comp.get("_seg_name", "")
    
    for comp in companies:
        code = comp.get("code", "")
        stock_code_list.append(code)
        sector = comp_seg_map.get(code, "")
        stock_cards_html += build_stock_card_html(comp, enriched, sector_name=sector, news_count=8)
        
        ed = enriched.get(code, {})
        fin = ed.get("fin")
        mcap_s = ed.get("mcap_s", "N/A")
        pe = ed.get("pe", 0)
        pe_s = f"{pe:.1f}" if pe else "N/A"
        print(f"    {comp['name']}({code}): 市值{mcap_s} PE={pe_s}" +
              (f" Q1营收{fin['revenue_q']}亿 净利{fin['profit_q']}亿" if fin and fin.get("revenue_q") else ""))
    
    # ── Build bottleneck table ──
    bottleneck_rows = ""
    for b in analysis.get("bottleneck_summary", []):
        dep_val = b["import_dep"].replace("%", "")
        try:
            dep_int = int(dep_val)
            if dep_int >= 90:
                level_icon, bt_class = "🔴", "bt-red"
            elif dep_int >= 60:
                level_icon, bt_class = "🟠", "bt-orange"
            else:
                level_icon, bt_class = "🟡", "bt-yellow"
        except ValueError:
            level_icon, bt_class = "🟡", "bt-yellow"
        bottleneck_rows += f"""
<tr>
    <td style="font-weight:600">{b['item']}</td>
    <td style="text-align:center"><span class="btd {bt_class}">{b['import_dep']}</span></td>
    <td>{b['barrier']}</td>
    <td>{b['china_alt']}</td>
    <td style="text-align:center">{b['timeline']}</td>
</tr>"""
    
    # ── Cross-chain ──
    cross_items = "".join(f"<li>{x}</li>" for x in analysis.get("cross_chain", []))
    
    # ── Build chart data for enhanced overview ──
    # Radar chart data: bottleneck import dependencies
    bt_data = analysis.get("bottleneck_summary", [])
    radar_indicators = []
    radar_values = []
    for b in bt_data:
        dep_val = b["import_dep"].replace("%", "").replace(">", "")
        try:
            dep_int = int(dep_val)
        except ValueError:
            dep_int = 50
        radar_indicators.append({"name": b["item"][:12], "max": 100})
        radar_values.append(dep_int)
    radar_json = json.dumps({"indicators": radar_indicators, "values": radar_values}, ensure_ascii=False)
    
    # Pie & growth data from scale segments
    pie_items = []
    growth_items = []
    for s in scale.get("segments", []):
        pie_items.append({"name": s["name"], "global": s.get("global", "N/A"), "china": s.get("china", "N/A")})
        cagr_str = s.get("cagr", "0%").replace("%", "").replace("+", "")
        try:
            growth_items.append({"name": s["name"], "cagr": float(cagr_str)})
        except ValueError:
            growth_items.append({"name": s["name"], "cagr": 0})
    pie_chart_json = json.dumps({"segments": pie_items}, ensure_ascii=False)
    growth_chart_json = json.dumps({"segments": growth_items}, ensure_ascii=False)
    
    # Dashboard metrics
    avg_dep = 0
    if bt_data:
        deps = []
        for b in bt_data:
            dv = b["import_dep"].replace("%", "").replace(">", "")
            try:
                deps.append(int(dv))
            except ValueError:
                pass
        avg_dep = round(sum(deps) / len(deps)) if deps else 0
    total_companies = len(companies)
    total_bottlenecks = len(bt_data)
    
    # ── Company-level aggregated data from real market data ──
    company_stats = []
    for comp in companies:
        code_ = comp["code"]
        ed_ = enriched.get(code_, {})
        fin_ = ed_.get("fin") or {}
        mcap_ = ed_.get("mcap", 0) or 0
        pe_ = ed_.get("pe", 0) or 0
        company_stats.append({
            "name": comp["name"], "code": code_,
            "segment": comp.get("_seg_name", "其他"),
            "mcap": mcap_, "pe": pe_,
            "revenue": fin_.get("revenue_q", 0) or 0,
            "profit": fin_.get("profit_q", 0) or 0,
            "rev_yoy": fin_.get("rev_yoy", 0) or 0,
            "prof_yoy": fin_.get("prof_yoy", 0) or 0,
            "margin_gross": fin_.get("margin_gross", 0) or 0,
            "margin_net": fin_.get("margin_net", 0) or 0,
            "roe": fin_.get("roe", 0) or 0,
            "qprofits": ed_.get("qprofits") or [],
        })
    company_stats.sort(key=lambda x: x["mcap"], reverse=True)
    
    # Top companies by market cap (bar chart data)
    top_n = company_stats[:10]
    top_n = [c for c in top_n if c["mcap"] > 0]
    top_companies_json = json.dumps([{"name": c["name"][:6], "mcap": round(c["mcap"], 1), "code": c["code"]} for c in top_n], ensure_ascii=False)
    
    # PE vs Revenue Growth scatter (filter reasonable values)
    scatter_data = [c for c in company_stats if 5 < c["pe"] < 500 and c["rev_yoy"] != 0]
    pe_growth_json = json.dumps([{"name": c["name"], "pe": round(c["pe"], 1), "rev_yoy": round(c["rev_yoy"], 1), "profit": round(c["profit"], 1), "mcap": round(c["mcap"], 1)} for c in scatter_data], ensure_ascii=False)
    
    # Performance heatmap (top 15 by mcap, normalized scores)
    top15 = company_stats[:15]
    perf_heatmap_json = json.dumps({"companies": [c["name"][:5] for c in top15], "metrics": ["PE", "营收增速%", "利润增速%", "毛利率%", "净利率%"]}, ensure_ascii=False)
    heatmap_values = []
    metric_keys = [("pe", True), ("rev_yoy", False), ("prof_yoy", False), ("margin_gross", False), ("margin_net", False)]
    for c in top15:
        row = []
        for key, invert in metric_keys:
            v = c.get(key, 0) or 0
            row.append(round(v, 1))
        heatmap_values.append(row)
    heatmap_values_json = json.dumps(heatmap_values, ensure_ascii=False)
    
    # Aggregate chain metrics from real data
    valid_mcaps = [c["mcap"] for c in company_stats if c["mcap"] > 0]
    valid_pes = [c["pe"] for c in company_stats if 5 < c["pe"] < 1000]
    valid_rev_yoy = [c["rev_yoy"] for c in company_stats if c["rev_yoy"] != 0]
    total_chain_mcap = sum(valid_mcaps)
    chain_mcap_s = f"¥{total_chain_mcap:.0f}亿" if total_chain_mcap > 0 else "N/A"
    avg_pe_chain = round(sum(valid_pes) / len(valid_pes), 1) if valid_pes else 0
    avg_rev_growth = round(sum(valid_rev_yoy) / len(valid_rev_yoy), 1) if valid_rev_yoy else 0
    # Count companies in different performance buckets
    growth_buckets = [
        {"name": "高增长(>20%)", "count": sum(1 for c in company_stats if c["rev_yoy"] > 20)},
        {"name": "中增长(0-20%)", "count": sum(1 for c in company_stats if 0 < c["rev_yoy"] <= 20)},
        {"name": "负增长(<0%)", "count": sum(1 for c in company_stats if c["rev_yoy"] < 0)},
        {"name": "无数据", "count": sum(1 for c in company_stats if c["rev_yoy"] == 0)},
    ]
    growth_dist_json = json.dumps(growth_buckets, ensure_ascii=False)
    
    # ── Segment-level real data aggregation (Layer 4) ──
    seg_stats = {}
    for i, seg in enumerate(tmpl["segments"]):
        seg_name = seg["name"]
        seg_companies = [c for c in company_stats if c["segment"] == seg_name]
        if not seg_companies:
            continue
        seg_mcaps = [c["mcap"] for c in seg_companies if c["mcap"] > 0]
        seg_pes = [c["pe"] for c in seg_companies if 5 < c["pe"] < 500]
        seg_revs = [c["rev_yoy"] for c in seg_companies if c["rev_yoy"] != 0]
        seg_gross = [c["margin_gross"] for c in seg_companies if c["margin_gross"] > 0]
        seg_net = [c["margin_net"] for c in seg_companies if c["margin_net"] > 0]
        seg_roe = [c["roe"] for c in seg_companies if c["roe"] != 0]
        seg_stats[seg_name] = {
            "count": len(seg_companies),
            "total_mcap": round(sum(seg_mcaps), 1),
            "avg_pe": round(sum(seg_pes) / len(seg_pes), 1) if seg_pes else 0,
            "avg_rev_yoy": round(sum(seg_revs) / len(seg_revs), 1) if seg_revs else 0,
            "avg_margin_gross": round(sum(seg_gross) / len(seg_gross), 1) if seg_gross else 0,
            "avg_margin_net": round(sum(seg_net) / len(seg_net), 1) if seg_net else 0,
            "avg_roe": round(sum(seg_roe) / len(seg_roe), 1) if seg_roe else 0,
        }
    has_multiple_segments = len(seg_stats) > 1
    seg_stats_json = json.dumps(seg_stats, ensure_ascii=False)
    
    # ── PE Distribution histogram (Layer 5) ──
    bucket_names = ["<0(亏损)", "0~15", "15~30", "30~60", "60~100", ">100"]
    bucket_values = [0] * 6
    bucket_companies = {b: [] for b in bucket_names}
    for c in company_stats:
        pe = c["pe"]
        if pe < 0:
            idx = 0
        elif pe <= 15:
            idx = 1
        elif pe <= 30:
            idx = 2
        elif pe <= 60:
            idx = 3
        elif pe <= 100:
            idx = 4
        else:
            idx = 5
        bucket_values[idx] += 1
        bucket_companies[bucket_names[idx]].append(c["name"])
    pe_hist_json = json.dumps({
        "categories": bucket_names,
        "values": bucket_values,
        "companies": [bucket_companies[b] for b in bucket_names],
    }, ensure_ascii=False)
    
    # ── Market Concentration CR5 (Layer 6) ──
    valid_mcaps_sorted = sorted(valid_mcaps, reverse=True)
    total_valid_mcap = sum(valid_mcaps_sorted) or 1
    cr5 = round(sum(valid_mcaps_sorted[:5]) / total_valid_mcap * 100, 1) if len(valid_mcaps_sorted) >= 5 else 0
    cr10 = round(sum(valid_mcaps_sorted[:10]) / total_valid_mcap * 100, 1) if len(valid_mcaps_sorted) >= 10 else 0
    if valid_mcaps_sorted:
        total_cap = sum(valid_mcaps_sorted)
        top1_pct = round(valid_mcaps_sorted[0] / total_cap * 100, 1) if valid_mcaps_sorted else 0
        top23_pct = round(sum(valid_mcaps_sorted[1:3]) / total_cap * 100, 1) if len(valid_mcaps_sorted) > 3 else 0
        top45_pct = round(sum(valid_mcaps_sorted[3:5]) / total_cap * 100, 1) if len(valid_mcaps_sorted) > 5 else 0
        other_pct = round(100 - top1_pct - top23_pct - top45_pct, 1)
        cr_data = [
            {"name": "Top1", "value": top1_pct, "itemStyle": {"color": "#e94560"}},
            {"name": "Top2-3", "value": top23_pct, "itemStyle": {"color": "#f6ad55"}},
            {"name": "Top4-5", "value": top45_pct, "itemStyle": {"color": "#63b3ed"}},
            {"name": "其他", "value": other_pct, "itemStyle": {"color": "#cbd5e1"}},
        ]
    else:
        cr_data = []
    cr_json = json.dumps({"cr5": cr5, "cr10": cr10, "data": cr_data}, ensure_ascii=False)
    
    # ── Revenue vs Market Cap scatter (Layer 7) ──
    rev_mcap_data = [c for c in company_stats if c["mcap"] > 0 and c["revenue"] > 0]
    rev_mcap_json = json.dumps([{
        "name": c["name"], "revenue": round(c["revenue"], 1),
        "mcap": round(c["mcap"], 1), "profit": round(c["profit"], 1),
        "margin_gross": c["margin_gross"],
    } for c in rev_mcap_data], ensure_ascii=False)
    
    # ── Multi-quarter revenue trend (Layer 12) ──
    trend_data = {}
    for c in company_stats[:6]:
        qp = c.get("qprofits") or []
        if qp:
            trend_data[c["code"]] = {
                "name": c["name"],
                "revenues": [{"quarter": q["label"], "value": round(q.get("revenue", 0), 1)} for q in qp if q.get("revenue")],
                "profits": [{"quarter": q["label"], "value": round(q.get("profit", 0), 1)} for q in qp if q.get("profit")],
            }
    trend_revenue_json = json.dumps(trend_data, ensure_ascii=False)
    has_trend_data = bool(trend_data)
    
    # ── Bottleneck-Company Exposure (Layer 14) ──
    if bt_data:
        bt_exposure = []
        for b in bt_data:
            b_name = b["item"]
            affected = []
            for c in company_stats:
                biz = (enriched.get(c["code"], {}) or {}).get("business", "") or ""
                c_seg = c.get("segment", "")
                # Match if bottleneck keyword appears in company's segment name or business
                kw = b_name[:4]
                if kw in c_seg or kw in biz:
                    affected.append(c["name"])
            dep_str = b["import_dep"]
            try:
                dep_int = int(dep_str.replace("%", ""))
                bt_class = "bt-red" if dep_int >= 90 else ("bt-orange" if dep_int >= 60 else "bt-yellow")
            except ValueError:
                bt_class = "bt-yellow"
            bt_exposure.append({
                "bottleneck": b_name,
                "dep": dep_str,
                "bt_class": bt_class,
                "timeline": b["timeline"],
                "affected": affected[:6],
            })
        bt_exposure_json = json.dumps(bt_exposure, ensure_ascii=False)
        _cards = []
        for _b in bt_exposure:
            _affected_html = (f'<div style="font-size:12px;color:#64748b;margin-top:8px">'
                             f'可能受影响的公司: {", ".join(_b["affected"][:6])}</div>'
                             ) if _b["affected"] else '<div style="font-size:12px;color:#94a3b8;margin-top:8px">暂无直接匹配</div>'
            _cards.append(
                f'<div style="background:var(--card-bg,#fff);border-radius:12px;padding:14px 16px;'
                f'box-shadow:0 1px 6px rgba(0,0,0,0.06)">'
                f'<div style="font-weight:600;font-size:14px;margin-bottom:6px">⚠️ {escape_html(_b["bottleneck"])}</div>'
                f'<div style="font-size:12px;color:#64748b;margin-bottom:4px">'
                f'进口依赖: <span class="btd {_b["bt_class"]}">{escape_html(_b["dep"])}</span>'
                f' &nbsp;·&nbsp; 替代时间: {escape_html(_b["timeline"])}</div>'
                f'{_affected_html}</div>'
            )
        _bt_exposure_html = ('<div class="over">'
                             '<h3>🎯 瓶颈-公司暴露度矩阵</h3>'
                             '<p style="color:#64748b;font-size:13px;margin-bottom:8px">'
                             '每个卡脖子环节下展示业务可能受影响的链内公司</p>'
                             '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">'
                             + "".join(_cards) +
                             '</div></div>')
    else:
        bt_exposure_json = "[]"
        _bt_exposure_html = ""
    
    # Color theme — auto-generated from chain name (or predefined)
    _THEME_PRESETS = {
        "storage": {"from": "#0f0c29", "mid": "#302b63", "to": "#24243e", "accent": "#667eea"},
        "semiconductor": {"from": "#1a0a2e", "mid": "#16213e", "to": "#0f3460", "accent": "#e94560"},
        "new-energy-vehicle": {"from": "#0d3320", "mid": "#1a5a30", "to": "#2d8a4e", "accent": "#00df7f"},
        "ai-computing": {"from": "#1a0a2e", "mid": "#2d1b69", "to": "#11998e", "accent": "#38ef7d"},
        "laser": {"from": "#1a0a2e", "mid": "#302b63", "to": "#24243e", "accent": "#e94560"},
    }
    theme = _THEME_PRESETS.get(chain_id)
    if not theme:
        import hashlib
        h = hashlib.md5(chain_id.encode()).hexdigest()
        hue = int(h[:6], 16) % 360
        sat = 50 + int(h[6:8], 16) % 30
        theme = {
            "from": f"hsl({hue},{sat}%,10%)",
            "mid": f"hsl({hue},{sat}%,20%)",
            "to": f"hsl({hue},{sat}%,30%)",
            "accent": f"hsl({hue},{sat + 20}%,55%)",
        }
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{tmpl['icon']} {tmpl['name']} — 深度研究报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
<style>
/* ── Theme overrides for this chain ── */
{theme_css(theme)}
/* ── Shared chain-analysis design system ── */
{CSS_COMMON}
/* ── chain_report-specific extensions ── */
.si-china{{font-size:11px;color:#94a3b8;margin-top:4px}}
.co-link{{border-bottom:1px dashed;font-weight:600}}
.co-link:hover{{color:#e53e3e;border-bottom-color:#e53e3e}}
</style>
</head>
<body>

<div class="header">
    <h1>{tmpl['icon']} {tmpl['name']} 深度研究报告</h1>
    <div class="sub">{tmpl.get('name_en', '')} | 产业链规模 · 上下游拓扑 · 卡脖子 · 上市公司</div>
    <div class="dt">📅 {now} | 数据来源: TrendForce, SIA, CPCA, 公司年报, Wind | 行情: 腾讯+东方财富</div>
</div>

<div class="cont">

<!-- ── Tab Navigation ── -->
<div class="seg-nav" style="margin-bottom:10px">
    <a href="javascript:void(0)" onclick="switchTab('overview')" class="sn" id="nav-overview" style="background:{theme['accent']};color:#fff;font-weight:600">📊 总览</a>
    <a href="javascript:void(0)" onclick="switchTab('stocks')" class="sn" id="nav-stocks">📋 个股分析</a>
</div>

<!-- ════════════════ TAB: 总览 ════════════════ -->
<div class="tab-content active" id="tab-overview">

<!-- 1. Key Metrics Dashboard -->
<div class="dashboard-grid">
    <div class="dashboard-item">
        <div class="d-label">全球市场规模</div>
        <div class="d-value">{scale.get('global_2025', 'N/A')}</div>
        <div class="d-sub">2025E</div>
    </div>
    <div class="dashboard-item">
        <div class="d-label">中国市场</div>
        <div class="d-value">{scale.get('china_2025', 'N/A')}</div>
        <div class="d-sub">2025E</div>
    </div>
    <div class="dashboard-item">
        <div class="d-label">复合增速</div>
        <div class="d-value">{scale.get('growth_cagr', 'N/A')}</div>
        <div class="d-sub">CAGR</div>
    </div>
    <div class="dashboard-item">
        <div class="d-label">覆盖公司</div>
        <div class="d-value">{total_companies}</div>
        <div class="d-sub">家上市公司</div>
    </div>
    <div class="dashboard-item">
        <div class="d-label">卡脖子环节</div>
        <div class="d-value">{total_bottlenecks}</div>
        <div class="d-sub">个瓶颈项</div>
    </div>
    <div class="dashboard-item">
        <div class="d-label">平均进口依赖</div>
        <div class="d-value">{avg_dep}%</div>
        <div class="d-sub">国产替代空间</div>
    </div>
    <div class="dashboard-item" style="border-top-color:#38a169">
        <div class="d-label">🟢 链内公司总市值</div>
        <div class="d-value">{chain_mcap_s}</div>
        <div class="d-sub">基于实时行情汇总</div>
    </div>
    <div class="dashboard-item" style="border-top-color:#667eea">
        <div class="d-label">🔵 链内平均 PE</div>
        <div class="d-value">{avg_pe_chain}</div>
        <div class="d-sub">剔除极端值后</div>
    </div>
    <div class="dashboard-item" style="border-top-color:#e94560">
        <div class="d-label">📈 平均营收增速</div>
        <div class="d-value">{avg_rev_growth}%</div>
        <div class="d-sub">基于最新财报</div>
    </div>
</div>

<!-- 2. Market Scale Bar Chart -->
<div class="over">
    <h3>📊 市场规模对比 (细分环节)</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">全球 vs 中国市场规模，展示各环节的国产替代空间</p>
    <div class="chart-box" id="scaleChart"></div>
</div>

<!-- 3. Growth + Pie side by side -->
<div class="chart-row">
    <div class="over" style="margin-bottom:0">
        <h3>📈 各环节增速对比 (CAGR)</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">红色虚线 = 产业链整体平均增速</p>
        <div class="chart-box" id="growthChart"></div>
    </div>
    <div class="over" style="margin-bottom:0">
        <h3>🧩 全球市场价值分布</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">各细分环节在全球市场中的价值占比</p>
        <div class="chart-box chart-box-sm" id="pieChart" style="height:300px"></div>
    </div>
</div>

<!-- 4. Bottleneck Radar Chart -->
{bt_data and f'''
<div class="over">
    <h3>⚠️ 卡脖子全景雷达 — 各环节进口依赖度</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">🔴 ≥90% 极度依赖 &nbsp;·&nbsp; 🟠 60-89% 高度依赖 &nbsp;·&nbsp; 🟡 &lt;60% 部分依赖</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div class="chart-box" id="radarChart" style="height:380px"></div>
        <div>
            <div class="chart-box chart-box-sm" id="depBarChart" style="height:380px"></div>
        </div>
    </div>
</div>''' or ''}

<!-- 5. Import Dependency vs Timeline Matrix -->
{bt_data and f'''
<div class="over">
    <h3>🕐 卡脖子替代时间线 &amp; 优先级矩阵</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">横轴 = 替代时间线 &nbsp;·&nbsp; 纵轴 = 进口依赖度 &nbsp;·&nbsp; 气泡大小 = 市场影响</p>
    <div class="chart-box" id="timelineMatrixChart"></div>
</div>''' or ''}

<!-- 6. Bottleneck Detail Table -->
{bottleneck_rows and f'''
<div class="sec">
    <div class="sec-hd"><h2>⚠️ 卡脖子核心瓶颈 — 详细拆解</h2></div>
    <div class="sec-bd">
        <table class="ctable">
            <thead><tr><th>瓶颈环节</th><th style="text-align:center">进口依赖</th><th>核心壁垒</th><th>国内替代</th><th style="text-align:center">替代时间</th></tr></thead>
            <tbody>{bottleneck_rows}</tbody>
        </table>
    </div>
</div>''' or ''}

<!-- 7. Cross-chain Dependencies -->
{cross_items and f'''
<div class="over">
    <h3>🔗 跨链依赖 / 关联产业</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:6px">本产业链与以下产业存在强关联关系：</p>
    <ul>{cross_items}</ul>
</div>''' or ''}

<!-- 8. Segment Real-Data Aggregation (Layer 4) -->
{has_multiple_segments and f'''
<div class="over">
    <h3>📊 细分环节实时数据聚合</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">基于实时行情+财报，按产业链环节聚合分析。总市值反映资本关注度，营收增速反映成长性，毛利率反映盈利能力。</p>
    <div class="chart-box" id="segStatsChart" style="height:{max(240, len(seg_stats) * 50 + 60)}px"></div>
</div>''' or ''}

<!-- 9. PE Distribution + Market Concentration (Layers 5+6) -->
<div class="chart-row">
    <div class="over" style="margin-bottom:0">
        <h3>📈 PE 估值分布</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">链内公司 PE (市盈率) 分布区间，了解整体估值水平</p>
        <div class="chart-box" id="peHistChart" style="height:260px"></div>
    </div>
    <div class="over" style="margin-bottom:0">
        <h3>🧮 市场集中度</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">Top 5 公司市值占全链比例 — {"CR5=" + str(cr5) + "% 高集中度" if cr5 > 60 else ("CR5=" + str(cr5) + "% 中等集中" if cr5 > 30 else "CR5=" + str(cr5) + "% 分散竞争")}</p>
        <div class="chart-box" id="crChart" style="height:260px"></div>
    </div>
</div>

<!-- 10. Revenue vs Market Cap Matrix (Layer 7) -->
{rev_mcap_data and f'''
<div class="over">
    <h3>💰 营收 vs 市值矩阵 — 价值发现</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">横轴=季度营收(亿元) &nbsp;·&nbsp; 纵轴=总市值(亿元) &nbsp;·&nbsp; 气泡大小=净利润 &nbsp;·&nbsp; 🟦 对角线上方=溢价(市值>营收) &nbsp;·&nbsp; 🔴 对角线下方=折价(市值&lt;营收)</p>
    <div class="chart-box" id="revMcapChart" style="height:380px"></div>
</div>''' or ''}

<!-- 11. Profitability by Segment + ROE (Layers 10+11) -->
{has_multiple_segments and f'''
<div class="chart-row">
    <div class="over" style="margin-bottom:0">
        <h3>💵 各环节盈利能力对比</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">🟦 平均毛利率 &nbsp;·&nbsp; 🟩 平均净利率 &nbsp;— 识别高附加值与薄利环节</p>
        <div class="chart-box" id="profitSegChart" style="height:260px"></div>
    </div>
    <div class="over" style="margin-bottom:0">
        <h3>📊 各环节 ROE 对比</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">ROE &gt; 15% = 优质 &nbsp;·&nbsp; 8-15% = 一般 &nbsp;·&nbsp; &lt; 8% = 回报偏低</p>
        <div class="chart-box" id="roeSegChart" style="height:260px"></div>
    </div>
</div>''' or ''}

<!-- 12. Multi-Quarter Revenue Trend (Layer 12) -->
{has_trend_data and f'''
<div class="over">
    <h3>💹 多季度营收趋势 (Top 6)</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">展示龙头公司近几个季度的营收变化趋势，红绿标识反映产业周期方向</p>
    <div class="chart-box" id="trendChart" style="height:380px"></div>
</div>''' or ''}

<!-- 13. Bottleneck-Company Exposure (Layer 14) -->
{_bt_exposure_html}

<!-- 14. Top Companies by Market Cap (from real market data) -->
{top_n and f'''
<div class="over">
    <h3>🏢 龙头企业排名 — 市值 Top 10</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">基于实时行情市值（人民币亿元），展示产业链内最大上市公司</p>
    <div class="chart-box" id="topCompaniesChart" style="height:320px"></div>
</div>''' or ''}

<!-- 15. PE vs Revenue Growth Scatter -->
{scatter_data and f'''
<div class="over">
    <h3>📈 估值 vs 成长性矩阵</h3>
    <p style="color:#64748b;font-size:13px;margin-bottom:8px">横轴 = PE (估值) &nbsp;·&nbsp; 纵轴 = 营收同比增速 &nbsp;·&nbsp; 气泡大小 = 利润 &nbsp;·&nbsp; 🟢 左上: 高成长低估值 (价值洼地) &nbsp;·&nbsp; 🔴 右下: 高估值低成长 (警惕)</p>
    <div class="chart-box" id="peGrowthChart" style="height:380px"></div>
</div>''' or ''}

<!-- 10. Growth Distribution + Performance Matrix -->
<div class="chart-row">
    {top_n and f'''
    <div class="over" style="margin-bottom:0">
        <h3>📊 营收增速分布</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">链内公司按最新季度营收增速分档</p>
        <div class="chart-box" id="growthDistChart" style="height:260px"></div>
    </div>''' or ''}
    {top15 and f'''
    <div class="over" style="margin-bottom:0">
        <h3>🔬 关键财务指标矩阵 (Top 15)</h3>
        <p style="color:#64748b;font-size:12px;margin-bottom:4px">颜色越深=数值越高 &nbsp;·&nbsp; PE 越高=越贵(红) &nbsp;·&nbsp; 营收/利润增速越高=成长越快(绿)</p>
        <div class="chart-box" id="perfHeatmapChart" style="height:260px"></div>
    </div>''' or ''}
</div>

<!-- 11. Segment Navigation + Details -->
<div class="seg-nav">{seg_nav}</div>

{segments_html}

</div><!-- /tab-overview -->

<!-- ════════════════ TAB: 个股分析 ════════════════ -->
<div class="tab-content" id="tab-stocks">

<h2 style="font-size:18px;color:#2d3748;margin-bottom:10px;padding:8px 0">📋 {len(companies)} 家重点公司深度分析</h2>
<p style="font-size:13px;color:#718096;margin-bottom:10px">点击下方公司名或上方表格中的蓝色链接，查看实时行情、K线走势、财务数据。</p>

<div class="stock-subnav">
    {stock_subnav_html}
</div>

{stock_cards_html}

</div><!-- /tab-stocks -->

</div>

<div class="ft">
    ⚠️ 本报告基于公开数据自动生成, 仅供研究参考, 不构成投资建议.<br>
    数据来源: TrendForce, IC Insights, SIA, CPCA, CAAM, 公司年报, Wind · {now}<br>
    生成工具: <a href="#">chain-analysis skill</a> · 用 <code>--chain</code> 切换产业链
</div>

<script>
var _coCodes = [{', '.join(f"'{c}'" for c in stock_code_list)}];

function switchTab(tab) {{
  if(_coCodes.indexOf(tab) !== -1) {{
    switchToStock(tab);
    return;
  }}
  document.querySelectorAll('.tab-content').forEach(function(el){{el.classList.remove('active')}});
  document.querySelectorAll('.sn').forEach(function(el){{el.style.background='';el.style.color='';el.style.fontWeight=''}});
  var tc = document.getElementById('tab-' + tab);
  if(tc) tc.classList.add('active');
  var na = document.getElementById('nav-' + tab);
  if(na) {{ na.style.background='{theme["accent"]}'; na.style.color='#fff'; na.style.fontWeight='600'; }}
  if(tab === 'overview') {{
    _coCodes.forEach(function(c){{
      var el = document.getElementById('co_' + c);
      if(el) el.style.display = '';
    }});
  }}
  setTimeout(function(){{
    document.querySelectorAll('.chart-box').forEach(function(cb){{
      var ch = echarts.getInstanceByDom(cb);
      if(ch) ch.resize();
    }});
  }}, 200);
}}

function switchToStock(code) {{
  document.querySelectorAll('.tab-content').forEach(function(el){{el.classList.remove('active')}});
  document.querySelectorAll('.sn').forEach(function(el){{el.style.background='';el.style.color='';el.style.fontWeight=''}});
  document.getElementById('tab-stocks').classList.add('active');
  var na = document.getElementById('nav-stocks');
  if(na) {{ na.style.background='{theme["accent"]}'; na.style.color='#fff'; na.style.fontWeight='600'; }}
  _coCodes.forEach(function(c){{
    var el = document.getElementById('co_' + c);
    if(el) el.style.display = c === code ? '' : 'none';
  }});
  setTimeout(function(){{
    var el = document.getElementById('co_' + code);
    if(el) el.scrollIntoView({{behavior:'smooth',block:'start'}});
    el.querySelectorAll('.chart-box').forEach(function(cb){{
      var ch = echarts.getInstanceByDom(cb);
      if(ch) ch.resize();
    }});
  }}, 200);
}}

// ══════════════════════════════════════════════
// Enhanced overview charts
// ══════════════════════════════════════════════
var chainAccent = '{theme["accent"]}';

// ── 1. Market Scale Bar Chart ──
var scaleData = {scale_chart_json};
var scChart = echarts.init(document.getElementById('scaleChart'));
scChart.setOption({{
    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(parms) {{
        var s = '<b>' + parms[0].axisValue + '</b><br/>';
        parms.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + scaleData[p.seriesIndex === 0 ? 'global' : 'china'][p.dataIndex] + '<br/>'; }});
        return s;
    }} }},
    legend: {{ data: ['全球规模', '中国规模'], bottom: 0, textStyle: {{ fontSize: 12 }} }},
    grid: {{ left: '3%', right: '4%', bottom: '22%', top: '6%', containLabel: true }},
    xAxis: {{ type: 'category', data: scaleData.names, axisLabel: {{ fontSize: 11, rotate: scaleData.names.length > 4 ? 25 : 0 }}, axisLine: {{ show: false }} }},
    yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 11, formatter: function(v){{return '$' + v + 'B';}} }} }},
    series: [
        {{ name: '全球规模', type: 'bar', data: scaleData.global.map(function(v) {{ var n=parseFloat(v.replace(/[^0-9.]/g,'')); var m=v.includes('T')?1000:v.includes('M')?0.001:1; return n*m; }}), itemStyle: {{ color: chainAccent, borderRadius: [4,4,0,0] }}, barMaxWidth: 40 }},
        {{ name: '中国规模', type: 'bar', data: scaleData.china.map(function(v) {{ var n=parseFloat(v.replace(/[^0-9.]/g,'')); var m=v.includes('T')?1000:v.includes('M')?0.001:1; return n*m; }}), itemStyle: {{ color: '#94a3b8', borderRadius: [4,4,0,0] }}, barMaxWidth: 40 }}
    ]
}});

// ── 2. Growth Rate Comparison Bar ──
var growthData = {growth_chart_json};
if(growthData.segments && growthData.segments.length > 0 && document.getElementById('growthChart')) {{
    var gChart = echarts.init(document.getElementById('growthChart'));
    var gNames = growthData.segments.map(function(s){{return s.name;}});
    var gVals = growthData.segments.map(function(s){{return s.cagr;}});
    var avgCagr = gVals.reduce(function(a,b){{return a+b;}},0) / gVals.length;
    gChart.setOption({{
        tooltip: {{ trigger: 'axis', formatter: function(parms) {{ return '<b>' + parms[0].axisValue + '</b><br/>' + parms[0].marker + ' CAGR: ' + parms[0].value + '%'; }} }},
        grid: {{ left: '3%', right: '4%', bottom: '18%', top: '12%', containLabel: true }},
        xAxis: {{ type: 'category', data: gNames, axisLabel: {{ fontSize: 10, rotate: gNames.length > 3 ? 20 : 0 }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 11, formatter: function(v){{return v + '%';}} }} }},
        series: [
            {{ name: 'CAGR', type: 'bar', data: gVals, itemStyle: {{ color: chainAccent, borderRadius: [4,4,0,0] }}, barMaxWidth: 40, label: {{ show: true, position: 'top', formatter: function(p){{return p.value + '%';}}, fontSize: 10 }} }},
            {{ name: '平均增速', type: 'line', data: gVals.map(function(){{return avgCagr;}}), lineStyle: {{ type: 'dashed', color: '#e53e3e', width: 2 }}, symbol: 'none', tooltip: {{ show: false }} }}
        ]
    }});
}}

// ── 3. Value Distribution Pie Chart ──
var pieData = {pie_chart_json};
if(pieData.segments && pieData.segments.length > 0 && document.getElementById('pieChart')) {{
    var colors = ['#667eea','#38a169','#e94560','#f6ad55','#63b3ed','#9f7aea','#fc8181','#68d391','#fbbf24','#a78bfa'];
    var pChart = echarts.init(document.getElementById('pieChart'));
    pChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p) {{ return '<b>' + p.name + '</b><br/>全球: ' + p.value; }} }},
        series: [{{
            type: 'pie', radius: ['30%','65%'], center: ['50%','50%'],
            data: pieData.segments.map(function(s,i){{ return {{ name: s.name, value: s.global, itemStyle: {{ color: colors[i % colors.length] }} }}; }}),
            label: {{ fontSize: 11, formatter: function(p){{ return p.name + '\\n' + p.value; }} }},
            emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' }} }}
        }}]
    }});
}}

// ── 4. Bottleneck Radar Chart ──
var radarData = {radar_json};
if(radarData.indicators && radarData.indicators.length > 0 && document.getElementById('radarChart')) {{
    var rChart = echarts.init(document.getElementById('radarChart'));
    rChart.setOption({{
        tooltip: {{ trigger: 'item' }},
        radar: {{
            indicator: radarData.indicators,
            center: ['50%','50%'],
            radius: '65%',
            shape: 'circle',
            splitArea: {{ areaStyle: {{ color: ['rgba(102,126,234,0.02)','rgba(102,126,234,0.06)','rgba(102,126,234,0.10)','rgba(102,126,234,0.14)'] }} }},
            axisLine: {{ lineStyle: {{ color: '#cbd5e1' }} }},
            splitLine: {{ lineStyle: {{ color: '#e2e8f0' }} }},
            name: {{ textStyle: {{ fontSize: 10, color: '#475569' }} }}
        }},
        series: [{{
            type: 'radar',
            data: [{{ value: radarData.values, name: '进口依赖度', areaStyle: {{ color: 'rgba(233,69,96,0.3)' }}, lineStyle: {{ color: '#e94560', width: 2 }}, itemStyle: {{ color: '#e94560' }} }}],
            symbol: 'circle',
            symbolSize: 6
        }}]
    }});
}}

// ── 5. Bottleneck Dependency Bar (horizontal) ──
if(radarData.indicators && radarData.indicators.length > 0 && document.getElementById('depBarChart')) {{
    var dBChart = echarts.init(document.getElementById('depBarChart'));
    var depLabels = radarData.indicators.map(function(d){{return d.name;}}).reverse();
    var depVals = radarData.values.slice().reverse();
    var depColors = depVals.map(function(v){{ return v >= 90 ? '#e94560' : v >= 60 ? '#f6ad55' : '#68d391'; }});
    dBChart.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(parms){{ return '<b>' + parms[0].name + '</b><br/>进口依赖: ' + parms[0].value + '%'; }} }},
        grid: {{ left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true }},
        xAxis: {{ type: 'value', max: 100, splitLine: {{ show: false }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '%';}} }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'category', data: depLabels, axisLabel: {{ fontSize: 10 }}, axisLine: {{ show: false }}, axisTick: {{ show: false }} }},
        series: [{{
            type: 'bar', data: depVals.map(function(v,i){{ return {{ value: v, itemStyle: {{ color: depColors[i], borderRadius: [0,4,4,0] }} }}; }}), barMaxWidth: 18,
            label: {{ show: true, position: 'right', formatter: function(p){{return p.value + '%';}}, fontSize: 10, fontWeight: 'bold' }}
        }}]
    }});
}}

// ── 6. Timeline Matrix (bubble scatter) ──
if(radarData.indicators && radarData.indicators.length > 0 && document.getElementById('timelineMatrixChart')) {{
    var tmChart = echarts.init(document.getElementById('timelineMatrixChart'));
    // Timeline mapping
    var tmMap = {{ '已突破': 1, '2026': 2, '2026-2027': 3, '2027': 3.5, '2027-2028': 4, '2028+': 5, '2030+': 6 }};
    var rawBt = {json.dumps(bt_data, ensure_ascii=False)};
    var tmData = rawBt.map(function(b, i) {{
        var tm = 3;
        for(var k in tmMap) {{ if(b.timeline.indexOf(k) !== -1) {{ tm = tmMap[k]; break; }} }}
        var dep = parseInt(b.import_dep.replace(/[^0-9]/g,'')) || 50;
        return {{ value: [tm, dep, 80 + Math.random() * 40], name: b.item }};
    }});
    tmChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p){{ return '<b>' + p.data.name + '</b><br/>进口依赖: ' + p.data.value[1] + '%<br/>替代时间轴: ' + ['','已突破','2026','2026-27','2027','2027-28','2028+','2030+'][p.data.value[0]]; }} }},
        grid: {{ left: '3%', right: '6%', bottom: '12%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'value', min: 0.5, max: 6.5, splitLine: {{ show: false }}, axisLabel: {{ fontSize: 11, formatter: function(v){{ return ['','已突破','2026','2026-27','2027','2027-28','2028+','2030+'][Math.round(v)] || ''; }} }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', min: 0, max: 100, splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 11, formatter: function(v){{return v + '%';}} }}, name: '进口依赖度', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }} }},
        series: [{{
            type: 'scatter', data: tmData, symbolSize: function(v){{ return v[2]/3; }},
            itemStyle: {{ color: function(p){{ var v=p.data.value[1]; return v>=90?'#e94560':v>=60?'#f6ad55':'#68d391'; }} }},
            label: {{ show: true, formatter: function(p){{ return p.data.name.slice(0,6); }}, fontSize: 9, position: 'right' }}
        }}]
    }});
}}

// ══════════════════════════════════════════════
// Enhanced real-data analysis charts
// ══════════════════════════════════════════════

// ── 7. Top Companies by Market Cap (horizontal bar) ──
var topData = {top_companies_json};
if(topData.length > 0 && document.getElementById('topCompaniesChart')) {{
    var tcChart = echarts.init(document.getElementById('topCompaniesChart'));
    var tcNames = topData.map(function(d){{return d.name;}}).reverse();
    var tcVals = topData.map(function(d){{return d.mcap;}}).reverse();
    tcChart.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(p){{return '<b>' + p[0].name + '</b><br/>市值: ' + p[0].value + '亿';}} }},
        grid: {{ left: '3%', right: '10%', bottom: '3%', top: '5%', containLabel: true }},
        xAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '亿';}} }} }},
        yAxis: {{ type: 'category', data: tcNames, axisLabel: {{ fontSize: 11, fontWeight: 'bold' }}, axisLine: {{ show: false }}, axisTick: {{ show: false }} }},
        series: [{{ type: 'bar', data: tcVals, itemStyle: {{ color: chainAccent, borderRadius: [0,4,4,0] }}, barMaxWidth: 24, label: {{ show: true, position: 'right', formatter: function(p){{return p.value + '亿';}}, fontSize: 10 }} }}]
    }});
}}

// ── 8. PE vs Revenue Growth Bubble Scatter ──
var scatterData = {pe_growth_json};
if(scatterData.length > 0 && document.getElementById('peGrowthChart')) {{
    var pgChart = echarts.init(document.getElementById('peGrowthChart'));
    pgChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p){{return '<b>' + p.data.name + '</b><br/>PE: ' + p.data.value[0] + '<br/>营收增速: ' + p.data.value[1] + '%<br/>利润: ' + p.data.value[2] + '亿<br/>市值: ' + p.data.value[3] + '亿';}} }},
        grid: {{ left: '3%', right: '6%', bottom: '14%', top: '8%', containLabel: true }},
        xAxis: {{ type: 'value', name: 'PE (估值)', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ show: false }}, axisLabel: {{ fontSize: 10 }} }},
        yAxis: {{ type: 'value', name: '营收同比增速 %', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '%';}} }} }},
        series: [{{
            type: 'scatter', data: scatterData.map(function(d){{return {{ value: [d.pe, d.rev_yoy, d.profit, d.mcap], name: d.name }}; }}),
            symbolSize: function(v){{return Math.max(8, Math.min(40, Math.abs(v[2]) * 1.5 + 8));}},
            itemStyle: {{ color: function(p){{var pe=p.data.value[0],gr=p.data.value[1];return gr>20&&pe<30?'#38a169':gr<0&&pe>50?'#e94560':'#667eea';}} }},
            label: {{ show: true, formatter: function(p){{return p.data.name.slice(0,5);}}, fontSize: 9, position: 'right' }}
        }}]
    }});
}}

// ── 9. Revenue Growth Distribution (pie) ──
var growthDist = {growth_dist_json};
if(growthDist.length > 0 && document.getElementById('growthDistChart')) {{
    var gdChart = echarts.init(document.getElementById('growthDistChart'));
    var gdColors = ['#38a169','#667eea','#e94560','#cbd5e1'];
    gdChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p){{return p.name + '<br/>' + p.value + ' 家 (' + p.percent + '%)';}} }},
        series: [{{
            type: 'pie', radius: ['40%','70%'], center: ['50%','55%'],
            data: growthDist.map(function(d,i){{return {{name:d.name, value:d.count, itemStyle:{{color:gdColors[i]}} }};}}),
            label: {{ fontSize: 11, formatter: function(p){{return p.name + '\\n' + p.value + '家';}} }},
            emphasis: {{ itemStyle: {{ shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.2)' }} }}
        }}]
    }});
}}

// ── 10. Performance Heatmap ──
var hmCompanies = {perf_heatmap_json};
var hmValues = {heatmap_values_json};
if(hmCompanies.metrics && hmCompanies.companies.length > 0 && document.getElementById('perfHeatmapChart')) {{
    var phChart = echarts.init(document.getElementById('perfHeatmapChart'));
    var hmData = [];
    hmCompanies.companies.forEach(function(cName, ci) {{
        hmCompanies.metrics.forEach(function(mName, mi) {{
            hmData.push([mi, ci, hmValues[ci][mi]]);
        }});
    }});
    phChart.setOption({{
        tooltip: {{ position: 'top', formatter: function(p){{return hmCompanies.companies[p.data.value[1]] + ' - ' + hmCompanies.metrics[p.data.value[0]] + '<br/>' + p.data.value[2];}} }},
        grid: {{ left: '8%', right: '4%', bottom: '8%', top: '4%', containLabel: true }},
        xAxis: {{ type: 'category', data: hmCompanies.metrics, splitArea: {{ show: true }}, axisLabel: {{ fontSize: 10, rotate: 15 }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'category', data: hmCompanies.companies, splitArea: {{ show: true }}, axisLabel: {{ fontSize: 10 }}, axisLine: {{ show: false }} }},
        visualMap: {{ min: -50, max: 100, inRange: {{ color: ['#e94560','#f6ad55','#fefcbf','#68d391','#38a169'] }}, calculable: true, orient: 'horizontal', left: 'center', bottom: 0 }},
        series: [{{
            type: 'heatmap', data: hmData,
            label: {{ show: true, fontSize: 9, color: '#1e293b' }},
            emphasis: {{ itemStyle: {{ shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.2)' }} }}
        }}]
    }});
}}

// ══════════════════════════════════════════════
// New deep analysis charts (Layers 4-12, 14)
// ══════════════════════════════════════════════

// ── 11. Segment-Level Real Data Aggregation (Layer 4) ──
var segStats = {seg_stats_json};
if(Object.keys(segStats).length > 1 && document.getElementById('segStatsChart')) {{
    var ssChart = echarts.init(document.getElementById('segStatsChart'));
    var ssNames = Object.keys(segStats);
    var ssMcap = ssNames.map(function(n){{return segStats[n].total_mcap;}});
    var ssGrowth = ssNames.map(function(n){{return segStats[n].avg_rev_yoy;}});
    var ssMargin = ssNames.map(function(n){{return segStats[n].avg_margin_gross;}});
    var ssCounts = ssNames.map(function(n){{return segStats[n].count;}});
    ssChart.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(parms){{
            var idx = parms[0].dataIndex;
            var n = ssNames[idx];
            return '<b>' + n + '</b><br/>' +
                '公司数: ' + ssCounts[idx] + '<br/>' +
                '总市值: ' + ssMcap[idx] + '亿<br/>' +
                '平均PE: ' + segStats[n].avg_pe + '<br/>' +
                '营收增速: ' + ssGrowth[idx] + '%<br/>' +
                '毛利率: ' + ssMargin[idx] + '%<br/>' +
                'ROE: ' + segStats[n].avg_roe + '%';
        }} }},
        legend: {{ data: ['总市值(亿)', '营收增速%', '毛利率%'], bottom: 0, textStyle: {{ fontSize: 11 }} }},
        grid: {{ left: '3%', right: '4%', bottom: '20%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'category', data: ssNames, axisLabel: {{ fontSize: 10, rotate: ssNames.length > 4 ? 20 : 0 }}, axisLine: {{ show: false }} }},
        yAxis: [
            {{ type: 'value', name: '市值(亿)', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10 }} }},
            {{ type: 'value', name: '%', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ show: false }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '%';}} }} }}
        ],
        series: [
            {{ name: '总市值(亿)', type: 'bar', data: ssMcap, yAxisIndex: 0, itemStyle: {{ color: '#667eea', borderRadius: [4,4,0,0] }}, barMaxWidth: 30 }},
            {{ name: '营收增速%', type: 'bar', data: ssGrowth, yAxisIndex: 1, itemStyle: {{ color: '#38a169', borderRadius: [4,4,0,0] }}, barMaxWidth: 30 }},
            {{ name: '毛利率%', type: 'bar', data: ssMargin, yAxisIndex: 1, itemStyle: {{ color: '#63b3ed', borderRadius: [4,4,0,0] }}, barMaxWidth: 30 }}
        ]
    }});
}}

// ── 12. PE Distribution Histogram (Layer 5) ──
var peHist = {pe_hist_json};
if(document.getElementById('peHistChart')) {{
    var phChart2 = echarts.init(document.getElementById('peHistChart'));
    var peColors = ['#e94560','#f6ad55','#38a169','#667eea','#9f7aea','#e94560'];
    phChart2.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(parms){{
            var idx = parms[0].dataIndex;
            var names = peHist.companies[idx] || [];
            return '<b>' + peHist.categories[idx] + '</b><br/>' + parms[0].value + ' 家<br/>' +
                (names.length > 0 ? '<small>' + names.slice(0,8).join(', ') + (names.length>8?'...':'') + '</small>' : '');
        }} }},
        grid: {{ left: '3%', right: '4%', bottom: '10%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'category', data: peHist.categories, axisLabel: {{ fontSize: 11, fontWeight: 'bold' }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10 }} }},
        series: [{{
            type: 'bar', data: peHist.values.map(function(v,i){{return {{value:v, itemStyle:{{color:peColors[i]}}}};}}),
            barMaxWidth: 40, label: {{ show: true, position: 'top', fontSize: 11, fontWeight: 'bold' }}
        }}]
    }});
}}

// ── 13. Market Concentration CR5 (Layer 6) ──
var crData = {cr_json};
if(crData.data.length > 0 && document.getElementById('crChart')) {{
    var crChart = echarts.init(document.getElementById('crChart'));
    crChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p){{return '<b>' + p.name + '</b><br/>市值占比: ' + p.value + '%';}} }},
        graphic: [{{
            type: 'text', left: 'center', top: 'center', style: {{
                text: 'CR5\\n' + crData.cr5 + '%', textAlign: 'center', fill: crData.cr5 > 60 ? '#e94560' : crData.cr5 > 30 ? '#f6ad55' : '#38a169',
                fontSize: 14, fontWeight: 'bold', lineHeight: 20
            }}
        }}],
        series: [{{
            type: 'pie', radius: ['45%','70%'], center: ['50%','55%'],
            data: crData.data, label: {{ fontSize: 11, formatter: function(p){{return p.name + '\\n' + p.value + '%';}} }},
            emphasis: {{ itemStyle: {{ shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.2)' }} }}
        }}]
    }});
}}

// ── 14. Revenue vs Market Cap Scatter (Layer 7) ──
var revMcap = {rev_mcap_json};
if(revMcap.length > 0 && document.getElementById('revMcapChart')) {{
    var rmChart = echarts.init(document.getElementById('revMcapChart'));
    var rmMax = 0;
    revMcap.forEach(function(d){{rmMax = Math.max(rmMax, d.revenue, d.mcap);}});
    rmChart.setOption({{
        tooltip: {{ trigger: 'item', formatter: function(p){{
            var d = p.data.value;
            return '<b>' + p.data.name + '</b><br/>营收: ' + d[0] + '亿<br/>市值: ' + d[1] + '亿<br/>净利: ' + d[2] + '亿<br/>毛利率: ' + d[3] + '%';
        }} }},
        grid: {{ left: '3%', right: '6%', bottom: '12%', top: '8%', containLabel: true }},
        xAxis: {{ type: 'value', name: '季度营收(亿元)', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ show: false }}, axisLabel: {{ fontSize: 10 }} }},
        yAxis: {{ type: 'value', name: '总市值(亿元)', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10 }} }},
        series: [{{
            type: 'scatter', data: revMcap.map(function(d){{var diag=d.revenue>0?d.mcap/d.revenue:1; return {{value:[d.revenue,d.mcap,d.profit,d.margin_gross],name:d.name}};}}),
            symbolSize: function(v){{return Math.max(10, Math.min(40, Math.abs(v[2]) * 2 + 10));}},
            itemStyle: {{ color: function(p){{var d=p.data.value;return d[1]>d[0]*1.2?'#667eea':'#e94560';}} }},
            label: {{ show: true, formatter: function(p){{return p.data.name.slice(0,5);}}, fontSize: 9, position: 'right' }}
        }}]
    }});
}}

// ── 15. Profitability by Segment (Layer 10) ──
var segStats2 = {seg_stats_json};
var ssNames2 = Object.keys(segStats2);
if(ssNames2.length > 1 && document.getElementById('profitSegChart')) {{
    var psChart = echarts.init(document.getElementById('profitSegChart'));
    var grossVals = ssNames2.map(function(n){{return segStats2[n].avg_margin_gross;}});
    var netVals = ssNames2.map(function(n){{return segStats2[n].avg_margin_net;}});
    psChart.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(parms){{
            var idx = parms[0].dataIndex;
            return '<b>' + ssNames2[idx] + '</b><br/>' +
                parms[0].marker + ' 毛利率: ' + grossVals[idx] + '%<br/>' +
                (parms[1] ? parms[1].marker + ' 净利率: ' + netVals[idx] + '%' : '');
        }} }},
        grid: {{ left: '3%', right: '4%', bottom: '10%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'category', data: ssNames2, axisLabel: {{ fontSize: 10, rotate: ssNames2.length > 3 ? 15 : 0 }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '%';}} }} }},
        series: [
            {{ name: '毛利率', type: 'bar', data: grossVals, itemStyle: {{ color: '#667eea', borderRadius: [4,4,0,0] }}, barMaxWidth: 30 }},
            {{ name: '净利率', type: 'bar', data: netVals, itemStyle: {{ color: '#38a169', borderRadius: [4,4,0,0] }}, barMaxWidth: 30 }}
        ]
    }});
}}

// ── 16. ROE by Segment (Layer 11) ──
if(ssNames2.length > 1 && document.getElementById('roeSegChart')) {{
    var roeChart = echarts.init(document.getElementById('roeSegChart'));
    var roeVals = ssNames2.map(function(n){{return segStats2[n].avg_roe;}});
    roeChart.setOption({{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: function(p){{return '<b>' + p[0].name + '</b><br/>ROE: ' + p[0].value + '%';}} }},
        grid: {{ left: '3%', right: '8%', bottom: '10%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'category', data: ssNames2, axisLabel: {{ fontSize: 10, rotate: ssNames2.length > 3 ? 15 : 0 }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10, formatter: function(v){{return v + '%';}} }} }},
        series: [{{
            type: 'bar', data: roeVals.map(function(v){{return {{value:v, itemStyle:{{color: v>=15?'#38a169':v>=8?'#667eea':'#e94560'}}}};}}),
            barMaxWidth: 40, label: {{ show: true, position: 'top', formatter: function(p){{return p.value + '%';}}, fontSize: 10, fontWeight: 'bold' }}
        }}]
    }});
}}

// ── 17. Multi-Quarter Revenue Trend (Layer 12) ──
var trendData = {trend_revenue_json};
var trendCodes = Object.keys(trendData);
if(trendCodes.length > 0 && document.getElementById('trendChart')) {{
    var tChart = echarts.init(document.getElementById('trendChart'));
    var trendColors = ['#667eea','#e94560','#38a169','#f6ad55','#9f7aea','#63b3ed'];
    // Collect all quarters across all companies
    var allQuarters = new Set();
    trendCodes.forEach(function(code) {{
        trendData[code].revenues.forEach(function(q){{allQuarters.add(q.quarter);}});
    }});
    var sortedQuarters = Array.from(allQuarters).sort();
    var trendSeries = trendCodes.map(function(code, i) {{
        var revMap = {{}};
        trendData[code].revenues.forEach(function(q){{revMap[q.quarter] = q.value;}});
        return {{
            name: trendData[code].name,
            type: 'line', smooth: true,
            data: sortedQuarters.map(function(q){{return revMap[q] || null;}}),
            lineStyle: {{ width: 2, color: trendColors[i % trendColors.length] }},
            itemStyle: {{ color: trendColors[i % trendColors.length] }},
            symbol: 'circle', symbolSize: 6
        }};
    }});
    tChart.setOption({{
        tooltip: {{ trigger: 'axis', formatter: function(parms){{
            var s = '<b>' + parms[0].axisValue + '</b><br/>';
            parms.forEach(function(p){{ if(p.value !== null) s += p.marker + ' ' + p.seriesName + ': ' + p.value + '亿<br/>'; }});
            return s;
        }} }},
        legend: {{ data: trendCodes.map(function(c){{return trendData[c].name;}}), bottom: 0, textStyle: {{ fontSize: 11 }} }},
        grid: {{ left: '3%', right: '4%', bottom: '22%', top: '6%', containLabel: true }},
        xAxis: {{ type: 'category', data: sortedQuarters, axisLabel: {{ fontSize: 11 }}, axisLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: '营收(亿元)', nameTextStyle: {{ fontSize: 10, color: '#94a3b8' }}, splitLine: {{ lineStyle: {{ type: 'dashed', color: '#e2e8f0' }} }}, axisLabel: {{ fontSize: 10 }} }},
        series: trendSeries
    }});
}}

// ── Responsive resize ──
window.addEventListener('resize', function() {{
    [scChart, gChart, pChart, rChart, dBChart, tmChart, ssChart, phChart2, crChart, rmChart, psChart, roeChart, tChart, tcChart, pgChart, gdChart, phChart].forEach(function(ch) {{ if(ch) ch.resize(); }});
}});
</script>
</body>
</html>"""


def list_chains():
    """Print available chains from templates."""
    print("Available predefined chains:")
    print("=" * 62)
    for cid, tmpl in CHAIN_TEMPLATES.items():
        if not tmpl.get("icon"):
            continue
        scale = format_market_scale(cid)
        seg_count = len(tmpl.get("segments", []))
        print(f"  {tmpl['icon']}  {tmpl['name']}  ({tmpl.get('name_en', '')})")
        print(f"      Global: {scale.get('global_2025', 'N/A')}, China: {scale.get('china_2025', 'N/A')}")
        print(f"      {seg_count} segments (companies discovered dynamically at generation)")
        print()
    print("---")
    print("💡 You can also analyze ANY chain not listed above:")
    print("   python chain_report.py --chain 光伏 --output 光伏产业链.html")
    print("   python chain_report.py --chain 机器人 --output 机器人产业链.html")
    print("   The system will auto-discover the chain structure via industry boards.")


def show_company_in_chain(chain_id: str, company_code: str):
    """Show a company's position in the chain (terminal output)."""
    if chain_id and chain_id not in CHAIN_TEMPLATES:
        print(f"Chain '{chain_id}' not found.")
        return
    
    chains_to_check = [chain_id] if chain_id else list(CHAIN_TEMPLATES.keys())
    found_any = False
    
    for cid in chains_to_check:
        tmpl = CHAIN_TEMPLATES[cid]
        if not tmpl.get("icon"):
            continue
        # Discover companies and check membership
        companies = discover_chain_companies(cid, max_companies=50)
        for comp in companies:
            if comp["code"] == company_code or comp["code"].endswith(company_code):
                found_any = True
                print(f"\n{'=' * 62}")
                print(f"  {tmpl['icon']} {tmpl['name']} — Company Found")
                print(f"{'=' * 62}")
                print(f"  🏢 Company:  {comp['name']} ({comp['code']})")
                print(f"\n  🔍 For full analysis: generate HTML report with --chain {cid} --output report.html")
                print(f"  🔍 For deep-dive: python ../stock-analysis/scripts/stock_report.py --symbol {comp['code']}")
                print()
    
    if not found_any:
        print(f"❌ Company {company_code} not found in any chain.")


def main():
    parser = argparse.ArgumentParser(description="Universal Chain Analysis Report Generator (HTML only)")
    parser.add_argument("--list", action="store_true", help="List predefined chains")
    parser.add_argument("--chain", "-c", help="Any chain name (e.g. 'storage', '光伏', '机器人')")
    parser.add_argument("--output", "-o", help="Output HTML file path (default: stdout)")
    parser.add_argument("--company", help="Show company position in chain by stock code")
    args = parser.parse_args()

    if args.list:
        list_chains()
        return

    if args.company:
        show_company_in_chain(args.chain, args.company)
        return

    if not args.chain:
        print("Error: --chain required. Use --list to see predefined chains.")
        print("Examples:")
        print("  python chain_report.py --chain storage --output storage_chain.html")
        print("  python chain_report.py --chain 光伏 --output 光伏产业链.html")
        print("  python chain_report.py --chain 机器人 --output 机器人产业链.html")
        sys.exit(1)

    html = generate_html(args.chain)

    if args.output:
        out_dir = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        name = CHAIN_TEMPLATES.get(args.chain, {}).get("name", f"{args.chain}产业链")
        print(f"✅ HTML report generated: {args.output}")
        print(f"   {name} | companies discovered dynamically")
        print(f"   Open in browser to view interactive report")
    else:
        print(html)


if __name__ == "__main__":
    main()
