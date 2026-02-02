import requests
import math
import datetime as dt
import os
import json

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

# Ammo tracking
DEFAULT_TRACKER_PATH = os.path.expanduser("/home/mmogdeveloper/.openclaw/workspace/memory/dca_ammo_tracker.json")
DEFAULT_TOTAL_UNITS = 600


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


def fetch_mvrv_zscore_last(n: int = 1):
    # Free-ish on-chain endpoint (BGeometrics / bitcoin-data.com)
    # Example: https://bitcoin-data.com/v1/mvrv-zscore/1
    url = f"https://bitcoin-data.com/v1/mvrv-zscore/{n}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    j = r.json()
    # when n=1, response is an object; when n>1, could be list (keep simple)
    if isinstance(j, list):
        j = j[-1]
    return {
        "date": j.get("d"),
        "value": float(j.get("mvrvZscore")),
        "source": "bitcoin-data.com (BGeometrics) /v1/mvrv-zscore",
    }


def load_tracker(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"total_units": DEFAULT_TOTAL_UNITS, "units_used": 0, "history": []}


def save_tracker(path: str, tracker: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def action_to_units(action: str) -> int:
    # Returns how many baseline units consumed for the day
    if action == "PAUSE":
        return 0
    if action == "1x":
        return 1
    if action == "2x":
        return 2
    if action == "3x":
        return 3
    return 0


def update_tracker_for_today(tracker_path: str, action: str):
    today = dt.datetime.utcnow().date().isoformat()
    tracker = load_tracker(tracker_path)
    tracker.setdefault("total_units", DEFAULT_TOTAL_UNITS)
    tracker.setdefault("units_used", 0)
    tracker.setdefault("history", [])

    # avoid double counting the same day
    for item in tracker["history"]:
        if item.get("date") == today:
            return tracker

    units = action_to_units(action)
    tracker["history"].append({"date": today, "action": action, "units": units})
    tracker["units_used"] = int(tracker.get("units_used", 0)) + units
    save_tracker(tracker_path, tracker)
    return tracker


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

    # 3) On-chain confirmation: MVRV Z-Score
    try:
        mvrv = fetch_mvrv_zscore_last(1)
    except Exception as e:
        mvrv = {"date": None, "value": None, "source": f"unavailable ({e})"}

    # 4) Mining cost anchors (MacroMicro Feb 2026 targets; adjustable later)
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

    # 6) MVRV confirmation rule (to prevent over-aggressive 3x)
    # Only allow 3x when MVRV Z-Score is "low" (cheap vs realized value).
    # If MVRV is unavailable, we do NOT block 3x (best-effort), but we mark it.
    if action == "3x" and mvrv.get("value") is not None:
        if mvrv["value"] > 1.0:
            action = "2x"

    # 7) Ammo tracking (record today's recommended action as baseline consumption)
    tracker_path = os.getenv("DCA_TRACKER_PATH", DEFAULT_TRACKER_PATH)
    tracker = update_tracker_for_today(tracker_path, action)
    total_units = int(tracker.get("total_units", DEFAULT_TOTAL_UNITS))
    used_units = int(tracker.get("units_used", 0))
    remaining_units = max(total_units - used_units, 0)

    # 8) Report
    lines = []
    lines.append("=== QIUQIU DCA ADVISOR ===")
    lines.append(f"BTC Spot (Coinbase): ${price:,.2f}")
    lines.append(f"Ahr999:              {ahr_val:.4f}")
    lines.append(f"Ahr999 Source:       {ahr_source}")
    if "gma200" in ahr:
        lines.append(f"GMA200 (CG daily):   ${ahr['gma200']:,.2f}")
        lines.append(f"ExpPrice (fixed):    ${ahr['expPrice']:,.2f}  [a={A_EXP}, b={B_EXP}]")
    lines.append(f"MVRV Z-Score:         {mvrv.get('value')}  ({mvrv.get('date')})")
    lines.append(f"MVRV Source:          {mvrv.get('source')}")
    lines.append(f"Mining Anchors:       Total ${total_cost:,.0f} / Cash ${cash_cost:,.0f}")
    lines.append("--------------------------")
    lines.append(f"RECOMMENDED ACTION:  [{action}]")
    lines.append("--------------------------")
    lines.append(f"Ammo (baseline units): used {used_units}/{total_units}, remaining {remaining_units}")
    lines.append(f"Tracker: {tracker_path}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_dca_instruction())
