#!/usr/bin/env python3
"""
Cross-Market Impact Analysis Report Generator.

Analyzes how A-share, Korean, and US market events affect A-share sectors/industry chains,
and generates a structured HTML report with company deep-dive cards.

Usage:
    # From events JSON file
    python market_impact_report.py --events events.json --output report.html

    # Interactive (AI-assisted)
    python market_impact_report.py --output report.html

Data Sources:
    - Real-time prices: Tencent Finance API
    - K-line: Sina Finance API
    - Financials: East Money Data Center
    - News: AKShare (stock_news_em)
"""

import argparse
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
# STOCK DATA FETCHING (shared patterns with chain-analysis)
# ============================================================

def fetch_tencent_real_time(companies):
    """Fetch real-time stock data from Tencent API for a list of companies."""
    if not companies:
        return {}
    market_codes = []
    for c in companies:
        market = c.get("market", "sz")
        code = c.get("code", "")
        if market == "hk":
            market_codes.append(f"hk{code}")
        else:
            market_codes.append(f"{market}{code}")
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
                results[code] = {
                    "price": price,
                    "change_pct": round(chg, 2),
                    "mcap": mcap,
                    "pe": pe,
                    "name": parts[1] if parts[1] else "",
                }
            except (ValueError, IndexError):
                continue
        return results
    except Exception as e:
        print(f"  [ERROR] Tencent API: {e}")
        return {}


def fetch_kline(company, days=40):
    """Fetch K-line data from Sina API."""
    market = company.get("market", "sz")
    code = company.get("code", "")
    if market == "hk":
        symbol = f"hk{code}"
    else:
        symbol = f"{market}{code}"
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


def fetch_financial(code, market):
    """Fetch latest quarterly financial data from East Money API (A-shares only)."""
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


def fetch_news(code, name, max_items=6):
    """Fetch recent news for a stock using AKShare."""
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
            if is_good and not is_bad:
                sentiment = "good"
            elif is_bad and not is_good:
                sentiment = "bad"
            else:
                sentiment = "neutral"
            news.append({
                "title": title,
                "source": str(row.get("文章来源", "")),
                "date": str(row.get("发布时间", ""))[:10],
                "url": str(row.get("新闻链接", "")),
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
        print(f"    [NEWS ERROR] {code} ({name}): {e}")
        return []


def collect_all_companies(sectors):
    """Flatten all companies from sectors into a deduplicated list."""
    seen = set()
    companies = []
    for sec in sectors:
        for co in sec.get("companies", []):
            key = co.get("code", "")
            if key and key not in seen:
                seen.add(key)
                companies.append(co)
    return companies


# ============================================================
# HTML GENERATION
# ============================================================

def generate_report(data, output_path):
    """Generate the full HTML report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = data.get("report_title", "跨市场影响分析报告")
    report_date = data.get("report_date", now[:10])
    sectors = data.get("sectors", [])
    overview = data.get("market_overview", {})

    # Collect all unique companies and fetch their data
    all_companies = collect_all_companies(sectors)
    print(f"[Data] Fetching real-time data for {len(all_companies)} companies...")
    realtime = fetch_tencent_real_time(all_companies)

    print("[Data] Fetching financials and news...")
    company_data = {}
    for co in all_companies:
        code = co["code"]
        name = co["name"]
        sd = realtime.get(code, {})
        price = sd.get("price", 0)
        chg = sd.get("change_pct", 0)
        mcap = sd.get("mcap", 0)
        pe = sd.get("pe", 0)

        fin = fetch_financial(code, co.get("market", "sz"))
        kline = fetch_kline(co, 40)
        news = fetch_news(code, name)

        mcap_s = f"{mcap:.0f}亿" if mcap > 0 else "N/A"
        country = co.get("market", "sz")
        if country == "us":
            mcap_s = f"${mcap:.0f}亿" if mcap > 0 else "N/A"

        company_data[code] = {
            "name": name,
            "price": price,
            "change_pct": chg,
            "mcap_s": mcap_s,
            "pe": pe,
            "fin": fin,
            "kline": kline,
            "news": news,
            "reason": co.get("reason", ""),
        }
        print(f"    {name}({code}): 市值{mcap_s} PE={pe}" +
              (f" Q1营收{fin['revenue_q']}亿 净利{fin['profit_q']}亿" if fin else ""))

    # ---- Build HTML ----
    html_parts = []

    # Sector impact cards HTML
    sector_cards_html = ""
    for sec in sectors:
        imp = sec.get("impact", "中性")
        if imp == "利好":
            badge_cls, badge_bg = "sector-good", "bg-green"
        elif imp == "利空":
            badge_cls, badge_bg = "sector-bad", "bg-red"
        else:
            badge_cls, badge_bg = "sector-neutral", "bg-gray"

        # Companies in this sector
        co_links = []
        for co in sec.get("companies", []):
            code = co["code"]
            cd = company_data.get(code, {})
            price = cd.get("price", 0)
            chg = cd.get("change_pct", 0)
            chg_cls = "up" if chg > 0 else "down"
            chg_sign = "+" if chg > 0 else ""
            co_links.append(
                f'<a href="javascript:void(0)" onclick="switchCompany(\'{code}\')" '
                f'class="co-link-tag">{co["name"]}</a>'
                f' <span style="font-size:10px;color:#718096">({price:.2f} '
                f'<span class="{chg_cls}">{chg_sign}{chg:.2f}%</span>)</span>'
                f'<br><span style="font-size:10px;color:#a0aec0">{co.get("reason", "")}</span>'
            )

        events_html = "<br>".join(
            f'<span class="tag tag-orange">{e}</span>' for e in sec.get("events", [])
        )
        mechanism_html = sec.get("mechanism", "")

        sector_cards_html += f"""
        <div class="sec">
          <div class="sec-hd" style="display:flex;justify-content:space-between;align-items:center">
            <h2><span class="{badge_bg}" style="display:inline-block;padding:2px 12px;border-radius:12px;font-size:12px;margin-right:8px">{imp}</span> {sec["name"]}</h2>
            <span style="font-size:11px;color:#a0aec0">置信度: {sec.get("confidence", "中")}</span>
          </div>
          <div class="sec-bd">
            <p style="color:#4a5568;font-size:12px;line-height:1.6;margin-bottom:8px">{sec.get("explanation", "")}</p>
            <div class="sg" style="grid-template-columns:1fr 1fr;gap:10px">
              <div class="si"><div class="sl">触发事件</div><div class="sv" style="font-weight:400;font-size:11px">{events_html}</div></div>
              <div class="si"><div class="sl">传导机制</div><div class="sv" style="font-weight:400;font-size:11px">{mechanism_html}</div></div>
            </div>
            <div style="margin-top:8px;padding-top:8px;border-top:1px solid #e2e8f0">
              <div style="font-size:11px;color:#a0aec0;margin-bottom:4px">📌 受益/受影响标的</div>
              <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px">
                {''.join(f'<div style="background:#f7fafc;border-radius:6px;padding:6px 10px;font-size:11px">{l}</div>' for l in co_links)}
              </div>
            </div>
          </div>
        </div>
        """

    # Company cards HTML
    cards_html = ""
    for co in all_companies:
        code = co["code"]
        cd = company_data.get(code, {})
        price = cd.get("price", 0)
        chg = cd.get("change_pct", 0)
        chg_cls = "up" if chg > 0 else "down"
        chg_sign = "+" if chg > 0 else ""
        mcap_s = cd.get("mcap_s", "N/A")
        pe = cd.get("pe", 0)
        fin = cd.get("fin")
        kline = cd.get("kline", [])
        news = cd.get("news", [])
        reason = cd.get("reason", "")

        kline_json = json.dumps(kline, ensure_ascii=False) if kline else "[]"

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
                ("营收同比", f"<span class='{'up' if fin['rev_yoy']>0 else 'down'}'>{fin['rev_yoy']:+.2f}%</span>"),
                ("净利同比", f"<span class='{'up' if fin['prof_yoy']>0 else 'down'}'>{fin['prof_yoy']:+.2f}%</span>"),
                ("毛利率", f"{fin['margin_gross']:.1f}%"),
                ("净利率", f"{fin['margin_net']:.1f}%"),
                ("ROE", f"{fin['roe']:.1f}%"),
                ("EPS", f"{fin['eps']}"),
            ]
        stat_grid = "".join(
            f'<div class="si"><div class="sl">{k}</div><div class="sv">{v}</div></div>'
            for k, v in stats_items
        )

        # News section
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
                    f'{t_html} <span class="news-meta">{item["date"]} · {item["source"]}</span></div>'
                )
            news_html = '<div class="co-news"><div class="co-news-hd">📰 近期消息</div>' + "".join(news_rows) + '</div>'

        cards_html += f"""<div class="co-card" id="co_{code}">
  <div class="co-hd">
    <div><span class="co-n">{co["name"]}</span> <span class="co-c">{code}</span></div>
    <div style="display:flex;align-items:center;gap:6px">
      <a href="https://stockpage.10jqka.com.cn/{'HK' if co.get('market')=='hk' else ''}{code}/" target="_blank" rel="noopener" class="ext-link" title="查看同花顺页面">同花顺 ›</a>
      <div class="co-tag" style="font-size:10px">{reason[:30]}</div>
    </div>
  </div>
  <div class="co-bd">
    <div class="co-ic"><div class="il"><div class="il-l">📋 入选理由</div><div class="il-t">{reason}</div></div></div>
    <div class="sg" style="grid-template-columns:repeat(auto-fit,minmax(100px,1fr))">{stat_grid}</div>
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

    # Market overview HTML
    overview_html = ""
    for market_key, market_label in [("a_share", "A股 (大A)"), ("korea", "韩国股市"), ("us", "美股")]:
        text = overview.get(market_key, "")
        if text:
            overview_html += f"""
            <div class="sec">
              <div class="sec-hd"><h2>🌍 {market_label}</h2></div>
              <div class="sec-bd">
                <p style="color:#4a5568;font-size:12px;line-height:1.8">{text}</p>
              </div>
            </div>"""

    # ---- Full HTML template ----
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📊 {title}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#f0f2f5;color:#333;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;padding-top:56px}}

.top-nav{{position:fixed;top:0;left:0;right:0;z-index:1000;background:linear-gradient(135deg,#0a1628,#1a2a4a);display:flex;align-items:center;overflow-x:auto;white-space:nowrap;padding:0 8px;height:56px;gap:2px}}
.top-nav .ntt{{color:#e2e8f0;font-weight:700;font-size:13px;padding:0 10px;flex-shrink:0}}
.top-nav .tab{{color:#a0aec0;text-decoration:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;transition:.2s;flex-shrink:0}}
.top-nav .tab:hover,.top-nav .tab.active{{background:rgba(255,255,255,0.12);color:#fff}}
.top-nav .tab-sep{{color:#2d3748;font-size:10px;padding:0 2px}}

.header{{background:linear-gradient(135deg,#0a1628,#1a2a4a,#0a1628);color:#fff;padding:48px 24px 32px;text-align:center}}
.header h1{{font-size:24px;margin-bottom:6px}}
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
.si .sv{{font-size:14px;font-weight:700;color:#2d3748}}
.chart-box{{width:100%;height:280px;margin:10px 0;border-radius:6px;background:#fafafa}}

.co-card{{background:#fff;border-radius:12px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.04);overflow:hidden}}
.co-hd{{background:linear-gradient(135deg,#f7fafc,#edf2f7);padding:12px 16px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center}}
.co-n{{font-size:16px;font-weight:700;color:#1a202c}}
.co-c{{font-size:11px;color:#718096;background:#edf2f7;padding:1px 6px;border-radius:10px}}
.co-tag{{font-size:11px;background:#e2e8f0;padding:2px 8px;border-radius:10px;color:#4a5568}}
.co-bd{{padding:14px 16px}}
.co-ic{{margin-bottom:10px}}
.il .il-l{{font-size:10px;color:#a0aec0;margin-bottom:2px}}
.il .il-t{{font-size:13px;color:#4a5568;line-height:1.5}}
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

.co-link-tag{{color:#2b6cb0;text-decoration:none;cursor:pointer}}
.co-link-tag:hover{{color:#e53e3e;text-decoration:underline}}

.up{{color:#e53e3e}}
.down{{color:#38a169}}

/* external link (同花顺) */
.ext-link{{font-size:10px;color:#3182ce;text-decoration:none;background:#ebf8ff;padding:1px 8px;border-radius:8px;font-weight:600;transition:.15s}}
.ext-link:hover{{background:#3182ce;color:#fff;text-decoration:none}}

.bg-red{{background:#e53e3e;color:#fff}}
.bg-green{{background:#38a169;color:#fff}}
.bg-gray{{background:#718096;color:#fff}}

.tag{{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600;margin:1px}}
.tag-orange{{background:#feebc8;color:#7b341e}}
.tag-red{{background:#fed7d7;color:#742a2a}}
.tag-green{{background:#c6f6d5;color:#22543d}}
.tag-blue{{background:#bee3f8;color:#2b6cb0}}

.ref-section{{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:20px;font-size:12px;color:#4a5568}}
.ref-section h3{{font-size:14px;margin-bottom:10px;color:#2d3748}}
.ref-section ol{{padding-left:20px;line-height:1.8}}

.ft{{text-align:center;padding:20px;color:#a0aec0;font-size:10px;line-height:1.6}}
.tab-target{{scroll-margin-top:64px}}

@media(max-width:768px){{.co-charts{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<nav class="top-nav" id="topNav">
  <span class="ntt">📊 跨市场影响</span>
  <a class="tab active" href="javascript:void(0)" onclick="switchTab('overview')">📋 影响分析</a>
  <span class="tab-sep">|</span>
  <a class="tab" href="javascript:void(0)" onclick="switchTab('companies')">🏢 公司分析</a>
</nav>

<div class="header">
  <h1>📊 {title}</h1>
  <div class="sub">跨市场事件对A股板块/产业链影响分析<br>A股 · 韩国股市 · 美股 → A股利好/利空</div>
  <div class="dt">📅 报告日期: {report_date} | 生成: {now} | 行情数据: 腾讯API+东方财富</div>
</div>

<div class="cont">

<!-- === TAB: Overview (Market Impact) === -->
<div class="tab-content active" id="tab-overview">
  <div class="sec">
    <div class="sec-hd"><h2>🌐 市场概览</h2></div>
    <div class="sec-bd">
      <p style="color:#4a5568;font-size:12px;line-height:1.8">本报告分析 <b>A股</b>、<b>韩国股市</b>、<b>美股</b> 近期重大事件，评估其对A股各板块和产业链的影响，帮助识别投资机会与风险。</p>
    </div>
  </div>
  {overview_html}
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0">
  <h2 style="font-size:16px;color:#2d3748;margin-bottom:12px">📊 板块影响矩阵</h2>
  {sector_cards_html}
  <!-- {{ref_overview}} -->
</div><!-- /tab-overview -->

<!-- === TAB: Companies === -->
<div class="tab-content" id="tab-companies">
  <h2 style="font-size:18px;color:#2d3748;margin-bottom:12px;padding:8px 0">🏢 重点公司分析</h2>
  {cards_html}
  <!-- {{ref_companies}} -->
</div>

<div class="ft">
  ⚠️ 本报告基于公开数据自动生成, 仅供参考, 不构成投资建议。<br>
  行情数据: 腾讯行情API · 东方财富 ｜ 新闻: AKShare (东方财富) ｜ 生成: {now}
</div>

</div><!-- /cont -->

{{inline_js_placeholder}}
</body>
</html>"""

    # Build JS
    co_codes = json.dumps([c["code"] for c in all_companies], ensure_ascii=False)
    inline_js = f"""<script>
var _coCodes = {co_codes};

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
}}

function switchCompany(code) {{
  switchTab('companies');
  setTimeout(function() {{
    var el = document.getElementById('co_' + code);
    if(el) el.scrollIntoView({{behavior:'smooth',block:'start'}});
  }}, 200);
}}

function scrollToRef(n) {{
  var active = document.querySelector('.tab-content.active');
  var el = active ? active.querySelector('#ref-' + n) : null;
  if(el) {{
    el.scrollIntoView({{behavior:'smooth',block:'center'}});
  }}
}}

// Scroll active tab into nav view
document.querySelectorAll('.tab').forEach(function(t){{
  t.addEventListener('click', function() {{
    this.scrollIntoView({{behavior:'smooth',inline:'center',block:'nearest'}});
  }});
}});
</script>"""

    html = html.replace('{inline_js_placeholder}', inline_js)

    # Per-tab reference filtering
    def get_cited_refs(segment):
        nums = set()
        for m in re.finditer(r'scrollToRef\((\d+)\)', segment):
            nums.add(int(m.group(1)))
        return sorted(nums)

    for tab_id, placeholder, label in [
        ("tab-overview", "<!-- {ref_overview} -->", "影响分析"),
        ("tab-companies", "<!-- {ref_companies} -->", "公司分析"),
    ]:
        m = re.search(rf'id="{re.escape(tab_id)}"(.*?){re.escape(placeholder)}', html, re.DOTALL)
        if m:
            html = html.replace(placeholder, "")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ Market impact report generated: {output_path}")
    size_kb = os.path.getsize(output_path) / 1024
    print(f"   Size: {size_kb:.0f} KB")


def interactive_prompt():
    """Print prompts for AI to fill in market data interactively."""
    print("=" * 60)
    print("📊 跨市场影响分析报告 — 交互模式")
    print("=" * 60)
    print()
    print("请准备以下数据（通过搜索获取后传入 --events 参数使用 JSON 格式）：")
    print()
    print("1️⃣  市场概览 (market_overview)")
    print("    - a_share: A股近期走势、热点板块、资金流向")
    print("    - korea: 韩国股市近期动态、半导体/电池/造船等行业")
    print("    - us: 美股近期走势、科技股/利率/政策变化")
    print()
    print("2️⃣  板块影响 (sectors)")
    print("    每个板块包含：")
    print("    - name: 板块名称")
    print("    - impact: 利好/利空/中性")
    print("    - confidence: 高/中/低")
    print("    - events: 触发事件列表")
    print("    - mechanism: 传导机制")
    print("    - explanation: 详细分析")
    print("    - companies: 相关公司列表 (code, market, name, reason)")
    print()
    print("3️⃣  使用示例：")
    print("    python market_impact_report.py --events events.json -o report.html")
    print()
    print("JSON 模板：")
    print('''{{
  "report_title": "跨市场影响分析报告: 2026-06",
  "report_date": "{date}",
  "market_overview": {{
    "a_share": "A股...",
    "korea": "韩国...",
    "us": "美股..."
  }},
  "sectors": [
    {{
      "name": "半导体",
      "impact": "利好",
      "confidence": "高",
      "events": ["US AI chip export controls"],
      "mechanism": "供应链 · 政策外溢",
      "explanation": "国产替代加速...",
      "companies": [
        {{"code": "002371", "market": "sz", "name": "北方华创", "reason": "半导体设备龙头"}}
      ]
    }}
  ]
}}'''.format(date=datetime.now().strftime("%Y-%m-%d")))
    return None


def main():
    parser = argparse.ArgumentParser(description="生成跨市场影响分析报告")
    parser.add_argument("--events", "-e", help="Events JSON file path")
    parser.add_argument("--output", "-o", default="market_impact_report.html", help="Output HTML file")
    args = parser.parse_args()

    if args.events:
        with open(args.events, "r", encoding="utf-8") as f:
            data = json.load(f)
        generate_report(data, args.output)
    else:
        interactive_prompt()


if __name__ == "__main__":
    main()
