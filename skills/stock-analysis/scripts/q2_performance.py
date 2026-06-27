#!/usr/bin/env python3
"""
Q2 2026 Quarterly Performance Report — Multi-Chain Analysis.

Analyzes the latest available quarterly financial data across major industry chains,
ranks companies by composite performance score, and generates a structured HTML report
with company deep-dive cards.

Industry Chains Covered:
  - AI算力/半导体: Semiconductor & AI computing
  - PCB/电子制造: PCB manufacturing & electronics
  - 新能源汽车: New energy vehicles & battery
  - 消费电子: Consumer electronics
  - 光伏/储能: Solar & energy storage
  - 医药生物: Biomedicine & healthcare

Output: HTML report with per-chain ranking, company analysis cards, K-line charts, news.
"""

import json
import os
import re
import sys
import urllib.request
import time
from datetime import datetime

try:
    import akshare as ak
    _HAS_AKSHARE = True
except ImportError:
    ak = None
    _HAS_AKSHARE = False


# ============================================================
# INDUSTRY CHAINS — representative A-share companies
# ============================================================

INDUSTRY_CHAINS = [
    {
        "name": "AI算力/半导体",
        "icon": "🧠",
        "description": "AI芯片、半导体设备、材料、封装测试。受益于AI算力爆发和国产替代双重驱动。",
        "companies": [
            {"code": "002371", "market": "sz", "name": "北方华创", "biz": "半导体设备（刻蚀/薄膜/清洗）龙头", "reason": "国产替代核心标的，收入利润持续高增"},
            {"code": "688012", "market": "sh", "name": "中微公司", "biz": "刻蚀+MOCVD设备龙头", "reason": "CCP/ICP刻蚀设备进入5nm产线"},
            {"code": "603501", "market": "sh", "name": "韦尔股份", "biz": "CIS图像传感器全球第三", "reason": "汽车+安防CIS驱动增长"},
            {"code": "300661", "market": "sz", "name": "圣邦股份", "biz": "模拟芯片设计龙头", "reason": "信号链+电源管理芯片国产化先锋"},
            {"code": "688008", "market": "sh", "name": "澜起科技", "biz": "内存接口芯片全球龙头", "reason": "DDR5渗透率提升带动量价齐升"},
            {"code": "603986", "market": "sh", "name": "兆易创新", "biz": "NOR Flash + MCU国内龙头", "reason": "存储+MCU双轮驱动，AI端侧受益"},
            {"code": "300782", "market": "sz", "name": "卓胜微", "biz": "射频前端芯片龙头", "reason": "射频模组放量，国产替代加速"},
            {"code": "688981", "market": "sh", "name": "中芯国际", "biz": "中国大陆最大晶圆代工厂", "reason": "产能利用率回升，先进制程突破"},
            {"code": "002185", "market": "sz", "name": "华天科技", "biz": "封装测试龙头", "reason": "先进封装(Chiplet)需求爆发"},
            {"code": "688072", "market": "sh", "name": "拓荆科技", "biz": "CVD/PVD薄膜沉积设备", "reason": "高端薄膜设备国产替代领军者"},
        ]
    },
    {
        "name": "PCB/电子制造",
        "icon": "🔌",
        "description": "PCB制造、覆铜板、铜箔、电子组装。AI服务器驱动高端PCB结构性紧缺。",
        "companies": [
            {"code": "002463", "market": "sz", "name": "沪电股份", "biz": "AI服务器PCB核心供应商", "reason": "NVIDIA直供，28层+背板量价齐升"},
            {"code": "002916", "market": "sz", "name": "深南电路", "biz": "通信背板+IC载板双龙头", "reason": "FCBGA载板突破，封装基板国内第一"},
            {"code": "002938", "market": "sz", "name": "鹏鼎控股", "biz": "全球营收最大PCB制造商", "reason": "SLP类载板领先，Apple核心供应链"},
            {"code": "002384", "market": "sz", "name": "东山精密", "biz": "FPC全球前三", "reason": "Multek整合完成，多元布局"},
            {"code": "300476", "market": "sz", "name": "胜宏科技", "biz": "HDI+服务器PCB", "reason": "高阶HDI(4-5阶)用于AI加速卡，全球显卡板25%+"},
            {"code": "600183", "market": "sh", "name": "生益科技", "biz": "覆铜板(CCL)全球前三", "reason": "M8材料突破，高速CCL量价齐升"},
            {"code": "002600", "market": "sz", "name": "领益智造", "biz": "精密功能件全球龙头", "reason": "AI手机散热+屏蔽件量价齐升"},
            {"code": "603228", "market": "sh", "name": "景旺电子", "biz": "汽车电子PCB龙头", "reason": "汽车板自动化率95%，新能源车驱动"},
            {"code": "002436", "market": "sz", "name": "兴森科技", "biz": "PCB样板+IC封装基板", "reason": "FCBGA(ABF载板)国内唯一试产"},
            {"code": "688519", "market": "sh", "name": "南亚新材", "biz": "M7高速CCL量产", "reason": "M7等级CCL国内首家，服务器CCL高增"},
        ]
    },
    {
        "name": "新能源汽车",
        "icon": "🚗",
        "description": "整车、动力电池、电驱系统、智能驾驶。NEV渗透率持续提升，海外市场拓展。",
        "companies": [
            {"code": "300750", "market": "sz", "name": "宁德时代", "biz": "全球动力电池龙头", "reason": "市占率持续提升，钠离子/固态电池布局"},
            {"code": "002594", "market": "sz", "name": "比亚迪", "biz": "新能源汽车+电池垂直整合", "reason": "DM-i 5.0技术，海外出口加速"},
            {"code": "601689", "market": "sh", "name": "拓普集团", "biz": "NVH+底盘+热管理模块化供应商", "reason": "Tier0.5平台化战略，单车价值量提升"},
            {"code": "002920", "market": "sz", "name": "德赛西威", "biz": "智能座舱+智能驾驶龙头", "reason": "高算力域控量产，智驾渗透率提升"},
            {"code": "300124", "market": "sz", "name": "汇川技术", "biz": "电驱系统+工业自动化", "reason": "新能源车电驱龙头，工业自动化复苏"},
            {"code": "002709", "market": "sz", "name": "天赐材料", "biz": "电解液全球龙头", "reason": "六氟磷酸锂价格企稳，海外布局加速"},
            {"code": "300014", "market": "sz", "name": "亿纬锂能", "biz": "圆柱+方形+软包全路线电池", "reason": "大圆柱电池量产，储能业务高增"},
        ]
    },
    {
        "name": "消费电子",
        "icon": "📱",
        "description": "智能手机、AI PC、可穿戴设备。AI端侧创新驱动换机周期。",
        "companies": [
            {"code": "002475", "market": "sz", "name": "立讯精密", "biz": "精密制造+整机代工龙头", "reason": "Apple供应链核心，AI服务器连接器"},
            {"code": "002241", "market": "sz", "name": "歌尔股份", "biz": "声学+光学+VR/AR整机", "reason": "Pancake光学方案，VR/AR硬件复苏"},
            {"code": "300433", "market": "sz", "name": "蓝思科技", "biz": "玻璃盖板+外观件龙头", "reason": "AI手机外观件升级驱动单价提升"},
            {"code": "601138", "market": "sh", "name": "工业富联", "biz": "AI服务器+通信设备制造", "reason": "NVIDIA AI服务器主力代工厂"},
            {"code": "002273", "market": "sz", "name": "水晶光电", "biz": "光学滤光片+微棱镜龙头", "reason": "潜望式镜头/AI手机光学升级受益"},
        ]
    },
    {
        "name": "光伏/储能",
        "icon": "☀️",
        "description": "光伏组件、逆变器、储能系统。产能出清中，头部集中度提升。",
        "companies": [
            {"code": "300274", "market": "sz", "name": "阳光电源", "biz": "光伏逆变器+储能系统全球龙头", "reason": "逆变器出货全球第一，储能高速增长"},
            {"code": "601012", "market": "sh", "name": "隆基绿能", "biz": "硅片+组件双龙头", "reason": "BC电池技术领先，产能出清中韧性最强"},
            {"code": "688599", "market": "sh", "name": "天合光能", "biz": "光伏组件+分布式系统", "reason": "分布式+支架系统差异化竞争"},
            {"code": "688223", "market": "sh", "name": "晶科能源", "biz": "TOPCon组件全球出货第一", "reason": "N型TOPCon技术领先，美国产能布局"},
            {"code": "002459", "market": "sz", "name": "晶澳科技", "biz": "垂直一体化光伏龙头", "reason": "n型电池产能占比提升，海外渠道优势"},
        ]
    },
    {
        "name": "医药生物",
        "icon": "💊",
        "description": "创新药、CXO、医疗器械。集采影响边际减弱，创新出海驱动增长。",
        "companies": [
            {"code": "600276", "market": "sh", "name": "恒瑞医药", "biz": "创新药龙头", "reason": "多个创新药NDA，国际化授权持续推进"},
            {"code": "300760", "market": "sz", "name": "迈瑞医疗", "biz": "医疗器械平台龙头", "reason": "海外高端客户突破，生命信息+影像稳健"},
            {"code": "603259", "market": "sh", "name": "药明康德", "biz": "CXO全球龙头", "reason": "生物安全法案影响减弱，在手订单恢复"},
            {"code": "300015", "market": "sz", "name": "爱尔眼科", "biz": "眼科连锁医疗龙头", "reason": "屈光+视光双轮驱动，下沉市场拓展"},
            {"code": "000661", "market": "sz", "name": "长春高新", "biz": "生长激素龙头", "reason": "长效水针放量，儿科+成人双适应症拓展"},
        ]
    },
]


# ============================================================
# DATA FETCHING
# ============================================================

def fetch_tencent_real_time(companies):
    """Fetch real-time stock data from Tencent API."""
    if not companies:
        return {}
    market_codes = []
    for c in companies:
        m = c.get("market", "sz")
        code = c.get("code", "")
        market_codes.append(f"hk{code}" if m == "hk" else f"{m}{code}")
    url = "http://qt.gtimg.cn/q=" + ",".join(market_codes)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("gbk")
        results = {}
        for line in data.strip().split("\n"):
            if "~" not in line:
                continue
            parts = line.split("~")
            if len(parts) < 10:
                continue
            code = parts[2]
            try:
                price = float(parts[3]) if parts[3] else 0
                prev_close = float(parts[4]) if parts[4] else 0
                chg = (price - prev_close) / prev_close * 100 if prev_close else 0
                mcap = float(parts[44].strip()) if len(parts) > 44 and parts[44].strip() else 0
                pe = float(parts[39].strip()) if len(parts) > 39 and parts[39].strip() else 0
                name = parts[1] if parts[1] else ""
                results[code] = {"price": price, "change_pct": round(chg, 2), "mcap": mcap, "pe": pe, "name": name}
            except (ValueError, IndexError):
                continue
        return results
    except Exception as e:
        print(f"  [ERROR] Tencent API: {e}")
        return {}


def fetch_financial(code, market):
    """Fetch latest quarterly financial data from East Money (A-shares only)."""
    if market == "hk":
        return None
    secucode = f"{code}.{'SH' if market == 'sh' else 'SZ'}"
    url = (f"https://datacenter.eastmoney.com/securities/api/data/v1/get"
           f"?reportName=RPT_F10_FINANCE_MAINFINADATA"
           f"&columns=SECUCODE,REPORT_DATE,TOTALOPERATEREVE,PARENTNETPROFIT,DJD_TOI_YOY,DJD_DPNP_YOY,EPSJB,ROEJQ,XSMLL,XSJLL"
           f"&filter=(SECUCODE=%22{secucode}%22)&pageNumber=1&pageSize=2&sortTypes=-1&sortColumns=REPORT_DATE")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.loads(resp.read())
        if d.get("result") and d["result"].get("data"):
            item = d["result"]["data"][0]
            return {
                "revenue_q": round((item.get("TOTALOPERATEREVE") or 0) / 1e8, 2),
                "profit_q": round((item.get("PARENTNETPROFIT") or 0) / 1e8, 2),
                "rev_yoy": round(item.get("DJD_TOI_YOY") or 0, 2),
                "prof_yoy": round(item.get("DJD_DPNP_YOY") or 0, 2),
                "eps": round(item.get("EPSJB") or 0, 4),
                "roe": round(item.get("ROEJQ") or 0, 2),
                "margin_gross": round(item.get("XSMLL") or 0, 2),
                "margin_net": round(item.get("XSJLL") or 0, 2),
                "report_date": item.get("REPORT_DATE", "")[:10],
            }
    except Exception:
        return None
    return None


def fetch_kline(company, days=40):
    """Fetch K-line from Sina API."""
    m = company.get("market", "sz")
    code = company.get("code", "")
    symbol = f"hk{code}" if m == "hk" else f"{m}{code}"
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=5&datalen={days}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("gbk")
        if not data or data == "null":
            return []
        items = json.loads(data.replace("'", '"'))
        return [{"date": i.get("day", ""), "open": float(i.get("open", 0)), "close": float(i.get("close", 0)),
                  "high": float(i.get("high", 0)), "low": float(i.get("low", 0)),
                  "volume": int(float(i.get("volume", 0)))} for i in items]
    except Exception:
        return []


def fetch_news(code, name, max_items=6):
    """Fetch recent stock news via AKShare."""
    if not _HAS_AKSHARE:
        return []
    try:
        df = ak.stock_lrb_em(symbol=code)  # wrong, let me fix
        return []
    except Exception:
        return []

def fetch_stock_news(code, name, max_items=6):
    """Fetch recent stock news via AKShare."""
    if not _HAS_AKSHARE:
        return []
    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return []
        good_kw = ["增长", "突破", "利好", "新高", "盈利", "订单", "扩产", "中标",
                    "投产", "量产", "认证", "合作", "业绩", "增持", "回购", "加速", "大涨"]
        bad_kw = ["下滑", "亏损", "减持", "诉讼", "处罚", "风险", "利空", "下调",
                   "跌停", "大跌", "减少", "退出", "暂停", "违规", "调查"]
        news = []
        for _, row in df.iterrows():
            title = str(row.get("新闻标题", ""))[:80]
            content = str(row.get("新闻内容", ""))[:200]
            combined = (title + content).lower()
            is_good = any(kw in combined for kw in good_kw)
            is_bad = any(kw in combined for kw in bad_kw)
            sentiment = "good" if (is_good and not is_bad) else ("bad" if is_bad else "neutral")
            news.append({
                "title": title, "source": str(row.get("文章来源", "")),
                "date": str(row.get("发布时间", ""))[:10], "url": str(row.get("新闻链接", "")),
                "sentiment": sentiment,
            })
        seen = set()
        deduped = []
        for item in news:
            if item["title"] not in seen:
                seen.add(item["title"])
                deduped.append(item)
        return deduped[:max_items]
    except Exception as e:
        print(f"    [NEWS] {code} ({name}): {e}")
        return []


# ============================================================
# PERFORMANCE SCORING
# ============================================================

def compute_score(fin):
    """Compute composite performance score (0-100) from financial data."""
    if not fin:
        return 0
    score = 50  # baseline
    # Revenue growth (weight 25)
    rev = fin.get("rev_yoy", 0)
    if rev > 50: score += 25
    elif rev > 30: score += 20
    elif rev > 15: score += 15
    elif rev > 5: score += 8
    elif rev > 0: score += 3
    elif rev > -10: score -= 5
    else: score -= 15
    # Profit growth (weight 30)
    prof = fin.get("prof_yoy", 0)
    if prof > 100: score += 30
    elif prof > 50: score += 25
    elif prof > 30: score += 20
    elif prof > 15: score += 14
    elif prof > 0: score += 6
    elif prof > -10: score -= 8
    else: score -= 20
    # ROE (weight 20)
    roe = fin.get("roe", 0)
    if roe > 20: score += 20
    elif roe > 15: score += 16
    elif roe > 10: score += 12
    elif roe > 5: score += 6
    elif roe > 0: score += 2
    else: score -= 10
    # Gross margin (weight 15)
    gm = fin.get("margin_gross", 0)
    if gm > 50: score += 15
    elif gm > 40: score += 12
    elif gm > 30: score += 9
    elif gm > 20: score += 6
    elif gm > 10: score += 3
    else: score += 0
    # Net margin (weight 10)
    nm = fin.get("margin_net", 0)
    if nm > 25: score += 10
    elif nm > 15: score += 7
    elif nm > 10: score += 5
    elif nm > 5: score += 3
    elif nm > 0: score += 1
    else: score -= 5
    return max(0, min(100, score))


def performance_label(score):
    if score >= 80: return "优秀", "tag-green"
    if score >= 65: return "良好", "tag-blue"
    if score >= 50: return "中等", "tag-orange"
    return "偏弱", "tag-red"


# ============================================================
# HTML GENERATION
# ============================================================

def generate_report(output_path):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_date = datetime.now().strftime("%Y-%m-%d")
    q_label = "2026Q1（最新完整季度）"

    # Collect all companies
    all_companies = []
    for chain in INDUSTRY_CHAINS:
        for co in chain["companies"]:
            co["chain"] = chain["name"]
            all_companies.append(co)

    print("=" * 60)
    print(f"📊 Q2 2026 Performance Report Generator")
    print(f"   报告日期: {report_date}")
    print(f"   覆盖产业链: {len(INDUSTRY_CHAINS)} 条")
    print(f"   公司数量: {len(all_companies)} 家")
    print("=" * 60)

    # Fetch real-time data
    print("\n[1/3] Fetching real-time data...")
    realtime = fetch_tencent_real_time(all_companies)

    # Fetch financials
    print("[2/3] Fetching financial data...")
    fin_data = {}
    for co in all_companies:
        code = co["code"]
        fin = fetch_financial(code, co.get("market", "sz"))
        fin_data[code] = fin
        if fin:
            print(f"    {co['name']}({code}): 营收{fin['revenue_q']}亿 净利{fin['profit_q']}亿 "
                  f"营收同比{fin['rev_yoy']:+.1f}% 净利同比{fin['prof_yoy']:+.1f}% ROE={fin['roe']}%")

    # Compute scores
    print("[3/3] Computing performance scores...")
    for co in all_companies:
        co["fin"] = fin_data.get(co["code"])
        co["score"] = compute_score(co["fin"])
        sd = realtime.get(co["code"], {})
        co["price"] = sd.get("price", 0)
        co["change_pct"] = sd.get("change_pct", 0)
        co["mcap"] = sd.get("mcap", 0)
        co["pe"] = sd.get("pe", 0)

    # Fetch news for top companies
    print("\n    Fetching news for top companies...")
    news_cache = {}
    for co in all_companies:
        if co["score"] >= 50:  # only for decent performers
            news_cache[co["code"]] = fetch_stock_news(co["code"], co["name"])
            time.sleep(0.3)

    # Fetch K-line for top companies
    print("    Fetching K-line data...")
    kline_cache = {}
    for co in all_companies:
        if co["score"] >= 50:
            kline_cache[co["code"]] = fetch_kline(co, 40)

    # Sort chains by average score
    chain_avg = {}
    for chain in INDUSTRY_CHAINS:
        scores = [co["score"] for co in chain["companies"]]
        chain_avg[chain["name"]] = round(sum(scores) / len(scores), 1) if scores else 0
    sorted_chains = sorted(INDUSTRY_CHAINS, key=lambda ch: chain_avg[ch["name"]], reverse=True)

    # Overall ranking (top 30)
    all_sorted = sorted(all_companies, key=lambda x: x["score"], reverse=True)
    top_overall = all_sorted[:30]

    print(f"\n{'='*60}")
    print(f"  产业链平均得分排名:")
    for ch in sorted_chains:
        avg = chain_avg[ch["name"]]
        print(f"    {ch['icon']} {ch['name']}: {avg:.1f} 分")
    print(f"{'='*60}")

    # ---- Build HTML ----
    
    # Overall ranking table
    rank_rows = ""
    for i, co in enumerate(top_overall):
        code = co["code"]
        score = co["score"]
        label, lbl_cls = performance_label(score)
        chg_cls = "up" if co["change_pct"] > 0 else "down"
        chg_sign = "+" if co["change_pct"] > 0 else ""
        mcap = co["mcap"]
        mcap_s = f"{mcap:.0f}亿" if mcap > 0 else "N/A"
        fin = co.get("fin")
        rev_yoy = f"{fin['rev_yoy']:+.1f}%" if fin else "N/A"
        prof_yoy = f"{fin['prof_yoy']:+.1f}%" if fin else "N/A"
        rank_rows += f"""
        <tr>
          <td style="font-weight:700;color:#2d3748">{i+1}</td>
          <td><a href="javascript:void(0)" onclick="switchCompany('{code}')" class="co-link-tag">{co['name']}</a></td>
          <td style="font-size:10px;color:#718096">{co['chain']}</td>
          <td style="text-align:right">{co['price']:.2f}</td>
          <td style="text-align:right;color:{'#e53e3e' if co['change_pct']>0 else '#38a169'}">{chg_sign}{co['change_pct']:.2f}%</td>
          <td style="text-align:right">{mcap_s}</td>
          <td style="text-align:right;font-weight:600">{score}</td>
          <td><span class="tag {lbl_cls}">{label}</span></td>
          <td style="text-align:right">{rev_yoy}</td>
          <td style="text-align:right">{prof_yoy}</td>
        </tr>"""

    # Chain sections
    chain_sections = ""
    for ch in sorted_chains:
        sorted_co = sorted(ch["companies"], key=lambda x: x["score"], reverse=True)
        co_rows = ""
        for co in sorted_co:
            code = co["code"]
            score = co["score"]
            label, lbl_cls = performance_label(score)
            fin = co.get("fin")
            rev_yoy = f"{fin['rev_yoy']:+.1f}%" if fin else "N/A"
            prof_yoy = f"{fin['prof_yoy']:+.1f}%" if fin else "N/A"
            roe = f"{fin['roe']}%" if fin else "N/A"
            rev_q = f"{fin['revenue_q']}亿" if fin else "N/A"
            profit_q = f"{fin['profit_q']}亿" if fin else "N/A"
            co_rows += f"""
            <tr>
              <td><a href="javascript:void(0)" onclick="switchCompany('{code}')" class="co-link-tag">{co['name']}</a></td>
              <td style="font-size:10px;color:#718096">{co.get('biz', '')}</td>
              <td style="text-align:right;font-weight:600">{score}</td>
              <td><span class="tag {lbl_cls}">{label}</span></td>
              <td style="text-align:right">{rev_q}</td>
              <td style="text-align:right">{profit_q}</td>
              <td style="text-align:right">{rev_yoy}</td>
              <td style="text-align:right">{prof_yoy}</td>
              <td style="text-align:right">{roe}</td>
            </tr>"""
        avg = chain_avg[ch["name"]]
        chain_sections += f"""
        <div class="sec">
          <div class="sec-hd" style="display:flex;justify-content:space-between;align-items:center">
            <h2>{ch['icon']} {ch['name']} <span style="font-size:11px;font-weight:400;color:#a0aec0">平均 {avg} 分</span></h2>
            <span style="font-size:11px;color:#a0aec0">{len(ch['companies'])} 家公司</span>
          </div>
          <div class="sec-bd">
            <p style="color:#718096;font-size:11px;margin-bottom:8px">{ch['description']}</p>
            <table class="ctable">
              <thead><tr><th>公司</th><th>业务</th><th style="text-align:right">评分</th><th>评级</th><th style="text-align:right">营收(亿)</th><th style="text-align:right">净利(亿)</th><th style="text-align:right">营收同比</th><th style="text-align:right">净利同比</th><th style="text-align:right">ROE</th></tr></thead>
              <tbody>{co_rows}</tbody>
            </table>
          </div>
        </div>"""

    # Company cards
    cards_html = ""
    for co in all_sorted:
        if co["score"] < 40:
            continue  # skip poor performers for cards
        code = co["code"]
        score = co["score"]
        label, lbl_cls = performance_label(score)
        fin = co.get("fin")
        sd = realtime.get(code, {})
        price = sd.get("price", 0)
        chg = sd.get("change_pct", 0)
        chg_cls = "up" if chg > 0 else "down"
        chg_sign = "+" if chg > 0 else ""
        mcap = sd.get("mcap", 0)
        mcap_s = f"{mcap:.0f}亿" if mcap > 0 else "N/A"
        pe = sd.get("pe", 0)
        kline = kline_cache.get(code, [])
        kline_json = json.dumps(kline, ensure_ascii=False) if kline else "[]"
        news = news_cache.get(code, [])

        stats_items = [
            ("最新价", f"<span style='font-size:20px;font-weight:700'>{price:.2f}</span>"),
            ("涨跌幅", f"<span class='{chg_cls}'>{chg_sign}{chg:.2f}%</span>"),
            ("市值", mcap_s),
            ("PE", f"{pe:.1f}" if pe else "N/A"),
        ]
        if fin:
            stats_items += [
                (f"最新财报({fin['report_date'][:7]})", ""),
                ("营收", f"{fin['revenue_q']}亿"),
                ("净利润", f"{fin['profit_q']}亿"),
                ("营收同比", f"<span class='{'up' if fin['rev_yoy']>0 else 'down'}'>{fin['rev_yoy']:+.1f}%</span>"),
                ("净利同比", f"<span class='{'up' if fin['prof_yoy']>0 else 'down'}'>{fin['prof_yoy']:+.1f}%</span>"),
                ("毛利率", f"{fin['margin_gross']:.1f}%"),
                ("净利率", f"{fin['margin_net']:.1f}%"),
                ("ROE", f"{fin['roe']:.1f}%"),
                ("EPS", f"{fin['eps']}"),
            ]
        stat_grid = "".join(
            f'<div class="si"><div class="sl">{k}</div><div class="sv">{v}</div></div>'
            for k, v in stats_items
        )

        news_html = ""
        if news:
            news_rows = []
            for item in news:
                sent = item["sentiment"]
                icon = "✅" if sent == "good" else ("⚠️" if sent == "bad" else "📄")
                cls = "news-good" if sent == "good" else ("news-bad" if sent == "bad" else "")
                url = item.get("url", "")
                t = item["title"]
                t_html = f'<a href="{url}" target="_blank" rel="noopener">{t}</a>' if url else t
                news_rows.append(
                    f'<div class="news-item {cls}"><span class="news-icon">{icon}</span> '
                    f'{t_html} <span class="news-meta">{item["date"]}</span></div>'
                )
            news_html = '<div class="co-news"><div class="co-news-hd">📰 近期消息</div>' + "".join(news_rows) + '</div>'

        mkt = co.get("market", "sz")
        ths_url = f"https://stockpage.10jqka.com.cn/{'HK' if mkt=='hk' else ''}{code}/"
        score_bar_pct = score
        cards_html += f"""<div class="co-card" id="co_{code}">
  <div class="co-hd">
    <div><span class="co-n">{co['name']}</span> <span class="co-c">{code}</span> <span class="co-t">{co['chain']}</span></div>
    <div style="display:flex;align-items:center;gap:6px">
      <a href="{ths_url}" target="_blank" rel="noopener" class="ext-link" title="查看同花顺页面">同花顺 ›</a>
      <div class="co-tag">{co.get('biz', '')[:25]}</div>
      <span class="tag {lbl_cls}">{score}分</span>
    </div>
  </div>
  <div class="co-bd">
    <div class="co-ic">
      <div class="il"><div class="il-l">📋 入选理由 · {co['chain']}</div><div class="il-t">{co.get('reason', '')}</div></div>
    </div>
    <div class="sg" style="grid-template-columns:repeat(auto-fit,minmax(100px,1fr))">{stat_grid}</div>
    <div class="score-bar"><div class="score-fill" style="width:{score_bar_pct}%"></div></div>
    <div class="co-charts">
      <div class="chart-box" id="k_{code}" style="height:190px"></div>
    </div>
    {news_html}
  </div>
</div>
<script>
(function(){{
var kd=document.getElementById('k_{code}');
if(kd){{
var ch=echarts.init(kd);
var k={kline_json};
if(k.length>0){{
var dt=k.map(x=>x.date.slice(5));
var pr=k.map(x=>[x.open,x.close,x.low,x.high]);
var vl=k.map(x=>x.volume);
ch.setOption({{
tooltip:{{trigger:'axis',axisPointer:{{type:'cross'}},formatter:function(p){{var d=k[p[0].dataIndex];return '<b>'+d.date+'</b><br/>开:'+d.open.toFixed(2)+' 收:'+d.close.toFixed(2)+'<br/>高:'+d.high.toFixed(2)+' 低:'+d.low.toFixed(2)+'<br/>量:'+(d.volume/10000).toFixed(0)+'万手';}}}},
grid:[{{left:'6%',right:'3%',top:'6%',height:'56%'}},{{left:'6%',right:'3%',top:'71%',height:'21%'}}],
xAxis:[{{type:'category',data:dt,gridIndex:0,axisLabel:{{fontSize:9,rotate:30}}}},{{type:'category',data:dt,gridIndex:1,axisLabel:{{show:false}}}}],
yAxis:[{{type:'value',scale:true,gridIndex:0,splitLine:{{lineStyle:{{type:'dashed',color:'#e2e8f0'}}}}}},{{type:'value',scale:true,gridIndex:1,splitLine:{{show:false}},axisLabel:{{show:false}}}}],
series:[
{{name:'K',type:'candlestick',xAxisIndex:0,yAxisIndex:0,data:pr,itemStyle:{{color:'#e53e3e',color0:'#38a169',borderColor:'#e53e3e',borderColor0:'#38a169'}}}},
{{name:'V',type:'bar',xAxisIndex:1,yAxisIndex:1,data:vl.map(function(v,i){{return {{value:v,itemStyle:{{color:pr[i][0]<=pr[i][1]?'#e53e3e':'#38a169'}}}};}})}}
],
dataZoom:[{{type:'inside',xAxisIndex:[0,1],start:Math.max(0,100-40),end:100}}]
}});
}} else {{
kd.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#a0aec0;font-size:12px;">⏳ K线数据暂不可用</div>';
}}
window.addEventListener('resize',function(){{ch.resize()}});
}}
}})();
</script>"""

    # Chain summary cards for top of report
    chain_summary = ""
    for ch in sorted_chains:
        avg = chain_avg[ch["name"]]
        top_co = sorted(ch["companies"], key=lambda x: x["score"], reverse=True)[:3]
        top_names = " · ".join(
            f'<a href="javascript:void(0)" onclick="switchCompany(\'{c["code"]}\')" class="co-link-tag">{c["name"]}</a>'
            for c in top_co
        )
        chain_summary += f"""
        <div class="si" style="text-align:left;padding:12px">
          <div class="sl" style="font-size:12px;margin-bottom:4px">{ch['icon']} {ch['name']}</div>
          <div class="sv" style="font-size:22px">{avg:.0f}</div>
          <div style="font-size:10px;color:#718096;margin-top:2px">平均分 · {top_names}</div>
        </div>"""

    # Build the full HTML
    all_codes_json = json.dumps([c["code"] for c in all_companies if c["score"] >= 40], ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📊 Q2 2026 业绩分析报告</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#f0f2f5;color:#333;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;padding-top:56px}}

.top-nav{{position:fixed;top:0;left:0;right:0;z-index:1000;background:linear-gradient(135deg,#0a1628,#1a2a4a);display:flex;align-items:center;overflow-x:auto;white-space:nowrap;padding:0 8px;height:56px;gap:2px}}
.top-nav .ntt{{color:#e2e8f0;font-weight:700;font-size:13px;padding:0 10px;flex-shrink:0}}
.top-nav .tab{{color:#a0aec0;text-decoration:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;transition:.2s;flex-shrink:0}}
.top-nav .tab:hover,.top-nav .tab.active{{background:rgba(255,255,255,0.12);color:#fff}}

.header{{background:linear-gradient(135deg,#0a1628,#1a2a4a,#0a1628);color:#fff;padding:48px 24px 32px;text-align:center}}
.header h1{{font-size:26px;margin-bottom:6px}}
.header .sub{{color:#a0aec0;font-size:13px;line-height:1.6}}
.header .dt{{color:#4a5568;font-size:11px;margin-top:4px}}
.cont{{max-width:1400px;margin:0 auto;padding:12px}}
.tab-content{{display:none}}
.tab-content.active{{display:block}}

.sec{{background:#fff;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.04);overflow:hidden}}
.sec-hd{{background:linear-gradient(135deg,#1a365d,#2a4a7f);padding:14px 20px;color:#fff;display:flex;justify-content:space-between;align-items:center}}
.sec-hd h2{{font-size:15px}}
.sec-bd{{padding:14px 20px}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:8px 0}}
.si{{background:#f7fafc;border-radius:8px;padding:10px;text-align:center}}
.si .sl{{font-size:10px;color:#a0aec0;margin-bottom:2px}}
.si .sv{{font-size:15px;font-weight:700;color:#2d3748}}

.ctable{{width:100%;border-collapse:collapse;margin:8px 0;font-size:11px}}
.ctable th{{background:#ebf4ff;padding:6px 8px;text-align:left;font-weight:600;color:#2b6cb0;border-bottom:2px solid #bee3f8;white-space:nowrap}}
.ctable td{{padding:6px 8px;border-bottom:1px solid #e2e8f0}}
.ctable tr:hover{{background:#f7fafc}}

.tag{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600;margin:1px}}
.tag-green{{background:#c6f6d5;color:#22543d}}
.tag-blue{{background:#bee3f8;color:#2b6cb0}}
.tag-orange{{background:#feebc8;color:#7b341e}}
.tag-red{{background:#fed7d7;color:#742a2a}}

.chart-box{{width:100%;height:280px;margin:10px 0;border-radius:6px;background:#fafafa}}
.co-card{{background:#fff;border-radius:12px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.04);overflow:hidden}}
.co-hd{{background:linear-gradient(135deg,#f7fafc,#edf2f7);padding:12px 16px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center}}
.co-n{{font-size:16px;font-weight:700;color:#1a202c}}
.co-c{{font-size:11px;color:#718096;background:#edf2f7;padding:1px 6px;border-radius:10px}}
.co-t{{font-size:10px;background:#ebf4ff;color:#2b6cb0;padding:1px 6px;border-radius:10px;font-weight:600}}
.co-tag{{font-size:10px;background:#e2e8f0;padding:1px 6px;border-radius:8px;color:#4a5568}}
.co-bd{{padding:14px 16px}}
.co-ic{{margin-bottom:10px}}
.il .il-l{{font-size:10px;color:#a0aec0;margin-bottom:2px}}
.il .il-t{{font-size:12px;color:#4a5568;line-height:1.5}}
.co-charts{{margin-top:10px}}
.co-news{{background:#fafcff;border-radius:8px;padding:10px 12px;margin-top:10px;border:1px solid #e2e8f0}}
.co-news-hd{{font-size:12px;font-weight:700;color:#2d3748;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e2e8f0}}
.news-item{{font-size:11px;padding:4px 0;display:flex;align-items:flex-start;gap:4px;line-height:1.4;border-bottom:1px solid #f0f2f5}}
.news-item:last-child{{border-bottom:none}}
.news-item .news-icon{{flex-shrink:0;width:18px;text-align:center}}
.news-item a{{color:#2b6cb0;text-decoration:none;flex:1}}
.news-item a:hover{{text-decoration:underline;color:#e53e3e}}
.news-item .news-meta{{flex-shrink:0;font-size:9px;color:#a0aec0;white-space:nowrap}}
.news-good{{border-left:3px solid #38a169;padding-left:4px}}
.news-bad{{border-left:3px solid #e53e3e;padding-left:4px}}

.score-bar{{height:4px;background:#edf2f7;border-radius:2px;margin:8px 0;overflow:hidden}}
.score-fill{{height:100%;background:linear-gradient(90deg,#38a169,#ecc94b,#e53e3e);border-radius:2px;transition:width 1s}}

.ext-link{{font-size:10px;color:#3182ce;text-decoration:none;background:#ebf8ff;padding:1px 8px;border-radius:8px;font-weight:600;transition:.15s}}
.ext-link:hover{{background:#3182ce;color:#fff;text-decoration:none}}
.co-link-tag{{color:#2b6cb0;text-decoration:none;cursor:pointer}}
.co-link-tag:hover{{color:#e53e3e;text-decoration:underline}}
.up{{color:#e53e3e}} .down{{color:#38a169}}

.ref-section{{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:20px;font-size:12px;color:#4a5568}}
.ref-section h3{{font-size:14px;margin-bottom:10px;color:#2d3748}}
.ft{{text-align:center;padding:20px;color:#a0aec0;font-size:10px;line-height:1.6}}
.tab-target{{scroll-margin-top:64px}}
@media(max-width:768px){{.co-charts{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<nav class="top-nav" id="topNav">
  <span class="ntt">📊 Q2业绩</span>
  <a class="tab active" href="javascript:void(0)" onclick="switchTab('overview')">📋 总览</a>
  <span class="tab-sep">|</span>
  <a class="tab" href="javascript:void(0)" onclick="switchTab('chains')">🔗 产业链</a>
  <span class="tab-sep">|</span>
  <a class="tab" href="javascript:void(0)" onclick="switchTab('companies')">🏢 公司分析</a>
</nav>

<div class="header">
  <h1>📊 Q2 2026 业绩分析报告</h1>
  <div class="sub">数据基于 {q_label} · {len(all_companies)} 家公司 · {len(INDUSTRY_CHAINS)} 条产业链</div>
  <div class="dt">📅 生成: {now} | 评分模型: 营收增速+净利增速+ROE+毛利率+净利率 | 数据: 腾讯API+东方财富</div>
</div>

<div class="cont">

<!-- === TAB: OVERVIEW === -->
<div class="tab-content active" id="tab-overview">
  <div class="sec">
    <div class="sec-hd"><h2>📊 产业链综合评分</h2></div>
    <div class="sec-bd">
      <p style="color:#4a5568;font-size:12px;margin-bottom:8px">
        评分基于 <b>营收同比增速</b>(25%) + <b>归母净利同比增速</b>(30%) + <b>ROE</b>(20%) + <b>毛利率</b>(15%) + <b>净利率</b>(10%)，
        满分100分。数据来自最新完整季度财报 ({q_label})。
      </p>
      <div class="sg" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr))">{chain_summary}</div>
    </div>
  </div>

  <div class="sec">
    <div class="sec-hd"><h2>🏆 综合业绩排名 Top {len(top_overall)}</h2></div>
    <div class="sec-bd">
      <table class="ctable">
        <thead><tr><th>#</th><th>公司</th><th>产业链</th><th style="text-align:right">股价</th><th style="text-align:right">涨跌幅</th><th style="text-align:right">市值</th><th style="text-align:right">评分</th><th>评级</th><th style="text-align:right">营收同比</th><th style="text-align:right">净利同比</th></tr></thead>
        <tbody>{rank_rows}</tbody>
      </table>
    </div>
  </div>
</div><!-- /tab-overview -->

<!-- === TAB: CHAINS === -->
<div class="tab-content" id="tab-chains">
  {chain_sections}
</div><!-- /tab-chains -->

<!-- === TAB: COMPANIES === -->
<div class="tab-content" id="tab-companies">
  <h2 style="font-size:18px;color:#2d3748;margin-bottom:12px;padding:8px 0">🏢 重点公司深度分析 (评分≥40)</h2>
  {cards_html}
</div><!-- /tab-companies -->

<div class="ft">
  ⚠️ 本报告基于公开数据自动生成, 仅供参考, 不构成投资建议。<br>
  数据: 腾讯行情API · 东方财富 ｜ 评分模型仅供参考 ｜ 生成: {now}
</div>

</div><!-- /cont -->

{{inline_js_placeholder}}
</body>
</html>"""

    # Build & inject JS
    inline_js = f"""<script>
var _coCodes = {all_codes_json};

function switchTab(tab) {{
  if(_coCodes.indexOf(tab) !== -1) {{
    switchCompany(tab);
    return;
  }}
  document.querySelectorAll('.tab-content').forEach(function(el){{el.classList.remove('active')}});
  document.querySelectorAll('.tab').forEach(function(el){{el.classList.remove('active')}});
  var tc = document.getElementById('tab-' + tab);
  if(tc) tc.classList.add('active');
  var ta = document.querySelector('.tab[onclick*="' + tab + '"]');
  if(ta) ta.classList.add('active');
  window.scrollTo({{top:0,behavior:'smooth'}});
  setTimeout(function(){{
    if(tc) {{
      tc.querySelectorAll('.chart-box').forEach(function(cb){{
        if(cb.id){{var ch=echarts.getInstanceByDom(cb);if(ch) ch.resize();}}
      }});
    }}
  }}, 150);
}}

function switchCompany(code) {{
  switchTab('companies');
  setTimeout(function() {{
    var el = document.getElementById('co_' + code);
    if(el) el.scrollIntoView({{behavior:'smooth',block:'start'}});
  }}, 200);
}}

document.querySelectorAll('.tab').forEach(function(t){{
  t.addEventListener('click', function() {{this.scrollIntoView({{behavior:'smooth',inline:'center',block:'nearest'}});}});
}});
</script>"""

    html = html.replace('{{inline_js_placeholder}}', inline_js)

    # Write
    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Q2 performance report generated: {output_path}")
    import os.path
    size_kb = os.path.getsize(output_path) / 1024
    print(f"   Size: {size_kb:.0f} KB")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Q2 2026 Quarterly Performance Report")
    parser.add_argument("--output", "-o", default="q2_performance_report.html")
    args = parser.parse_args()
    generate_report(args.output)
