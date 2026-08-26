#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小K 投資儀表板 — 數據抓取（精簡快速版）"""
import json, time, subprocess, sys

UA = "Mozilla/5.0"
COOKIE = "/tmp/ycookie.txt"
OUT = "/Users/user/my-work/market_data.json"

def curl(url, cookie=False):
    cmd = ["curl", "-s", "--max-time", "15", "-A", UA]
    if cookie:
        cmd += ["-b", COOKIE]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

def get_crumb():
    subprocess.run(["curl", "-s", "-c", COOKIE, "-A", UA, "https://fc.yahoo.com", "-o", "/dev/null"], capture_output=True)
    time.sleep(0.5)
    c = curl("https://query1.finance.yahoo.com/v1/test/getcrumb", cookie=True)
    return c if c and "Too Many" not in c and len(c) > 3 else ""

def chart(sym):
    d = json.loads(curl(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d"))
    m = d["chart"]["result"][0]["meta"]
    return {
        "price": m.get("regularMarketPrice"),
        "prevClose": m.get("chartPreviousClose") or m.get("previousClose"),
        "high52": m.get("fiftyTwoWeekHigh"),
        "low52": m.get("fiftyTwoWeekLow"),
        "currency": m.get("currency"),
    }

def summary(sym, crumb):
    if not crumb:
        return {}
    mods = "summaryDetail,financialData,defaultKeyStatistics"
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}?modules={mods}&crumb={crumb}"
    txt = curl(url, cookie=True)
    if not txt:
        return {}
    try:
        r = json.loads(txt)["quoteSummary"]["result"][0]
    except Exception:
        return {}
    fd = r.get("financialData", {}); ks = r.get("defaultKeyStatistics", {}); sd = r.get("summaryDetail", {})
    def raw(o, k):
        v = o.get(k)
        return v.get("raw") if isinstance(v, dict) and "raw" in v else v
    return {
        "revenueGrowth": raw(fd, "revenueGrowth"), "grossMargins": raw(fd, "grossMargins"),
        "profitMargins": raw(fd, "profitMargins"), "operatingMargins": raw(fd, "operatingMargins"),
        "targetMean": raw(fd, "targetMeanPrice"), "targetHigh": raw(fd, "targetHighPrice"), "targetLow": raw(fd, "targetLowPrice"),
        "recommendation": raw(fd, "recommendationKey"), "trailingPE": raw(ks, "trailingPE"),
        "forwardPE": raw(ks, "forwardPE"), "pegRatio": raw(ks, "pegRatio"),
        "psTrailing": raw(ks, "priceToSalesTrailing12Months"), "revQuarterlyGrowth": raw(ks, "revenueQuarterlyGrowth"),
        "earningsQuarterlyGrowth": raw(ks, "earningsQuarterlyGrowth"), "marketCap": raw(sd, "marketCap"),
        "beta": raw(sd, "beta"), "dividendYield": raw(sd, "dividendYield"),
    }

def pos52(price, low, high):
    if not price or not low or not high or high == low:
        return None
    return round((price - low) / (high - low) * 100, 1)

def main():
    crumb = get_crumb()
    print(f"crumb={'OK' if crumb else 'FAIL'}", file=sys.stderr)

    macro_syms = {
        "^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "道瓊",
        "^TWII": "台灣加權", "^VIX": "VIX恐慌指數",
        "^TNX": "美10年債殖利率", "^TYX": "美30年債殖利率", "^FVX": "美5年債殖利率",
        "GC=F": "黃金", "CL=F": "WTI原油", "DX-Y.NYB": "美元指數",
    }
    macro = {}
    for sym, label in macro_syms.items():
        try:
            m = chart(sym); m["label"] = label; m["pos52"] = pos52(m["price"], m["low52"], m["high52"])
            macro[sym] = m
        except Exception as e:
            macro[sym] = {"label": label, "error": str(e)[:60]}
        time.sleep(1.0)

    stocks = {}
    tickers = [
        ("NVDA","NVIDIA 輝達","AI半導體"),("TSM","台積電 ADR","AI半導體"),("MU","美光","AI半導體/記憶體"),
        ("AMD","AMD","AI半導體"),("ASML","ASML","AI半導體/設備"),("AVGO","博通","AI半導體"),
        ("MSFT","微軟","Mega Tech"),("GOOGL","谷歌","Mega Tech"),("AMZN","亞馬遜","Mega Tech"),("META","Meta","Mega Tech"),
        ("GEV","GE Vernova","資料中心/電力"),("ETN","伊頓 Eaton","資料中心/電力"),("VST","Vistra","資料中心/電力"),("EQIX","Equinix","資料中心/REIT"),
        ("2330.TW","台積電","核心台股"),("2317.TW","鴻海","核心台股"),("2337.TW","旺宏","核心台股/記憶體"),
        ("4772.TWO","台特化","核心台股"),("3689.TWO","湧德","核心台股"),("1815.TWO","富喬","核心台股"),("3042.TW","晶技","核心台股"),
        ("0050.TW","元大台灣50","ETF"),("VOO","Vanguard S&P500","ETF"),("QQQ","Invesco QQQ","ETF"),
        ("00933B.TWO","國泰金融債","債券ETF"),("00937B.TWO","群益ESG投等債","債券ETF"),("00945B.TW","凱基非投等債","債券ETF"),("00953B.TW","群益非投等債","債券ETF"),
    ]
    for sym, label, grp in tickers:
        rec = {"label": label, "group": grp}
        try:
            m = chart(sym); m["pos52"] = pos52(m["price"], m["low52"], m["high52"]); rec.update(m)
        except Exception as e:
            rec["error"] = str(e)[:60]
        try:
            rec["fund"] = summary(sym, crumb)
        except Exception:
            rec["fund"] = {}
        stocks[sym] = rec
        time.sleep(1.0)

    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "macro": macro, "stocks": stocks}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n完成！存至 {OUT}", file=sys.stderr)
    for sym, m in macro.items():
        if "price" in m:
            print(f"MACRO {sym}: {m['price']} pos52={m.get('pos52')}")
    for sym, s in stocks.items():
        f = s.get("fund", {})
        print(f"STOCK {sym}: px={s.get('price')} pos52={s.get('pos52')} fPE={f.get('forwardPE')} tPE={f.get('trailingPE')} revG={f.get('revenueGrowth')} GM={f.get('grossMargins')} NM={f.get('profitMargins')}")

if __name__ == "__main__":
    main()
