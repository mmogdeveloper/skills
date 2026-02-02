import requests
import math
import datetime as dt
import os

# DCA daily report
# - Price source: Coinbase spot
# - Ahr999 primary: CoinGlass (manual/override if provided)
# - Ahr999 fallback: self-calculated (CoinGecko daily closes + fixed ExpPrice params)

# Self-calc (B) fixed params for ExpPrice
A_EXP = 5.84
B_EXP = -17.01
GENESIS = dt.date(2009, 1, 3)

# Empirical adjustment to align self-calc(B) with CoinGlass (based on observed ~8.4% lower)
# We scale CoinGlass thresholds down by ~0.915 when using self-calc.
ALIGN_RATIO = 0.915


def fetch_btc_spot_coinbase():
    r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10)
    r.raise_for_status()
    return float(r.json()["data"]["amount"])


def fetch_btc_daily_closes_coingecko(days: int = 240):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": str(days), "interval": "daily"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("prices", [])

    by_date = {}
    for ts_ms, price in data:
        d = dt.datetime.utcfromtimestamp(ts_ms / 1000).date()
        by_date[d] = float(price)

    closes = [by_date[d] for d in sorted(by_date.keys())]
    return closes


def gma(prices):
    s = 0.0
    n = 0
    for p in prices:
        if p and p > 0:
            s += math.log(p)
            n += 1
    return math.exp(s / n) if n else None


def exp_price(today: dt.date):
    days = (today - GENESIS).days
    return 10 ** (A_EXP * math.log10(days) + B_EXP)


def ahr999_selfcalc():
    today = dt.datetime.utcnow().date()
    closes = fetch_btc_daily_closes_coingecko(240)
    if len(closes) < 200:
        raise RuntimeError(f"Not enough daily closes from CoinGecko: got {len(closes)}")
    gma200 = gma(closes[-200:])
    p = fetch_btc_spot_coinbase()
    e = exp_price(today)
    val = (p / gma200) * (p / e)
    return {
        "value": val,
        "source": "selfcalc(B): CoinGecko daily GMA200 + fixed ExpPrice",
        "gma200": gma200,
        "expPrice": e,
    }


def ahr999_primary_or_fallback():
    # Primary: CoinGlass value provided manually (environment override)
    # Example: export COINGLASS_AHR999=0.42
    v = os.getenv("COINGLASS_AHR999")
    if v:
        try:
            return {"value": float(v), "source": "CoinGlass (manual override via COINGLASS_AHR999)"}
        except:
            pass

    # Fallback: selfcalc
    return ahr999_selfcalc()


def get_dca_instruction():
    # 1) Price
    try:
        price = fetch_btc_spot_coinbase()
    except Exception as e:
        return f"Error: Price fetch failed ({e})."

    # 2) Ahr999
    try:
        ahr = ahr999_primary_or_fallback()
    except Exception as e:
        return f"Error: Ahr999 fetch/calc failed ({e})."

    ahr_val = ahr["value"]
    ahr_source = ahr["source"]

    # 3) Mining cost anchors (MacroMicro Feb 2026 targets; adjustable later)
    total_cost = 85000
    cash_cost = 60000

    # 4) Thresholds (CoinGlass-first semantics)
    # CoinGlass thresholds (conceptual): 3x if <0.40, 2x if <0.45
    # When using self-calc, thresholds are scaled down by ALIGN_RATIO.
    using_selfcalc = ahr_source.startswith("selfcalc")
    thr_3x = (0.40 * ALIGN_RATIO) if using_selfcalc else 0.40
    thr_2x = (0.45 * ALIGN_RATIO) if using_selfcalc else 0.45

    # 5) Multiplier logic (1-2-3 model + pause)
    if price > total_cost * 1.2:
        action = "PAUSE"
    elif price <= cash_cost or ahr_val < thr_3x:
        action = "3x"
    elif price <= total_cost or ahr_val < thr_2x:
        action = "2x"
    else:
        action = "1x"

    # 6) Report
    lines = []
    lines.append("=== QIUQIU DCA ADVISOR ===")
    lines.append(f"BTC Spot (Coinbase): ${price:,.2f}")
    lines.append(f"Ahr999:              {ahr_val:.4f}")
    lines.append(f"Ahr999 Source:       {ahr_source}")
    if "gma200" in ahr:
        lines.append(f"GMA200 (CG daily):   ${ahr['gma200']:,.2f}")
        lines.append(f"ExpPrice (fixed):    ${ahr['expPrice']:,.2f}  [a={A_EXP}, b={B_EXP}]")
    lines.append(f"Mining Anchors:      Total ${total_cost:,.0f} / Cash ${cash_cost:,.0f}")
    lines.append("--------------------------")
    lines.append(f"RECOMMENDED ACTION: [{action}]")
    lines.append("--------------------------")

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_dca_instruction())
