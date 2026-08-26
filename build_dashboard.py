#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小K 投資儀表板 — 從 market_data.json 生成 HTML"""
import json, html

DATA = json.load(open("/Users/user/my-work/market_data.json"))
MACRO = DATA["macro"]
STOCKS = DATA["stocks"]
GEN = DATA["generated_at"]

# 板塊分組與本益比合理區間
GROUPS = [
    ("🥇 AI 半導體 / 記憶體 / 設備", "g1", "sky",
     ["NVDA","TSM","MU","AMD","ASML","AVGO"], (18, 28)),
    ("🥈 Mega Tech / Cloud / AI 平台", "g2", "purple",
     ["MSFT","GOOGL","AMZN","META"], (18, 26)),
    ("🥉 AI 資料中心 / 電力 / 基礎建設", "g3", "green",
     ["GEV","ETN","VST","EQIX"], (18, 28)),
    ("🇹🇼 核心台股", "g4", "red",
     ["2330.TW","2317.TW","2337.TW"], (15, 25)),
]
HOLDINGS = {"NVDA","2330.TW","2317.TW","2337.TW","MU","GOOGL","TSM"}

def fnum(v, d=2):
    if v is None: return "—"
    if isinstance(v, float):
        return f"{v:,.{d}f}"
    return str(v)

def fpct(v):
    if v is None: return "—"
    return f"{v*100:+.1f}%"

def fmt_pe(v):
    if v is None: return "—"
    return f"{v:.1f}"

def pct_str(v):
    if v is None: return "—"
    return f"{v:.0f}%"

def water_light(pos):
    """價格水位燈號"""
    if pos is None: return ("—", "gray", "無數據")
    if pos >= 70: return ("🔴", "high", "高位")
    if pos <= 35: return ("🟢", "low", "低位")
    return ("🟡", "mid", "中位")

def val_light(fpe, low, high):
    """估值燈號（前瞻本益比 vs 板塊合理區間）"""
    if fpe is None: return ("—", "gray", "無數據")
    if fpe < low: return ("🟢", "cheap", "偏低")
    if fpe <= high: return ("🟡", "fair", "合理")
    return ("🔴", "rich", "偏高")

def growth_light(g):
    if g is None: return ("—", "gray", "無數據")
    if g >= 0.30: return ("🟢", "strong", "強勁")
    if g >= 0.10: return ("🟡", "ok", "穩健")
    if g >= 0: return ("🟠", "weak", "平緩")
    return ("🔴", "neg", "衰退")

def advice(pos, fpe, g, low, high, sym):
    """綜合建議"""
    wl = water_light(pos)[1]
    vl = val_light(fpe, low, high)[1]
    gl = growth_light(g)[1]
    # 週期股特殊處理（低PE可能是景氣頂部警訊）
    if sym in ("MU","2337.TW"):
        if pos is not None and pos >= 70:
            return "🔴 高位＋週期股，低PE非便宜而是景氣疑慮，分批停利、嚴設停損"
        return "🟡 週期股低PE需辯證看待，追蹤報價/庫存，景氣反轉前退場"
    if sym == "EQIX":
        return "🟡 REIT 高P/E屬重資產特性，改看殖利率與租金成長，利率見頂才加碼"
    if sym == "2317.TW":
        return "🟢 代工低PE常態，看AI伺服器訂單與毛利變化，拉回分批"
    if gl == "neg":
        return "🔴 營收衰退，先觀望基本面是否落底，暫不進場"
    if wl == "high" and vl == "rich":
        return "🔴 高位＋偏貴，追高風險大，等待拉回"
    if wl == "high" and vl == "fair":
        return "🟡 高位但估值尚合理，持有不追高"
    if wl == "low" and vl == "cheap":
        return "🟢 低位＋低估，安全邊際浮現，可分批低接"
    if wl == "low" and vl == "fair":
        return "🟡 低位但估值中性，確認基本面後再進"
    if vl == "cheap":
        return "🟢 估值偏低，具安全邊際，拉回承接"
    return "🟡 中性，等待更好價位或催化劑"

# ---- 生成 HTML ----
def macro_card(sym, m, kind):
    label = m["label"]
    price = m.get("price")
    pos = m.get("pos52")
    cur = m.get("currency","")
    # 依類型給解讀
    note = ""
    if sym == "^VIX":
        note = "低位＝市場平靜" if pos is not None and pos <= 40 else "警戒"
    elif sym in ("^TNX","^TYX","^FVX"):
        note = "殖利率高位＝債券承壓"
    elif sym == "GC=F":
        note = "避險需求"
    elif sym == "^TWII":
        note = "台股水位"
    val = fnum(price)
    if sym in ("^TNX","^TYX","^FVX") and price:
        val = f"{price:.2f}%"
    pos_txt = pct_str(pos)
    light, _, wtxt = water_light(pos)
    return f'''<div class="mcard {kind}">
  <div class="mlabel">{label}</div>
  <div class="mval">{val}</div>
  <div class="mpos"><span class="light {light}">{light}</span> 52週水位 {pos_txt} · {wtxt}</div>
  <div class="mnote">{note}</div>
</div>'''

macro_html = ""
# 分組：股市指數
idx_syms = ["^GSPC","^IXIC","^DJI","^TWII"]
risk_syms = ["^VIX"]
bond_syms = ["^TNX","^TYX","^FVX"]
comm_syms = ["GC=F","CL=F","DX-Y.NYB"]

def group_section(title, syms, kind):
    cards = "".join(macro_card(s, MACRO.get(s,{"label":s}), kind) for s in syms if s in MACRO)
    return f'<div class="msub"><div class="msub-title">{title}</div><div class="mgrid">{cards}</div></div>' if cards else ""

macro_html += group_section("股市指數", idx_syms, "idx")
macro_html += group_section("波動率", risk_syms, "risk")
macro_html += group_section("債券殖利率", bond_syms, "bond")
macro_html += group_section("商品 / 匯率", comm_syms, "comm")

# ---- 標的表格 ----
stock_rows = ""
for gtitle, gcls, gcolor, syms, (lo, hi) in GROUPS:
    cards = ""
    for sym in syms:
        s = STOCKS.get(sym, {})
        f = s.get("fund", {})
        price = s.get("price"); pos = s.get("pos52")
        fpe = f.get("forwardPE"); g = f.get("revenueGrowth")
        gm = f.get("grossMargins"); nm = f.get("profitMargins")
        target = f.get("targetMean"); mcap = f.get("marketCap")
        wl, wcls, wtxt = water_light(pos)
        vl, vcls, vtxt = val_light(fpe, lo, hi)
        gl, gcls, gtxt = growth_light(g)
        adv = advice(pos, fpe, g, lo, hi, sym)
        hold = '<span class="hold">★持有</span>' if sym in HOLDINGS else ""
        cur = s.get("currency","")
        # 目標價空間
        upside = ""
        if price and target:
            u = (target - price) / price * 100
            upside = f'<span class="up{"pos" if u>=0 else "neg"}">目標 {fnum(target)}（{"+" if u>=0 else ""}{u:.0f}%）</span>'
        mcap_txt = ""
        if mcap:
            mcap_txt = f"{mcap/1e8:.0f}億{cur}"
        cards += f'''<div class="scard">
  <div class="shead"><span class="sname">{s.get("label",sym)}</span><span class="scode">{sym}</span>{hold}<span class="stag">{s.get("group","")}</span></div>
  <div class="price-row"><span class="price">{fnum(price)} <i>{cur}</i></span>{upside}</div>
  <div class="lights">
    <span class="chip {wcls}">水位 {wl} {wtxt} ({pct_str(pos)})</span>
    <span class="chip {vcls}">估值 {vl} 本益比 {fmt_pe(fpe)}</span>
    <span class="chip {gcls}">成長 {gl} {fpct(g)}</span>
  </div>
  <div class="fund">
    <span>毛利率 <b>{fpct(gm)}</b></span>
    <span>淨利率 <b>{fpct(nm)}</b></span>
    <span>市值 <b>{mcap_txt}</b></span>
  </div>
  <div class="advice">{adv}</div>
</div>'''
    stock_rows += f'<div class="group {gcls}"><div class="group-title">{gtitle}</div>{cards}</div>'

# ---- 同業比較摘要 ----
peer_rows = ""
for gtitle, gcls, gcolor, syms, (lo, hi) in GROUPS:
    rows = ""
    for sym in syms:
        s = STOCKS.get(sym, {}); f = s.get("fund", {})
        fpe = f.get("forwardPE"); g = f.get("revenueGrowth"); gm = f.get("grossMargins"); nm = f.get("profitMargins")
        rows += f"<tr><td>{s.get('label',sym)}</td><td>{sym}</td><td>{fmt_pe(fpe)}</td><td>{fpct(g)}</td><td>{fpct(gm)}</td><td>{fpct(nm)}</td></tr>"
    peer_rows += f'<tr class="phead"><td colspan="6">{gtitle}</td></tr>{rows}'

HTML_DOC = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0b0e14">
<title>投資儀表板 · 估值評判與總經水位</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
  body {{ font-family:-apple-system,'PingFang TC','Noto Sans TC',sans-serif; background:#0b0e14; color:#dfe6f0; font-size:16px; line-height:1.8; -webkit-font-smoothing:antialiased; padding-bottom:env(safe-area-inset-bottom); }}
  .hero {{ background:radial-gradient(ellipse at 50% -20%, #12264d 0%, #0b0e14 65%); padding:calc(env(safe-area-inset-top)+66px) 24px 40px; text-align:center; border-bottom:1px solid rgba(94,174,255,.12); }}
  .hero .icon {{ font-size:44px; display:block; margin-bottom:10px; }}
  .hero .badge {{ display:inline-block; background:rgba(56,189,248,.1); color:#38bdf8; font-size:11px; font-weight:700; padding:4px 14px; border-radius:20px; border:1px solid rgba(56,189,248,.2); margin-bottom:12px; letter-spacing:2px; }}
  .hero h1 {{ font-size:24px; font-weight:900; letter-spacing:-.5px; }}
  .hero h1 span {{ background:linear-gradient(135deg,#fff,#38bdf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
  .hero .sub {{ color:#7c8ba3; font-size:13px; margin-top:10px; }}
  .hero .upd {{ color:#55627a; font-size:12px; margin-top:8px; }}
  .content {{ max-width:720px; margin:0 auto; padding:26px 18px 60px; }}
  .disclaimer {{ background:rgba(248,113,113,.06); border:1px solid rgba(248,113,113,.2); border-radius:12px; padding:12px 14px; margin-bottom:24px; font-size:12.5px; color:#fca5a5; }}
  .sec-title {{ font-size:19px; font-weight:900; color:#fff; margin:30px 0 14px; display:flex; align-items:center; gap:8px; }}
  .sec-title .bar {{ width:4px; height:20px; background:linear-gradient(#38bdf8,#818cf8); border-radius:2px; }}
  /* 總經 */
  .msub-title {{ font-size:13px; font-weight:800; color:#7dd3fc; margin:16px 0 8px; letter-spacing:1px; }}
  .mgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }}
  .mcard {{ background:#101623; border:1px solid rgba(255,255,255,.06); border-radius:12px; padding:12px 14px; }}
  .mlabel {{ font-size:12px; color:#7c8ba3; font-weight:700; }}
  .mval {{ font-size:22px; font-weight:900; color:#fff; margin:4px 0; }}
  .mpos {{ font-size:11px; color:#9fb0c8; }}
  .mnote {{ font-size:10.5px; color:#55627a; margin-top:4px; }}
  .light.high,.light.rich,.light.neg {{ color:#f87171; }}
  .light.low,.light.cheap,.light.strong {{ color:#4ade80; }}
  .light.mid,.light.fair,.light.ok {{ color:#fbbf24; }}
  .light.weak {{ color:#fb923c; }}
  .light.gray {{ color:#64748b; }}
  /* 標的 */
  .group {{ margin-bottom:26px; }}
  .group-title {{ font-size:15px; font-weight:800; color:#fff; padding:10px 14px; margin-bottom:10px; border-left:4px solid #38bdf8; background:rgba(56,189,248,.06); border-radius:0 10px 10px 0; }}
  .g1 .group-title {{ border-left-color:#fbbf24; background:rgba(251,191,36,.06); }}
  .g2 .group-title {{ border-left-color:#a78bfa; background:rgba(167,139,250,.06); }}
  .g3 .group-title {{ border-left-color:#4ade80; background:rgba(74,222,128,.06); }}
  .g4 .group-title {{ border-left-color:#f87171; background:rgba(248,113,113,.06); }}
  .scard {{ background:#101623; border:1px solid rgba(255,255,255,.06); border-radius:14px; padding:15px 16px; margin-bottom:10px; }}
  .shead {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:8px; }}
  .sname {{ font-size:16px; font-weight:800; color:#fff; }}
  .scode {{ font-size:11px; color:#7dd3fc; font-weight:700; background:rgba(56,189,248,.08); padding:2px 8px; border-radius:8px; }}
  .stag {{ font-size:10.5px; color:#64748b; margin-left:auto; }}
  .hold {{ font-size:10px; color:#fbbf24; font-weight:800; background:rgba(251,191,36,.1); padding:2px 8px; border-radius:8px; border:1px solid rgba(251,191,36,.2); }}
  .price-row {{ display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:10px; }}
  .price {{ font-size:22px; font-weight:900; color:#fff; }}
  .price i {{ font-size:12px; font-style:normal; color:#7c8ba3; }}
  .up.pos {{ color:#4ade80; font-size:12px; }}
  .up.neg {{ color:#f87171; font-size:12px; }}
  .lights {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }}
  .chip {{ font-size:11px; padding:3px 9px; border-radius:8px; border:1px solid rgba(255,255,255,.08); }}
  .chip.high,.chip.rich,.chip.neg {{ background:rgba(248,113,113,.1); color:#fca5a5; }}
  .chip.low,.chip.cheap,.chip.strong {{ background:rgba(74,222,128,.1); color:#86efac; }}
  .chip.mid,.chip.fair,.chip.ok {{ background:rgba(251,191,36,.1); color:#fcd34d; }}
  .chip.weak {{ background:rgba(251,146,60,.1); color:#fdba74; }}
  .chip.gray {{ background:rgba(100,116,139,.1); color:#94a3b8; }}
  .fund {{ display:flex; gap:14px; flex-wrap:wrap; font-size:12px; color:#9fb0c8; margin-bottom:10px; }}
  .fund b {{ color:#dfe6f0; }}
  .advice {{ font-size:13px; color:#c2cbd9; border-top:1px dashed rgba(255,255,255,.07); padding-top:10px; }}
  /* 同業比較表 */
  table {{ width:100%; border-collapse:collapse; font-size:12px; margin-bottom:20px; }}
  th,td {{ padding:8px 6px; text-align:left; border-bottom:1px solid rgba(255,255,255,.05); }}
  th {{ color:#7c8ba3; font-weight:700; }}
  td {{ color:#c2cbd9; }}
  .phead td {{ color:#fff; font-weight:800; background:rgba(56,189,248,.05); }}
  /* 方法論 */
  .method {{ background:#101623; border:1px solid rgba(255,255,255,.06); border-radius:14px; padding:16px 18px; margin-bottom:12px; }}
  .method h4 {{ font-size:14px; font-weight:800; color:#7dd3fc; margin-bottom:8px; }}
  .method p, .method li {{ font-size:13px; color:#c2cbd9; }}
  .method ul {{ padding-left:18px; }}
  .footer {{ text-align:center; padding:30px 20px 30px; color:#44536e; font-size:12px; }}
  .back-link {{ display:block; text-align:center; margin-top:14px; padding:12px; border-radius:12px; background:rgba(255,255,255,.03); color:#7c8ba3; font-size:13px; text-decoration:none; }}
  @media (prefers-color-scheme: light) {{
    body {{ background:#f5f7fb; color:#1d2333; }}
    .hero {{ background:radial-gradient(ellipse at 50% -20%,#dbe9ff 0%,#f5f7fb 65%); border-color:rgba(37,99,235,.12); }}
    .hero h1 {{ color:#1d2333; }}
    .hero h1 span {{ background:linear-gradient(135deg,#1d2333,#2563eb); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
    .hero .sub {{ color:#5a6478; }}
    .hero .upd {{ color:#8892a8; }}
    .disclaimer {{ background:rgba(220,38,38,.04); border-color:rgba(220,38,38,.2); color:#dc2626; }}
    .sec-title {{ color:#1d2333; }}
    .mcard,.scard,.method {{ background:#fff; border-color:rgba(0,0,0,.06); }}
    .mlabel {{ color:#6b7280; }}
    .mval {{ color:#1d2333; }}
    .mpos {{ color:#6b7280; }}
    .mnote {{ color:#8892a8; }}
    .group-title {{ color:#1d2333; background:rgba(37,99,235,.05); }}
    .sname {{ color:#1d2333; }}
    .price {{ color:#1d2333; }}
    .fund {{ color:#6b7280; }}
    .fund b {{ color:#1d2333; }}
    .advice {{ color:#3d4757; border-color:rgba(0,0,0,.05); }}
    th {{ color:#6b7280; }}
    td {{ color:#3d4757; }}
    .phead td {{ color:#1d2333; background:rgba(37,99,235,.04); }}
    .method h4 {{ color:#2563eb; }}
    .method p,.method li {{ color:#3d4757; }}
    .back-link {{ background:rgba(0,0,0,.03); color:#4a5468; }}
  }}
</style>
</head>
<body>
<div class="hero">
  <span class="icon">📊</span>
  <div class="badge">INVESTMENT DASHBOARD · 估值評判</div>
  <h1>投資儀表板<br><span>即時報價 · 水位 · 總經</span></h1>
  <div class="sub">17 檔核心標的 + 總經/債券/黃金 自動化評判</div>
  <div class="upd">🕐 最後更新：{GEN}</div>
</div>

<div class="content">
  <div class="disclaimer">⚠️ 本儀表板數據來自 Yahoo Finance 即時行情，燈號與建議為量化框架自動生成，非買賣建議。實際決策請搭配個人風險承受能力。</div>

  <div class="sec-title"><span class="bar"></span>🌍 總經儀表板</div>
  {macro_html}

  <div class="sec-title"><span class="bar"></span>🎯 標的估值評判</div>
  {stock_rows}

  <div class="sec-title"><span class="bar"></span>📋 同業比較總表</div>
  <table><thead><tr><th>標的</th><th>代號</th><th>前瞻本益比</th><th>營收年增</th><th>毛利率</th><th>淨利率</th></tr></thead><tbody>{peer_rows}</tbody></table>

  <div class="sec-title"><span class="bar"></span>🧭 評判方法論</div>
  <div class="method">
    <h4>① 水位燈號（價格位置）</h4>
    <p>用「現價 vs 52週高低點」算出百分位：<b>≥70% 高位</b>（追高風險）、<b>35~70% 中位</b>、<b>≤35% 低位</b>（安全邊際）。</p>
  </div>
  <div class="method">
    <h4>② 估值燈號（前瞻本益比 vs 板塊合理區間）</h4>
    <p>AI 半導體與電力設備因高成長可容忍較高本益比（合理 18~28x）；Mega Tech 合理 18~26x；台股 15~25x。<b>低於下限＝低估</b>、<b>高於上限＝偏高</b>。</p>
  </div>
  <div class="method">
    <h4>③ 基本面依據（營收 / 毛利率 / 淨利率）</h4>
    <ul>
      <li><b>營收年增率</b>：&gt;30% 強勁、10~30% 穩健、0~10% 平緩、&lt;0% 衰退。</li>
      <li><b>毛利率</b>：反映定價權與護城河，&gt;60% 為強護城河（如 NVDA、Meta、博通）。</li>
      <li><b>淨利率</b>：最終獲利能力，&gt;40% 為極佳（NVDA、谷歌、台積電）。</li>
      <li><b>月營收/季營收</b>：台股上市櫃每月公告月營收（需 TWSE 數據源），美股以季報為主。</li>
    </ul>
  </div>
  <div class="method">
    <h4>④ 週期股陷阱提醒</h4>
    <p>記憶體（美光、旺宏）出現<b>極低本益比 + 營收暴增</b>時，常是景氣頂部訊號（市場預期未來衰退）。低 PE 在此處<b>不是便宜，而是反轉警訊</b>，需搭配報價與庫存數據辯證看待。</p>
  </div>

  <div class="footer">小K書房 · 投資儀表板 · 數據由 Yahoo Finance 提供</div>
  <a class="back-link" href="library.html">← 回小K書房</a>
</div>
</body>
</html>'''

open("/Users/user/my-work/investment-dashboard.html","w",encoding="utf-8").write(HTML_DOC)
print("已生成 investment-dashboard.html，", len(HTML_DOC), "字元")
