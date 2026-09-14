#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小K 投資週報生成腳本 — 從 market_data.json 生成單週報告 HTML"""
import json, datetime, os

BASE = "/Users/user/my-work"
DATA = json.load(open(f"{BASE}/market_data.json"))
MACRO = DATA["macro"]
STOCKS = DATA["stocks"]
GEN = DATA["generated_at"]

# 日期與週數
today = datetime.date.today()
year, week, _ = today.isocalendar()
date_str = today.strftime("%Y%m%d")
display_date = today.strftime("%Y/%m/%d")

def fnum(v, d=2):
    return "—" if v is None else f"{v:,.{d}f}"

def fpct(v):
    if v is None or not isinstance(v, (int, float)):
        return "—"
    return f"{v*100:+.1f}%"

def water(pos):
    if pos is None: return "—"
    return "🔴" if pos >= 70 else ("🟢" if pos <= 35 else "🟡")

def water_txt(pos):
    if pos is None: return "無數據"
    return "高位" if pos >= 70 else ("低位" if pos <= 35 else "中位")

# 總經
macro_items = [
    ("^TWII", "台股加權", "TWD", ""),
    ("^GSPC", "S&P 500", "USD", ""),
    ("^IXIC", "Nasdaq", "USD", ""),
    ("^VIX", "VIX恐慌", "USD", ""),
    ("^TNX", "10年債殖利率", "USD", "%"),
    ("^TYX", "30年債殖利率", "USD", "%"),
    ("GC=F", "黃金", "USD", ""),
]
macro_cards = ""
for sym, label, cur, unit in macro_items:
    m = MACRO.get(sym, {})
    p = m.get("price"); pos = m.get("pos52")
    val = f"{p:.2f}{unit}" if isinstance(p, float) and unit == "%" else fnum(p)
    macro_cards += f'''<div class="mcard">
  <div class="mlabel">{label}</div>
  <div class="mval">{val}</div>
  <div class="mpos">{water(pos)} {water_txt(pos)} · 水位 {pos if pos is not None else '—'}%</div>
</div>'''

# 標的分組 + 找出高低位
groups = {
    "AI半導體": ["NVDA","TSM","MU","AMD","ASML","AVGO"],
    "Mega Tech": ["MSFT","GOOGL","AMZN","META"],
    "資料中心/電力": ["GEV","ETN","VST","EQIX"],
    "核心台股": ["2330.TW","2317.TW","2337.TW","4772.TWO","3689.TWO","1815.TWO"],
    "ETF": ["0050.TW","009816.TW","VOO","QQQ","00933B.TWO","00937B.TWO","00945B.TW","00953B.TW"],
}

# 低位（機會）與高位（風險）
all_stocks = []
for g, syms in groups.items():
    for s in syms:
        st = STOCKS.get(s, {})
        f = st.get("fund", {})
        pos = st.get("pos52")
        fpe = f.get("forwardPE")
        g_ = f.get("revenueGrowth")
        all_stocks.append({
            "sym": s, "label": st.get("label", s), "price": st.get("price"),
            "pos": pos, "fpe": fpe, "revg": g_, "group": g,
        })

low_stocks = [s for s in all_stocks if s["pos"] is not None and s["pos"] <= 35]
high_stocks = [s for s in all_stocks if s["pos"] is not None and s["pos"] >= 85]
low_stocks.sort(key=lambda x: x["pos"])
high_stocks.sort(key=lambda x: -x["pos"])

def stock_row(s):
    pe = f"{s['fpe']:.1f}" if isinstance(s["fpe"], (int, float)) else "—"
    rg = fpct(s["revg"])
    return f"<tr><td>{water(s['pos'])} {s['label']}</td><td>{s['sym']}</td><td>{fnum(s['price'])}</td><td>{s['pos']}%</td><td>{pe}</td><td>{rg}</td></tr>"

low_rows = "".join(stock_row(s) for s in low_stocks[:6])
high_rows = "".join(stock_row(s) for s in high_stocks[:6])

# 質押安全（靜態，來自設定）
pledge_info = "成數 2.9%（目標 &lt;40%）· 遠低於警戒線 · 維持率安全"

HTML = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>投資週報 {year} 第{week}週 · 小K書房</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,'PingFang TC','Noto Sans TC',sans-serif; background:#fff; color:#1a1a1a; line-height:1.8; padding:0 0 40px; -webkit-font-smoothing:antialiased; }}
  .hero {{ text-align:center; padding:48px 20px 28px; border-bottom:1px solid #eee; }}
  .hero .badge {{ display:inline-block; background:#eef2ff; color:#4f46e5; font-size:12px; font-weight:700; padding:4px 14px; border-radius:20px; margin-bottom:14px; letter-spacing:2px; }}
  .hero h1 {{ font-size:26px; font-weight:900; }}
  .hero .sub {{ color:#6b7280; font-size:14px; margin-top:8px; }}
  .content {{ max-width:760px; margin:0 auto; padding:24px 18px; }}
  .sec {{ margin:28px 0 14px; font-size:18px; font-weight:800; display:flex; align-items:center; gap:8px; }}
  .sec .bar {{ width:4px; height:18px; background:#4f46e5; border-radius:2px; }}
  .mgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }}
  .mcard {{ border:1px solid #e5e7eb; border-radius:10px; padding:12px 14px; }}
  .mlabel {{ font-size:12px; color:#6b7280; font-weight:700; }}
  .mval {{ font-size:20px; font-weight:800; margin:2px 0; }}
  .mpos {{ font-size:11px; color:#6b7280; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }}
  th,td {{ padding:8px 10px; text-align:left; border-bottom:1px solid #f0f0f0; }}
  th {{ color:#6b7280; font-weight:700; background:#fafafa; }}
  .note {{ background:#f9fafb; border:1px solid #eee; border-radius:10px; padding:14px 16px; margin-top:12px; font-size:14px; color:#374151; }}
  .footer {{ text-align:center; color:#9ca3af; font-size:12px; padding:30px 20px 0; }}
  .back {{ display:block; text-align:center; margin:20px auto 0; padding:10px; border-radius:10px; background:#f3f4f6; color:#374151; font-size:13px; text-decoration:none; max-width:200px; }}
  .hold {{ font-size:10px; color:#b45309; font-weight:700; background:#fef3c7; padding:1px 6px; border-radius:6px; margin-left:4px; }}
</style>
</head>
<body>
<div class="hero">
  <div class="badge">WEEKLY REPORT · 投資週報</div>
  <h1>{year} 年第 {week} 週投資週報</h1>
  <div class="sub">📅 {display_date} · 數據快照：{GEN}</div>
</div>

<div class="content">
  <div class="sec"><span class="bar"></span>🌍 總經水位</div>
  <div class="mgrid">{macro_cards}</div>

  <div class="sec"><span class="bar"></span>🟢 低位／機會（安全邊際）</div>
  <table><thead><tr><th>標的</th><th>代號</th><th>現價</th><th>水位</th><th>本益比</th><th>營收年增</th></tr></thead>
  <tbody>{low_rows}</tbody></table>

  <div class="sec"><span class="bar"></span>🔴 高位／追高風險</div>
  <table><thead><tr><th>標的</th><th>代號</th><th>現價</th><th>水位</th><th>本益比</th><th>營收年增</th></tr></thead>
  <tbody>{high_rows}</tbody></table>

  <div class="sec"><span class="bar"></span>🏦 質押安全</div>
  <div class="note">{pledge_info}</div>

  <div class="sec"><span class="bar"></span>📌 下週焦點</div>
  <div class="note">
    • 追蹤 10 年債殖利率是否續創新高（債券長天期加碼訊號）<br>
    • 觀察 VIX 是否脫離極低檔（市場平靜過久的反轉風險）<br>
    • 台股高位標的（台積電/富喬）是否出現拉回，留意安全邊際
  </div>

  <div class="footer">小K書房 · 投資週報 · 每週一自動更新</div>
  <a class="back" href="library.html">← 回小K書房</a>
</div>
</body>
</html>'''

out_path = f"{BASE}/investment-weekly-{date_str}.html"
open(out_path, "w", encoding="utf-8").write(HTML)
print(f"已生成 {out_path} ({len(HTML)} 字元)")
print(f"低位標的數：{len(low_stocks)}，高位標的數：{len(high_stocks)}")

# ---- 更新小K書房首頁（library.html）----
LIB = "/Users/user/lee-yung-tools/library.html"
try:
    lib = open(LIB, encoding="utf-8").read()
    marker = "<!-- 投資週報 -->"
    if marker in lib:
        # 遞增計數
        import re
        def inc_count(m):
            return f'📅 投資週報 <span class="count">{int(m.group(1)) + 1}</span>'
        lib = re.sub(r'📅 投資週報 <span class="count">(\d+)</span>', inc_count, lib)
        # 插入新卡片（在 cat-title 之後）
        card = f'''<a class="book-card" href="investment-weekly-{date_str}.html">
      <div class="cover cover-12">📅</div>
      <div class="info">
        <div class="title">投資週報 · {year} 第{week}週</div>
        <div class="desc">每週總經水位 · 標的估值 · 質押安全 · 決策焦點</div>
      </div>
      <div class="arrow">›</div>
    </a>
'''
        # 找到投資週報分類的 cat-title 行，在其後插入卡片
        cat_pattern = r'(📅 投資週報 <span class="count">\d+</span></div>\n)'
        lib = re.sub(cat_pattern, r'\1\n' + card, lib, count=1)
        open(LIB, "w", encoding="utf-8").write(lib)
        print(f"已更新 {LIB}")
    else:
        print("⚠️ 找不到「投資週報」分類標記，跳過 library.html 更新")
except Exception as e:
    print(f"⚠️ library.html 更新失敗：{e}")
