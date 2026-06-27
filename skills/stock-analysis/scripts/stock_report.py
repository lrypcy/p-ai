#!/usr/bin/env python3
"""
Comprehensive stock analysis report generator.

Fetches real data from AKShare and produces a structured report with:
  - Company profile and valuation
  - Quarterly financial trends
  - Technical indicator analysis (MA, MACD, RSI, Bollinger)
  - Market sentiment (委比 from order book)
  - Buy/Hold/Sell recommendation with confidence scoring

Usage:
    # Full report for a single A-share stock
    python stock_report.py --symbol 000001

    # Report without technicals (faster, fewer API calls)
    python stock_report.py --symbol 600519 --skip-technical

    # Report for Hong Kong stock
    python stock_report.py --symbol 00700 --market hk

    # Output to file
    python stock_report.py --symbol 000001 --output report.txt
"""

import argparse
import sys
from typing import Optional

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("pandas and numpy required. Install: pip install pandas numpy")
    sys.exit(1)

try:
    import akshare as ak
except ImportError:
    print("akshare required. Install: pip install akshare")
    sys.exit(1)

# ── Helpers ──────────────────────────────────────────────────────────────────


def extract_info(info_df: pd.DataFrame, key: str) -> str:
    """Extract a value from stock_individual_info_em DataFrame by item name."""
    try:
        return info_df.loc[info_df["item"] == key, "value"].values[0]
    except (IndexError, KeyError):
        return "N/A"


def format_market_cap(val) -> str:
    """Format market cap value (in 亿元 if large)."""
    try:
        v = float(val)
        if v > 1e8:
            return f"{v / 1e8:.2f}亿"
        return f"{v:.2f}"
    except (ValueError, TypeError):
        return str(val)


def compute_weibi(bid_ask_df: pd.DataFrame) -> float:
    """Compute 委比 (entrust ratio) from bid/ask level 2 data.

    委比 = (委买总量 - 委卖总量) / (委买总量 + 委卖总量) x 100%
    Range: -100% (full sell pressure) to +100% (full buy pressure).
    """
    try:
        row = bid_ask_df.iloc[0]
        buy_vol = sum(row.get(f"买{i}量", 0) for i in range(1, 6))
        sell_vol = sum(row.get(f"卖{i}量", 0) for i in range(1, 6))
        total = buy_vol + sell_vol
        if total == 0:
            return 0.0
        return round((buy_vol - sell_vol) / total * 100, 1)
    except Exception:
        return 0.0


# ── Data Collection ─────────────────────────────────────────────────────────


def collect_a_share_data(symbol: str, skip_technical: bool = False) -> dict:
    """Collect all data for an A-share stock analysis."""
    data = {}

    # Company profile
    data["info"] = ak.stock_individual_info_em(symbol)

    # Quarterly financials
    try:
        data["income"] = ak.stock_financial_income_statement_by_report_em(symbol)
    except Exception:
        data["income"] = None

    # Bid/ask (level 2) for 委比
    try:
        data["bid_ask"] = ak.stock_bid_ask_em(symbol)
    except Exception:
        data["bid_ask"] = None

    # K-line for technical analysis
    if not skip_technical:
        try:
            data["kline"] = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date="20250101",
                end_date="20260626",
                adjust="qfq",
            )
        except Exception:
            data["kline"] = None
    else:
        data["kline"] = None

    # Recent news
    try:
        news = ak.stock_news_em(symbol)
        data["news"] = news.head(5) if news is not None else None
    except Exception:
        data["news"] = None

    return data


def collect_hk_data(symbol: str, skip_technical: bool = False) -> dict:
    """Collect all data for a Hong Kong stock analysis."""
    data = {}

    # HK company profile
    try:
        data["info"] = ak.stock_hk_individual_info_em(symbol)
    except Exception:
        data["info"] = None

    # HK quarterly financials
    try:
        data["income"] = ak.stock_hk_financial_income_statement_by_report_em(symbol)
    except Exception:
        data["income"] = None

    # HK bid/ask
    try:
        data["bid_ask"] = ak.stock_hk_bid_ask_em(symbol)
    except Exception:
        data["bid_ask"] = None

    # HK K-line
    if not skip_technical:
        try:
            data["kline"] = ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date="20250101",
                end_date="20260626",
                adjust="qfq",
            )
        except Exception:
            data["kline"] = None
    else:
        data["kline"] = None

    # HK news
    try:
        news = ak.stock_hk_news_em(symbol)
        data["news"] = news.head(5) if news is not None else None
    except Exception:
        data["news"] = None

    return data


# ── Scoring ─────────────────────────────────────────────────────────────────


def score_technical(kline: pd.DataFrame) -> dict:
    """Score technical indicators 0-5 on each factor, max 15 total."""
    score = {
        "ma_score": 0,
        "macd_score": 0,
        "rsi_score": 0,
        "volume_score": 0,
        "total": 0,
        "details": {},
    }

    if kline is None or len(kline) < 30:
        score["total"] = 6  # Neutral default
        return score

    c = kline["收盘"]
    ma5 = c.rolling(5).mean()
    ma20 = c.rolling(20).mean()
    latest = kline.iloc[-1]
    latest_close = latest["收盘"]

    # MA alignment score
    if latest_close > ma5.iloc[-1] > ma20.iloc[-1]:
        score["ma_score"] = 5
    elif latest_close > ma20.iloc[-1] and latest_close > ma5.iloc[-1]:
        score["ma_score"] = 4
    elif latest_close > ma20.iloc[-1]:
        score["ma_score"] = 3
    elif latest_close > ma5.iloc[-1]:
        score["ma_score"] = 2
    else:
        score["ma_score"] = 1 if latest_close > ma20.iloc[-1] * 0.95 else 0

    # RSI score
    delta = c.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi_series = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    rsi_val = rsi_series.iloc[-1]

    if 40 <= rsi_val <= 60:
        score["rsi_score"] = 5
    elif 30 <= rsi_val < 40 or 60 < rsi_val <= 70:
        score["rsi_score"] = 3
    elif rsi_val < 30:
        score["rsi_score"] = 2  # Oversold — potential bounce
    else:
        score["rsi_score"] = 0  # Overbought — caution

    # Volume score
    vol_ma5 = kline["成交量"].rolling(5).mean()
    latest_vol = kline["成交量"].iloc[-1]
    vol_ratio = latest_vol / vol_ma5.iloc[-1] if vol_ma5.iloc[-1] > 0 else 1
    if vol_ratio > 1.5 and latest_close > c.iloc[-2]:
        score["volume_score"] = 5  # Volume surge with price up
    elif vol_ratio > 1.5:
        score["volume_score"] = 4  # Volume surge, price mixed
    elif vol_ratio > 1.0:
        score["volume_score"] = 3
    elif vol_ratio > 0.7:
        score["volume_score"] = 2
    else:
        score["volume_score"] = 1

    score["total"] = score["ma_score"] + score["macd_score"] + score["rsi_score"] + score["volume_score"]
    score["details"] = {
        "latest_close": latest_close,
        "ma5": round(ma5.iloc[-1], 2) if not pd.isna(ma5.iloc[-1]) else "N/A",
        "ma20": round(ma20.iloc[-1], 2) if not pd.isna(ma20.iloc[-1]) else "N/A",
        "rsi_14": round(rsi_val, 1) if not pd.isna(rsi_val) else "N/A",
        "vol_ratio": round(vol_ratio, 2),
    }
    return score


def score_fundamental(info: pd.DataFrame, income: pd.DataFrame) -> dict:
    """Score fundamental indicators 0-5 on each factor, max 10 total."""
    score = {
        "pe_score": 0,
        "profit_score": 0,
        "total": 0,
        "details": {},
    }

    # PE score
    try:
        pe = extract_info(info, "市盈率-动态")
        pe_val = float(pe)
        if 0 < pe_val < 10:
            score["pe_score"] = 5
        elif pe_val < 15:
            score["pe_score"] = 4
        elif pe_val < 25:
            score["pe_score"] = 3
        elif pe_val < 40:
            score["pe_score"] = 2
        elif pe_val < 60:
            score["pe_score"] = 1
        else:
            score["pe_score"] = 0  # Very high PE or negative
        score["details"]["pe"] = pe_val
    except Exception:
        score["pe_score"] = 2
        score["details"]["pe"] = "N/A"

    # Profit growth (YoY)
    profit_growth = None
    try:
        if income is not None and len(income) >= 2:
            # Income statement: latest period at index 0
            latest_profit = income.iloc[0].get("净利润", None)
            prev_profit = income.iloc[1].get("净利润", None)
            if latest_profit and prev_profit and prev_profit != 0:
                profit_growth = (latest_profit - prev_profit) / abs(prev_profit) * 100
    except Exception:
        pass

    if profit_growth is not None:
        if profit_growth > 30:
            score["profit_score"] = 5
        elif profit_growth > 15:
            score["profit_score"] = 4
        elif profit_growth > 5:
            score["profit_score"] = 3
        elif profit_growth > 0:
            score["profit_score"] = 2
        elif profit_growth > -15:
            score["profit_score"] = 1
        else:
            score["profit_score"] = 0
    else:
        score["profit_score"] = 2  # No data — neutral

    score["details"]["profit_growth_yoy"] = (
        round(profit_growth, 1) if profit_growth is not None else "N/A"
    )
    score["total"] = score["pe_score"] + score["profit_score"]
    return score


def score_sentiment(bid_ask, news_df) -> dict:
    """Score market sentiment factors 0-5 based on 委比 and news."""
    score = {"weibi_score": 0, "weibi": 0, "news_count": 0, "news_titles": []}

    # 委比 score
    if bid_ask is not None:
        weibi = compute_weibi(bid_ask)
        score["weibi"] = weibi
        if weibi > 30:
            score["weibi_score"] = 5
        elif weibi > 10:
            score["weibi_score"] = 4
        elif weibi > -10:
            score["weibi_score"] = 3
        elif weibi > -30:
            score["weibi_score"] = 2
        else:
            score["weibi_score"] = 1

    # News
    if news_df is not None:
        count = len(news_df)
        score["news_count"] = count
        if "新闻标题" in news_df.columns:
            score["news_titles"] = news_df["新闻标题"].tolist()

    return score


def generate_recommendation(tech_score: float, fund_score: float, sent_score: float) -> tuple:
    """Generate buy/hold/sell recommendation based on composite score.

    Weights: Technical 40%, Fundamental 40%, Sentiment 20%.

    Returns: (recommendation, confidence, composite_score)
    """
    # Normalize to 0-5 scale
    tech_norm = min(tech_score / 3, 5.0)  # tech total max 15
    fund_norm = min(fund_score / 2, 5.0)  # fund total max 10
    sent_norm = sent_score

    composite = tech_norm * 0.4 + fund_norm * 0.4 + sent_norm * 0.2

    if composite >= 4.0:
        return ("买入 (Buy)", "Strong", composite)
    elif composite >= 3.0:
        return ("增持 (Accumulate)", "Moderate", composite)
    elif composite >= 2.0:
        return ("持有 (Hold)", "Neutral", composite)
    elif composite >= 1.0:
        return ("减持 (Reduce)", "Cautious", composite)
    else:
        return ("卖出 (Sell)", "Strong", composite)


# ── Report Generation ───────────────────────────────────────────────────────


def generate_report(symbol: str, data: dict, market_label: str) -> str:
    """Generate formatted text report from collected data."""
    info = data.get("info")
    income = data.get("income")
    bid_ask = data.get("bid_ask")
    kline = data.get("kline")
    news_df = data.get("news")

    # ── Scoring ──────────────────────────────────────────────────────────
    tech = score_technical(kline)
    fund = score_fundamental(info, income)
    sent = score_sentiment(bid_ask, news_df)
    rec, conf, composite = generate_recommendation(tech["total"], fund["total"], sent["weibi_score"])

    # ── Company Overview ─────────────────────────────────────────────────
    company_name = extract_info(info, "股票简称") if info is not None else "N/A"
    industry = extract_info(info, "行业") if info is not None else "N/A"
    market_cap = extract_info(info, "总市值") if info is not None else "N/A"
    float_mc = extract_info(info, "流通市值") if info is not None else "N/A"
    pe = extract_info(info, "市盈率-动态") if info is not None else "N/A"
    pb = extract_info(info, "市净率") if info is not None else "N/A"
    eps = extract_info(info, "每股收益") if info is not None else "N/A"

    lines = []
    lines.append("=" * 55)
    lines.append(f"  {company_name} ({symbol}) — 综合分析报告")
    lines.append(f"  Market: {market_label.upper()}")
    lines.append("=" * 55)
    lines.append("")

    # ── Recommendation ──────────────────────────────────────────────────
    lines.append(f"  ★ 推荐: {rec}  (信心: {conf}, 综合评分: {composite:.2f}/5.0)")
    lines.append("")

    # ── Company Profile ─────────────────────────────────────────────────
    lines.append("─" * 45)
    lines.append("  公司概况")
    lines.append("─" * 45)
    lines.append(f"    名称: {company_name}")
    lines.append(f"    行业: {industry}")
    lines.append(f"    总市值: {format_market_cap(market_cap)}")
    lines.append(f"    流通市值: {format_market_cap(float_mc)}")
    lines.append(f"    市盈率(动态): {pe}")
    lines.append(f"    市净率: {pb}")
    lines.append(f"    每股收益: {eps}")
    lines.append("")

    # ── Financial Overview ──────────────────────────────────────────────
    lines.append("─" * 45)
    lines.append("  财务概览")
    lines.append("─" * 45)
    try:
        if income is not None and len(income) > 0:
            lines.append(f"    最近4个季度净利润趋势:")
            # Show last 4 quarters (newest first)
            for i in range(min(4, len(income))):
                row = income.iloc[i]
                period = row.get("报告期", "N/A")
                revenue = row.get("营业收入", "N/A")
                profit = row.get("净利润", "N/A")
                lines.append(f"      {period}: 营收={revenue}  净利润={profit}")
        else:
            lines.append("    (财务数据暂不可用)")
    except Exception:
        lines.append("    (无法解析财务数据)")

    lines.append(f"    净利润同比增长: {fund['details'].get('profit_growth_yoy', 'N/A')}%")
    lines.append("")

    # ── Technical Analysis ──────────────────────────────────────────────
    lines.append("─" * 45)
    lines.append("  技术分析")
    lines.append("─" * 45)
    if tech["details"]:
        d = tech["details"]
        lines.append(f"    最新收盘: {d.get('latest_close', 'N/A')}")
        lines.append(f"    MA5: {d.get('ma5', 'N/A')}  |  MA20: {d.get('ma20', 'N/A')}")
        lines.append(f"    RSI(14): {d.get('rsi_14', 'N/A')}  |  量比: {d.get('vol_ratio', 'N/A')}")
        lines.append(f"    MA评分: {tech['ma_score']}/5  |  RSI评分: {tech['rsi_score']}/5  |  量价评分: {tech['volume_score']}/5")
    else:
        lines.append("    (技术数据暂不可用)")
    lines.append(f"    技术总分: {tech['total']}/15")
    lines.append("")

    # ── Sentiment ───────────────────────────────────────────────────────
    lines.append("─" * 45)
    lines.append("  市场情绪")
    lines.append("─" * 45)
    lines.append(f"    委比: {sent['weibi']}%  (评分: {sent['weibi_score']}/5)")
    lines.append(f"    近期相关新闻: {sent['news_count']} 条")
    for title in sent["news_titles"][:3]:
        lines.append(f"      · {title}")
    lines.append("")

    # ── Scoring Summary ────────────────────────────────────────────────
    lines.append("─" * 45)
    lines.append("  评分汇总")
    lines.append("─" * 45)
    lines.append(f"    基本面评分: {fund['total']}/10")
    lines.append(f"    技术面评分: {tech['total']}/15")
    lines.append(f"    情绪面评分: {sent['weibi_score']}/5")
    lines.append(f"    综合评分: {composite:.2f}/5.0")
    lines.append("")

    # ── Footer ──────────────────────────────────────────────────────────
    lines.append("=" * 55)
    lines.append("  ⚠️ 本报告基于公开数据自动生成，仅供参考，不构成投资建议。")
    lines.append("=" * 55)

    return "\n".join(lines)


def generate_html_report(symbol: str, data: dict, market_label: str) -> str:
    """Generate interactive HTML report from collected data."""
    import json

    info = data.get("info")
    income = data.get("income")
    bid_ask = data.get("bid_ask")
    kline = data.get("kline")
    news_df = data.get("news")

    # ── Scoring ──────────────────────────────────────────────────────────
    tech = score_technical(kline)
    fund = score_fundamental(info, income)
    sent = score_sentiment(bid_ask, news_df)
    rec, conf, composite = generate_recommendation(tech["total"], fund["total"], sent["weibi_score"])

    # ── Company Overview ─────────────────────────────────────────────────
    company_name = extract_info(info, "股票简称") if info is not None else "N/A"
    industry = extract_info(info, "行业") if info is not None else "N/A"
    market_cap = extract_info(info, "总市值") if info is not None else "N/A"
    float_mc = extract_info(info, "流通市值") if info is not None else "N/A"
    pe = extract_info(info, "市盈率-动态") if info is not None else "N/A"
    pb = extract_info(info, "市净率") if info is not None else "N/A"
    eps = extract_info(info, "每股收益") if info is not None else "N/A"

    rec_color = {"买入 (Buy)": "#e53e3e", "增持 (Accumulate)": "#dd6b20", "持有 (Hold)": "#d69e2e",
                  "减持 (Reduce)": "#718096", "卖出 (Sell)": "#38a169"}.get(rec, "#718096")

    # K-line data for chart
    kline_data = []
    quarterly_data = []
    if kline is not None and len(kline) > 0:
        for _, row in kline.iterrows():
            try:
                kline_data.append({
                    "date": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": int(row.get("成交量", 0)),
                })
            except (ValueError, TypeError):
                pass

    if income is not None and len(income) > 0:
        for _, row in income.iterrows():
            try:
                quarterly_data.append({
                    "label": str(row.get("报告期", ""))[:7],
                    "revenue": float(row.get("营业收入", 0)) / 1e8 if float(row.get("营业收入", 0)) > 1e8 else float(row.get("营业收入", 0)),
                    "profit": float(row.get("净利润", 0)) / 1e8 if float(row.get("净利润", 0)) > 1e8 else float(row.get("净利润", 0)),
                })
            except (ValueError, TypeError):
                pass

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{company_name} ({symbol}) — 综合投资分析报告</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#f0f2f5;color:#333;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}}
.header{{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;padding:50px 30px 35px;text-align:center}}
.header h1{{font-size:26px;margin-bottom:4px}}
.header .sub{{color:#a0aec0;font-size:13px}}
.cont{{max-width:1000px;margin:0 auto;padding:16px}}
.card{{background:#fff;border-radius:12px;margin-bottom:18px;box-shadow:0 2px 12px rgba(0,0,0,0.06);overflow:hidden}}
.card-hd{{padding:14px 20px;background:linear-gradient(135deg,#2d3748,#1a202c);color:#fff;font-size:15px;font-weight:600}}
.card-bd{{padding:16px 20px}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin:8px 0}}
.si{{background:#f7fafc;border-radius:6px;padding:8px;text-align:center}}
.si .l{{font-size:10px;color:#a0aec0}}
.si .v{{font-size:14px;font-weight:700;color:#2d3748}}
.rec-box{{text-align:center;padding:16px;border-radius:10px;margin:8px 0;background:linear-gradient(135deg,#fff5f5,#fff)}}
.rec-box .r{{font-size:28px;font-weight:700;color:{rec_color}}}
.rec-box .d{{font-size:12px;color:#718096;margin-top:4px}}
.tag{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}}
.tag-green{{background:#c6f6d5;color:#22543d}}
.tag-yellow{{background:#fefcbf;color:#744210}}
.tag-red{{background:#fed7d7;color:#742a2a}}
.tag-gray{{background:#edf2f7;color:#4a5568}}
.ctable{{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}}
.ctable td{{padding:6px 10px;border-bottom:1px solid #edf2f7}}
.ctable td:first-child{{color:#718096;width:120px}}
.chart-box{{width:100%;height:280px;margin-top:8px;border-radius:6px;background:#fafafa}}
.ft{{text-align:center;padding:20px;color:#a0aec0;font-size:11px}}
@media(max-width:600px){{.sg{{grid-template-columns:repeat(3,1fr)}}}}
</style>
</head>
<body>
<div class="header">
    <h1>{company_name} <span style="font-size:16px;color:#a0aec0">({symbol})</span></h1>
    <div class="sub">{industry} · {market_label} · {format_market_cap(market_cap)}</div>
</div>
<div class="cont">

<div class="card">
    <div class="rec-box">
        <div class="r">{rec}</div>
        <div class="d">信心: {conf} · 综合评分: {composite:.2f}/5.0 · PE: {pe} · PB: {pb}</div>
    </div>
</div>

<div class="card">
    <div class="card-hd">📊 技术分析</div>
    <div class="card-bd">
        <div class="sg">
            <div class="si"><div class="l">最新价</div><div class="v">{tech['details'].get('latest_close', 'N/A')}</div></div>
            <div class="si"><div class="l">MA5</div><div class="v">{tech['details'].get('ma5', 'N/A')}</div></div>
            <div class="si"><div class="l">MA20</div><div class="v">{tech['details'].get('ma20', 'N/A')}</div></div>
            <div class="si"><div class="l">RSI(14)</div><div class="v">{tech['details'].get('rsi_14', 'N/A')}</div></div>
            <div class="si"><div class="l">量比</div><div class="v">{tech['details'].get('vol_ratio', 'N/A')}</div></div>
        </div>
        <div><span class="tag {'tag-green' if tech['ma_score']>=3 else 'tag-yellow' if tech['ma_score']>=2 else 'tag-gray'}">MA: {tech['ma_score']}/5</span> <span class="tag {'tag-green' if tech['rsi_score']>=3 else 'tag-yellow' if tech['rsi_score']>=2 else 'tag-gray'}">RSI: {tech['rsi_score']}/5</span> <span class="tag {'tag-green' if tech['volume_score']>=3 else 'tag-yellow' if tech['volume_score']>=2 else 'tag-gray'}">量价: {tech['volume_score']}/5</span> <span class="tag tag-gray">总分: {tech['total']}/15</span></div>
    </div>
</div>

<div class="card">
    <div class="card-hd">📈 K线走势</div>
    <div class="card-bd"><div class="chart-box" id="klineChart"></div></div>
</div>

<div class="card">
    <div class="card-hd">💰 财务概览</div>
    <div class="card-bd">
        <table class="ctable">
            <tr><td>公司名称</td><td>{company_name}</td></tr>
            <tr><td>行业</td><td>{industry}</td></tr>
            <tr><td>总市值</td><td>{format_market_cap(market_cap)}</td></tr>
            <tr><td>流通市值</td><td>{format_market_cap(float_mc)}</td></tr>
            <tr><td>市盈率(动态)</td><td>{pe}</td></tr>
            <tr><td>市净率</td><td>{pb}</td></tr>
            <tr><td>每股收益</td><td>{eps}</td></tr>
            <tr><td>净利润同比增长</td><td>{fund['details'].get('profit_growth_yoy', 'N/A')}%</td></tr>
        </table>
        <div style="margin-top:8px"><span class="tag {'tag-green' if fund['pe_score']>=3 else 'tag-yellow' if fund['pe_score']>=2 else 'tag-gray'}">PE: {fund['pe_score']}/5</span> <span class="tag {'tag-green' if fund['profit_score']>=3 else 'tag-yellow' if fund['profit_score']>=2 else 'tag-gray'}">增长: {fund['profit_score']}/5</span> <span class="tag tag-gray">基本面: {fund['total']}/10</span></div>
        <div class="chart-box" id="quarterlyChart" style="height:200px"></div>
    </div>
</div>

<div class="card">
    <div class="card-hd">📰 市场情绪</div>
    <div class="card-bd">
        <div class="sg">
            <div class="si"><div class="l">委比</div><div class="v">{sent['weibi']}%</div></div>
            <div class="si"><div class="l">情绪评分</div><div class="v">{sent['weibi_score']}/5</div></div>
            <div class="si"><div class="l">相关新闻</div><div class="v">{sent['news_count']}条</div></div>
        </div>
        {"<ul style='margin-top:8px;font-size:13px;color:#718096'>" + "".join(f"<li style='margin-bottom:4px'>{t}</li>" for t in sent['news_titles'][:3]) + "</ul>" if sent['news_titles'] else ""}
    </div>
</div>

</div>
<div class="ft">⚠️ 自动生成 · 仅供参考 · 不构成投资建议 · 数据来源: AKShare/东方财富</div>

<script>
(function(){{
var kd = {json.dumps(kline_data)};
var qd = {json.dumps(quarterly_data)};

// K-line chart
var kc = document.getElementById('klineChart');
if(kc && kd.length > 0){{
    var ch = echarts.init(kc);
    ch.setOption({{
        tooltip:{{trigger:'axis',axisPointer:{{type:'cross'}},
            formatter:function(p){{var d=kd[p[0].dataIndex];return '<b>'+d.date+'</b><br/>开:'+d.open.toFixed(2)+' 收:'+d.close.toFixed(2)+'<br/>高:'+d.high.toFixed(2)+' 低:'+d.low.toFixed(2)+'<br/>量:'+(d.volume/10000).toFixed(0)+'万手';}}}},
        grid:[{{left:'6%',right:'3%',top:'4%',height:'59%'}},{{left:'6%',right:'3%',top:'72%',height:'21%'}}],
        xAxis:[{{type:'category',data:kd.map(x=>x.date.slice(5)),gridIndex:0,axisLabel:{{fontSize:9,rotate:30}}}},
               {{type:'category',data:kd.map(x=>x.date.slice(5)),gridIndex:1,axisLabel:{{show:false}}}}],
        yAxis:[{{type:'value',scale:true,gridIndex:0,splitLine:{{lineStyle:{{type:'dashed',color:'#e2e8f0'}}}}}},
               {{type:'value',scale:true,gridIndex:1,splitLine:{{show:false}},axisLabel:{{show:false}}}}],
        series:[
            {{name:'K',type:'candlestick',xAxisIndex:0,yAxisIndex:0,data:kd.map(x=>[x.open,x.close,x.low,x.high]),
              itemStyle:{{color:'#e53e3e',color0:'#38a169',borderColor:'#e53e3e',borderColor0:'#38a169'}}}},
            {{name:'V',type:'bar',xAxisIndex:1,yAxisIndex:1,data:kd.map(x=>{{return {{value:x.volume,itemStyle:{{color:x.open<=x.close?'#e53e3e':'#38a169'}}}}}})}},
        ],
        dataZoom:[{{type:'inside',xAxisIndex:[0,1],start:Math.max(0,100-30),end:100}}]
    }});
    window.addEventListener('resize',function(){{ch.resize()}});
}}

// Quarterly profit chart
var qch = document.getElementById('quarterlyChart');
if(qch && qd.length > 0){{
    var ch2 = echarts.init(qch);
    ch2.setOption({{
        tooltip:{{trigger:'axis',formatter:function(p){{var d=qd[p[0].dataIndex];return '<b>'+d.label+'</b><br/>净利润: '+d.profit.toFixed(2)+'亿<br/>营收: '+d.revenue.toFixed(1)+'亿';}}}},
        grid:{{left:'6%',right:'3%',top:'8%',bottom:'14%'}},
        xAxis:{{type:'category',data:qd.map(x=>x.label),axisLabel:{{fontSize:9,interval:0}}}},
        yAxis:{{type:'value',scale:true,splitLine:{{lineStyle:{{type:'dashed',color:'#e2e8f0'}}}},axisLabel:{{fontSize:9}}}},
        series:[{{name:'净利润',type:'bar',data:qd.map(x=>{{return {{value:Math.round(x.profit*100)/100,itemStyle:{{color:x.profit>=0?'#e53e3e':'#38a169'}}}}}}),barWidth:'50%',
                 markLine:{{silent:true,data:[{{yAxis:0,lineStyle:{{type:'solid',color:'#718096',opacity:0.3}}}}]}}}}]
    }});
    window.addEventListener('resize',function(){{ch2.resize()}});
}}
}})();
</script>
</body>
</html>"""

# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive stock analysis report"
    )
    parser.add_argument(
        "--symbol", "-s", required=True,
        help="Stock code, e.g. 000001 (A-share) or 00700 (HK)"
    )
    parser.add_argument(
        "--market", "-m", choices=["a", "hk"], default="a",
        help="Market: a = A-share, hk = Hong Kong"
    )
    parser.add_argument(
        "--skip-technical", action="store_true",
        help="Skip technical indicator fetching (faster)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write report to file instead of stdout"
    )
    parser.add_argument(
        "--html", action="store_true",
        help="Generate HTML format report (with ECharts interactive charts)"
    )
    args = parser.parse_args()

    print(f"Fetching data for {args.symbol} ({'A-share' if args.market == 'a' else 'HK'})...")

    if args.market == "a":
        data = collect_a_share_data(args.symbol, args.skip_technical)
        market_label = "A-share"
    else:
        data = collect_hk_data(args.symbol, args.skip_technical)
        market_label = "HK"

    if not data.get("info") is None or data.get("kline") is not None:
        if args.html:
            report = generate_html_report(args.symbol, data, market_label)
        else:
            report = generate_report(args.symbol, data, market_label)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    else:
        print(f"Error: No data returned for {args.symbol}. Check the symbol code and market setting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
