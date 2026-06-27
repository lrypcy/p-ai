#!/usr/bin/env python3
"""
Shared HTML/CSS Theme Module for Chain Analysis Reports.

Provides a unified design system (CSS variables, common components, JS snippets)
so every generated HTML report shares a consistent visual style regardless of
which script produces it.

Usage:
    from html_theme import CSS_COMMON, generate_header, generate_footer, ...

    html = f'''<!DOCTYPE html>
    <html>
    <head>
    <style>:root {{
      --accent: #667eea;
      --primary-from: #0f0c29;
      --primary-mid: #302b63;
      --primary-to: #24243e;
    }}
    {CSS_COMMON}
    /* report-specific overrides here */
    </style>
    </head>
    <body>
    {generate_header("产业报告", "...", "...", accent="#667eea")}
    ...
    {generate_footer()}
    </body>
    </html>'''
"""

from datetime import datetime
from typing import Optional

# ════════════════════════════════════════════════════════════════
# COMMON CSS — uses CSS custom properties for theming
# Override :root variables per report to customize colors
# ════════════════════════════════════════════════════════════════

CSS_COMMON = """
/* ════════════════════════════════════════
   Chain Analysis — Shared Design System
   ════════════════════════════════════════ */

/* ── Reset & Base ── */
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg,#f0f2f5);color:var(--text,#1a1a2e);font-family:-apple-system,'PingFang SC','Microsoft YaHei','Helvetica Neue',sans-serif;line-height:1.6}

/* ── CSS Variables (defaults) ── */
:root {
  --primary-from: #0f0c29;
  --primary-mid: #302b63;
  --primary-to: #24243e;
  --accent: #667eea;
  --accent-light: rgba(102,126,234,0.1);
  --bg: #f0f2f5;
  --card-bg: #fff;
  --text: #1a1a2e;
  --text-muted: #718096;
  --text-light: #a0aec0;
  --border: #e2e8f0;
  --section-hd-bg: linear-gradient(135deg,#2d3748,#1a202c);
  --table-hd-bg: #f1f5f9;
  --table-hd-color: #475569;
  --tag-red-bg: #fef2f2;
  --tag-red-color: #dc2626;
  --tag-orange-bg: #fff7ed;
  --tag-orange-color: #ea580c;
  --tag-yellow-bg: #fefce8;
  --tag-yellow-color: #ca8a04;
  --tag-green-bg: #f0fdf4;
  --tag-green-color: #16a34a;
  --tag-blue-bg: #eff6ff;
  --tag-blue-color: #2563eb;
  --bt-red-bg: #fef2f2;
  --bt-red-border: #dc2626;
  --bt-red-color: #991b1b;
  --bt-orange-bg: #fff7ed;
  --bt-orange-border: #ea580c;
  --bt-orange-color: #9a3412;
  --bt-yellow-bg: #fefce8;
  --bt-yellow-border: #ca8a04;
  --bt-yellow-color: #854d0e;
  --bt-green-bg: #f0fdf4;
  --bt-green-border: #16a34a;
  --bt-green-color: #166534;
  --up: #e53e3e;
  --down: #38a169;
  --co-link: #2563eb;
  --co-hd-bg: linear-gradient(135deg,#f7fafc,#edf2f7);
}

/* ── Header ── */
.header{background:linear-gradient(135deg,var(--primary-from),var(--primary-mid),var(--primary-to));color:#fff;padding:45px 30px 30px;text-align:center}
.header h1{font-size:28px;margin-bottom:8px;letter-spacing:1px}
.header .sub{color:#a0aec0;font-size:13px;margin-bottom:4px}
.header .dt{color:#718096;font-size:11px;margin-top:4px}

/* ── Container ── */
.cont{max-width:1400px;margin:0 auto;padding:16px}

/* ── Tab Content ── */
.tab-content{display:none}
.tab-content.active{display:block}

/* ── Tab Navigation (general) ── */
.seg-nav{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}
.sn{display:inline-block;padding:5px 12px;border-radius:6px;background:#f1f5f9;color:#475569;text-decoration:none;font-size:12px;transition:all 0.2s;border:1px solid var(--border,#e2e8f0);cursor:pointer;white-space:nowrap}
.sn:hover{background:#e2e8f0;color:#1e293b;border-color:#cbd5e1}

/* ── Fixed Top Nav (PCB style) ── */
.top-nav{position:fixed;top:0;left:0;right:0;z-index:1000;background:linear-gradient(135deg,var(--primary-from),var(--primary-mid));display:flex;align-items:center;overflow-x:auto;white-space:nowrap;padding:0 8px;height:56px;gap:2px}
.top-nav .ntt{color:#e2e8f0;font-weight:700;font-size:13px;padding:0 10px;flex-shrink:0}
.top-nav .tab{color:#a0aec0;text-decoration:none;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;transition:.2s;flex-shrink:0}
.top-nav .tab:hover,.top-nav .tab.active{background:rgba(255,255,255,0.12);color:#fff}
.top-nav .tab-sep{color:#2d3748;font-size:10px;padding:0 2px}
body.has-top-nav{padding-top:56px}

/* ── Chain Selector (chain_report style) ── */
.cs-bar{background:rgba(255,255,255,0.08);padding:10px 30px;text-align:center;display:flex;justify-content:center;gap:6px;flex-wrap:wrap}
.cs{display:inline-block;padding:6px 14px;border-radius:20px;color:#a0aec0;text-decoration:none;font-size:13px;transition:all 0.2s}
.cs:hover{background:rgba(255,255,255,0.15);color:#fff}
.cs.active{background:var(--accent);color:#fff;font-weight:600}

/* ── Sections ── */
.sec{background:var(--card-bg,#fff);border-radius:14px;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.06);overflow:hidden;transition:box-shadow 0.2s}
.sec:hover{box-shadow:0 4px 20px rgba(0,0,0,0.1)}
.sec-hd{background:var(--section-hd-bg,linear-gradient(135deg,#2d3748,#1a202c));padding:14px 24px;color:#fff}
.sec-hd h2{font-size:16px;font-weight:600}
.sec-bd{padding:12px 24px 18px}
.sec-desc{color:#4a5568;font-size:14px;line-height:1.8;margin-bottom:14px}

/* ── Overview Box (chain_report) ── */
.over{background:var(--card-bg,#fff);border-radius:14px;padding:18px 24px;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.06)}
.over h3{margin-bottom:10px;color:#1e293b;font-size:15px;font-weight:600}
.over p,.over li{color:#64748b;line-height:1.8;font-size:13px}
.over ul{padding-left:20px}

/* ── Stats Grid ── */
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:8px 0}
.si{background:#f7fafc;border-radius:8px;padding:10px;text-align:center;border:1px solid #eef2f7}
.si .sl,.si .l{font-size:10px;color:#a0aec0;margin-bottom:2px;text-transform:uppercase;letter-spacing:0.3px}
.si .sv,.si .v{font-size:15px;font-weight:700;color:#2d3748}
.si .st,.si .s{font-size:10px;color:#718096;margin-top:2px}

/* ── Card Grid (glass style) ── */
.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:4px 0 12px}
.card-item{background:#f8fafc;border-radius:10px;padding:14px 12px;text-align:center;border:1px solid #eef2f7}
.card-item .l{font-size:11px;color:#94a3b8;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px}
.card-item .v{font-size:16px;font-weight:700;color:#1e293b}
.card-item .s{font-size:11px;color:#94a3b8;margin-top:4px}

/* ── Charts ── */
.chart-box{width:100%;height:360px;margin:8px 0 4px}
.chart-box-sm{height:280px}  /* for card-embedded charts */

/* ── Tables ── */
.ctable{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px}
.ctable th{background:var(--table-hd-bg);padding:10px 12px;text-align:left;font-weight:600;color:var(--table-hd-color);font-size:12px;text-transform:uppercase;letter-spacing:0.3px}
.ctable td{padding:10px 12px;border-bottom:1px solid var(--border,#e2e8f0);font-size:13px}
.ctable tr:last-child td{border-bottom:none}
.ctable tr:hover{background:#f8fafc}
.ctable code{background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:12px;color:var(--accent,#2563eb)}

/* ── Clickable Company Links ── */
.co-link{color:var(--co-link,#2563eb);text-decoration:none;font-weight:600;cursor:pointer}
.co-link:hover{text-decoration:underline;color:#1d4ed8}
.co-link-tag{display:inline-block;padding:1px 6px;border-radius:4px;background:var(--accent-light,#eff6ff);color:var(--co-link,#2563eb);text-decoration:none;font-size:12px;cursor:pointer}
.co-link-tag:hover{background:#dbeafe}

/* ── Bottleneck / Warning Boxes ── */
.bt-box{background:var(--bt-yellow-bg);border-left:4px solid var(--bt-yellow-border);color:var(--bt-yellow-color);padding:10px 16px;margin:8px 0 12px;font-size:13px;line-height:1.7;border-radius:0 8px 8px 0}
.bt-red,.btl{background:var(--bt-red-bg);border-left:4px solid var(--bt-red-border);color:var(--bt-red-color)}
.bt-orange,.btm{background:var(--bt-orange-bg);border-left:4px solid var(--bt-orange-border);color:var(--bt-orange-color)}
.bt-yellow{background:var(--bt-yellow-bg);border-left:4px solid var(--bt-yellow-border);color:var(--bt-yellow-color)}
.bt-green,.btg{background:var(--bt-green-bg);border-left:4px solid var(--bt-green-border);color:var(--bt-green-color)}
.btl,.btm,.btg{padding:10px 14px;margin:10px 0;font-size:12px;line-height:1.6;border-radius:0 6px 6px 0}

/* ── Tags ── */
.tag{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;margin:0 2px}
.tag-red,.tag-r{background:var(--tag-red-bg);color:var(--tag-red-color)}
.tag-orange,.tag-o{background:var(--tag-orange-bg);color:var(--tag-orange-color)}
.tag-yellow,.tag-y{background:var(--tag-yellow-bg);color:var(--tag-yellow-color)}
.tag-green,.tag-g{background:var(--tag-green-bg);color:var(--tag-green-color)}
.tag-blue,.tag-b{background:var(--tag-blue-bg);color:var(--tag-blue-color)}

/* ── Stock Cards ── */
.co-card{background:var(--card-bg,#fff);border-radius:12px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.04);overflow:hidden}
.co-hd{background:var(--co-hd-bg,linear-gradient(135deg,#f7fafc,#edf2f7));padding:12px 16px;border-bottom:1px solid var(--border,#e2e8f0);display:flex;justify-content:space-between;align-items:center}
.co-n{font-size:16px;font-weight:700;color:#1a202c}
.co-c{font-size:11px;color:#718096;background:#edf2f7;padding:1px 6px;border-radius:10px}
.co-t{font-size:10px;background:#ebf4ff;color:#2b6cb0;padding:1px 6px;border-radius:10px;font-weight:600}
.co-tag{font-size:11px;background:#e2e8f0;padding:2px 8px;border-radius:10px;color:#4a5568}
.co-bd{padding:14px 16px}
.co-ic{margin-bottom:10px}
.il .il-l{font-size:10px;color:#a0aec0;margin-bottom:2px}
.il .il-t{font-size:13px;color:#4a5568;line-height:1.5}
.co-charts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
@media(max-width:768px){.co-charts{grid-template-columns:1fr}}

/* ── Stock Subnav ── */
.stock-subnav{display:flex;flex-wrap:wrap;gap:4px;margin:10px 0 14px}
.stock-subnav .sn{font-size:11px}

/* ── Up/Down ── */
.up{color:var(--up,#e53e3e)}
.down{color:var(--down,#38a169)}

/* ── External Link (同花顺) ── */
.ext-link{font-size:10px;color:#3182ce;text-decoration:none;background:#ebf8ff;padding:1px 8px;border-radius:8px;font-weight:600;transition:.15s}
.ext-link:hover{background:#3182ce;color:#fff;text-decoration:none}

/* ── News Section ── */
.co-news{background:#fafcff;border-radius:8px;padding:10px 12px;margin-top:10px;border:1px solid var(--border,#e2e8f0)}
.co-news-hd{font-size:12px;font-weight:700;color:#2d3748;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid var(--border,#e2e8f0)}
.news-item{font-size:11px;padding:4px 0;display:flex;align-items:flex-start;gap:4px;line-height:1.4;border-bottom:1px solid #f0f2f5}
.news-item:last-child{border-bottom:none}
.news-item .news-icon{flex-shrink:0;width:18px;text-align:center}
.news-item a{color:#2b6cb0;text-decoration:none;flex:1}
.news-item a:hover{text-decoration:underline;color:#e53e3e}
.news-item .news-meta{flex-shrink:0;font-size:9px;color:#a0aec0;white-space:nowrap}
.news-good{border-left:3px solid var(--bt-green-border,#38a169);padding-left:4px}
.news-bad{border-left:3px solid var(--bt-red-border,#e53e3e);padding-left:4px}

/* ── Footer ── */
.ft{text-align:center;padding:24px;color:#94a3b8;font-size:11px;line-height:1.8}
.ft a{color:#64748b;text-decoration:underline}

/* ── Bottleneck Summary Tags (chain_report) ── */
.bottleneck-tag{padding:10px 16px;margin:8px 0 12px;font-size:13px;line-height:1.7;border-radius:0 8px 8px 0}
.btd{display:inline-block;padding:2px 10px;border-radius:12px;font-weight:600;font-size:12px}

/* ── Flow Box (PCB topology) ── */
.flow-box{display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:center;padding:14px;background:#f7fafc;border-radius:8px;margin:10px 0;font-size:12px}
.flow-node{background:var(--primary-mid);color:#fff;padding:6px 14px;border-radius:6px;font-weight:600;text-align:center;min-width:70px}
.flow-arrow{color:#a0aec0;font-size:16px}
.flow-node-down{background:#48bb78;color:#fff;padding:6px 14px;border-radius:6px;font-weight:600;text-align:center;min-width:70px}

/* ── Timeline (glass style) ── */
.tline{position:relative;padding:0;list-style:none;margin:12px 0}
.tline li{padding:6px 0 6px 20px;border-left:2px solid #e2e8f0;position:relative;font-size:13px;color:#4a5568;margin-left:8px}
.tline li:before{content:'';position:absolute;left:-5px;top:12px;width:8px;height:8px;border-radius:50%;background:var(--accent,#667eea)}
.tline li .d{font-size:11px;color:#94a3b8}

/* ── Citation superscript (PCB) ── */
sup.src{font-size:9px;color:var(--co-link,#2b6cb0);cursor:pointer;font-weight:600;margin:0 1px}
sup.src:hover{color:#e53e3e;text-decoration:underline}

/* ── Reference Section (PCB) ── */
.ref-section{background:var(--card-bg,#fff);border-radius:12px;padding:20px 24px;margin-bottom:20px;font-size:12px;color:#4a5568}
.ref-section h3{font-size:14px;margin-bottom:10px;color:#2d3748}
.ref-section ol{padding-left:20px;line-height:1.8}

/* ── Scroll margin ── */
.tab-target{scroll-margin-top:64px}

/* ── Dashboard Grid ── */
.dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:20px}
.dashboard-item{background:var(--card-bg,#fff);border-radius:10px;padding:14px 12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);border-top:3px solid var(--accent,#667eea)}
.dashboard-item .d-label{font-size:10px;color:#94a3b8;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px}
.dashboard-item .d-value{font-size:18px;font-weight:700;color:var(--text,#1e293b)}
.dashboard-item .d-sub{font-size:10px;color:#94a3b8;margin-top:2px}

/* ── Side-by-side chart containers ── */
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:900px){.chart-row{grid-template-columns:1fr}}

/* ── Special: scale chart grid (chain_report) ── */
.sc{background:var(--card-bg,#fff);border-radius:14px;margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.06);overflow:hidden;padding:16px 24px}
.sc:hover{box-shadow:0 4px 20px rgba(0,0,0,0.1)}

/* ── Responsive ── */
@media(max-width:768px){
  .sg{grid-template-columns:repeat(2,1fr)}
  .card-grid{grid-template-columns:repeat(2,1fr)}
  .cont{padding:10px}
  .cs-bar{padding:8px 10px}
}

/* ── Dark Mode ── */
@media(prefers-color-scheme:dark){
  :root {
    --bg: #0f172a;
    --card-bg: #1e293b;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --text-light: #718096;
    --border: #334155;
    --section-hd-bg: linear-gradient(135deg,#334155,#1e293b);
    --table-hd-bg: #334155;
    --table-hd-color: #cbd5e1;
    --co-hd-bg: linear-gradient(135deg,#2d3748,#1e293b);
  }
  body{background:var(--bg);color:var(--text)}
  .sec,.over,.co-card,.sc,.ref-section{background:var(--card-bg);box-shadow:0 2px 12px rgba(0,0,0,0.3)}
  .sec-hd{background:var(--section-hd-bg)}
  .si,.card-item{background:#334155;border-color:#475569}
  .si .sv,.si .v,.card-item .v{color:#f1f5f9}
  .ctable th{background:var(--table-hd-bg);color:var(--table-hd-color)}
  .ctable td{border-bottom-color:#334155;color:#cbd5e1}
  .ctable tr:hover{background:#0f172a}
  .ctable code{background:#334155;color:#60a5fa}
  .sec-desc,.over p,.over li{color:#94a3b8}
  .over h3{color:#f1f5f9}
  .sn{background:#334155;color:#94a3b8;border-color:#475569}
  .sn:hover{background:#475569;color:#f1f5f9}
  .co-hd{background:var(--co-hd-bg);border-bottom-color:#334155}
  .co-n{color:#f1f5f9}
  .co-c{background:#334155;color:#94a3b8}
  .co-t{background:#334155;color:#60a5fa}
  .il .il-t{color:#94a3b8}
  .co-card .sg .si{background:#2d3748}
  .dashboard-item{background:#1e293b;border-top-color:var(--accent,#667eea)}
  .dashboard-item .d-value{color:#f1f5f9}
  .dashboard-item .d-label{color:#718096}
  .co-news{background:#1e293b;border-color:#334155}
  .co-news-hd{color:#e2e8f0;border-bottom-color:#334155}
  .news-item{border-bottom-color:#1a202c}
  .news-item a{color:#60a5fa}
  .bt-red,.btl{background:rgba(220,38,38,0.15);color:#fca5a5}
  .bt-orange,.btm{background:rgba(234,88,12,0.15);color:#fdba74}
  .bt-yellow{background:rgba(202,138,4,0.15);color:#fde68a}
  .bt-green,.btg{background:rgba(22,163,74,0.15);color:#86efac}
  .tline li{color:#94a3b8}
  .flow-box{background:#334155}
  .bottleneck-tag.bt-red{background:rgba(220,38,38,0.15);color:#fca5a5}
  .bottleneck-tag.bt-orange{background:rgba(234,88,12,0.15);color:#fdba74}
  .bottleneck-tag.bt-yellow{background:rgba(202,138,4,0.15);color:#fde68a}
  .btd.bt-red{background:rgba(220,38,38,0.2)}
  .btd.bt-orange{background:rgba(234,88,12,0.2)}
  .btd.bt-yellow{background:rgba(202,138,4,0.2)}
}
"""

# ════════════════════════════════════════════════════════════════
# THEME PRESETS — consistent color schemes per chain
# ════════════════════════════════════════════════════════════════

THEMES = {
    "storage": {
        "from": "#0a1628",
        "mid": "#1a2a4a",
        "to": "#0a1628",
        "accent": "#3182ce",
        "name": "存储产业链",
    },
    "semiconductor": {
        "from": "#0f0c29",
        "mid": "#302b63",
        "to": "#24243e",
        "accent": "#667eea",
        "name": "半导体产业链",
    },
    "new-energy-vehicle": {
        "from": "#0a2e1a",
        "mid": "#1a4a2a",
        "to": "#0a2e1a",
        "accent": "#38a169",
        "name": "新能源汽车产业链",
    },
    "ai-computing": {
        "from": "#1a0a2e",
        "mid": "#3a1a5e",
        "to": "#1a0a2e",
        "accent": "#8b5cf6",
        "name": "AI算力产业链",
    },
    "glass_substrate": {
        "from": "#0f0c29",
        "mid": "#302b63",
        "to": "#24243e",
        "accent": "#667eea",
        "name": "玻璃基板与激光产业链",
    },
    "pcb": {
        "from": "#0a1628",
        "mid": "#1a2a4a",
        "to": "#0a1628",
        "accent": "#3182ce",
        "name": "PCB产业链",
    },
    "laser": {
        "from": "#1a0a2e",
        "mid": "#302b63",
        "to": "#0f3460",
        "accent": "#e94560",
        "name": "激光产业链",
    },
}


def theme_css(theme: dict) -> str:
    """Generate :root CSS variable overrides from a theme dict."""
    return f""":root{{
  --primary-from:{theme['from']};
  --primary-mid:{theme['mid']};
  --primary-to:{theme['to']};
  --accent:{theme['accent']};
  --co-link:{theme['accent']};
}}"""


# ════════════════════════════════════════════════════════════════
# COMMON JS SNIPPETS
# ════════════════════════════════════════════════════════════════

TAB_SWITCH_JS = """
function switchTab(tab) {
  var tabs = document.querySelectorAll('.tab-content');
  tabs.forEach(function(el){ el.classList.remove('active'); });
  var navs = document.querySelectorAll('.seg-nav .sn, .top-nav .tab');
  navs.forEach(function(el){
    el.style.background=''; el.style.color=''; el.style.fontWeight='';
  });
  var tc = document.getElementById('tab-' + tab);
  if(tc) tc.classList.add('active');
  var na = document.getElementById('nav-' + tab);
  if(na) { na.style.background='{accent}'; na.style.color='#fff'; na.style.fontWeight='600'; }
  setTimeout(function(){
    document.querySelectorAll('.chart-box').forEach(function(cb){
      var ch = echarts.getInstanceByDom(cb);
      if(ch) ch.resize();
    });
  }, 200);
}
"""

STOCK_SWITCH_JS = """
var _coCodes = [{codes}];
function switchTab(tab) {
  if(_coCodes.indexOf(tab) !== -1) { switchToStock(tab); return; }
  document.querySelectorAll('.tab-content').forEach(function(el){ el.classList.remove('active'); });
  document.querySelectorAll('.sn').forEach(function(el){ el.style.background=''; el.style.color=''; el.style.fontWeight=''; });
  var tc = document.getElementById('tab-' + tab);
  if(tc) tc.classList.add('active');
  var na = document.getElementById('nav-' + tab);
  if(na) { na.style.background='{accent}'; na.style.color='#fff'; na.style.fontWeight='600'; }
  if(tab === 'overview') {
    _coCodes.forEach(function(c){
      var el = document.getElementById('co_' + c);
      if(el) el.style.display = '';
    });
  }
  setTimeout(function(){
    document.querySelectorAll('.chart-box').forEach(function(cb){
      var ch = echarts.getInstanceByDom(cb);
      if(ch) ch.resize();
    });
  }, 200);
}
function switchToStock(code) {
  document.querySelectorAll('.tab-content').forEach(function(el){ el.classList.remove('active'); });
  document.querySelectorAll('.sn').forEach(function(el){ el.style.background=''; el.style.color=''; el.style.fontWeight=''; });
  document.getElementById('tab-stocks').classList.add('active');
  var na = document.getElementById('nav-stocks');
  if(na) { na.style.background='{accent}'; na.style.color='#fff'; na.style.fontWeight='600'; }
  _coCodes.forEach(function(c){
    var el = document.getElementById('co_' + c);
    if(el) el.style.display = c === code ? '' : 'none';
  });
  setTimeout(function(){
    var el = document.getElementById('co_' + code);
    if(el) {
      el.scrollIntoView({behavior:'smooth', block:'start'});
      el.querySelectorAll('.chart-box').forEach(function(cb){
        var ch = echarts.getInstanceByDom(cb);
        if(ch) ch.resize();
      });
    }
  }, 200);
}
"""


# ════════════════════════════════════════════════════════════════
# COMMON HTML GENERATORS
# ════════════════════════════════════════════════════════════════

def generate_header(
    title: str,
    subtitle: str,
    meta: str = "",
    theme: Optional[dict] = None,
    chain_selector: str = "",
) -> str:
    """Generate standard page header."""
    return f"""<div class="header">
    <h1>{title}</h1>
    <div class="sub">{subtitle}</div>
    <div class="dt">📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} | {meta}</div>
    {chain_selector}
</div>"""


def generate_footer(extra: str = "") -> str:
    """Generate standard footer."""
    return f"""<div class="ft">
    ⚠️ 本报告基于公开数据自动生成，仅供研究参考，不构成投资建议。<br>
    数据来源: 公司公告, 行业研报, 实时行情 ｜ 报告生成: chain-analysis skill<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M')}
    {extra}
</div>"""


def generate_tab_nav(items: list, active: str = "overview", accent: str = "#667eea") -> str:
    """Generate tab navigation bar.
    items: list of (id, label, icon) tuples
    """
    links = ""
    for tid, label, icon in items:
        a = " active" if tid == active else ""
        bg = f"background:{accent};color:#fff;font-weight:600" if tid == active else ""
        links += f'<a href="javascript:void(0)" onclick="switchTab(\'{tid}\')" class="sn{a}" id="nav-{tid}" style="{bg}">{icon} {label}</a>\n    '
    return f'<div class="seg-nav" style="margin-bottom:10px">{links}</div>'


def generate_stock_subnav(companies: list, accent: str = "#667eea") -> str:
    """Generate stock sub-navigation for switching stock cards."""
    items = ""
    for co in companies:
        items += f'<a href="javascript:void(0)" onclick="switchTab(\'{co["code"]}\')" class="sn">{co["name"]}</a>\n      '
    return f'<div class="stock-subnav">{items}</div>'
