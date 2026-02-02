import math
import datetime as dt
import requests

# Self-calculated Ahr999 (B option): fixed regression parameters for ExpPrice
# Reference form used widely online:
# ExpPrice = 10^(a*log10(days_since_genesis) + b)
# with a=5.84, b=-17.01
A = 5.84
B = -17.01

GENESIS = dt.date(2009, 1, 3)


def gma(prices):
    # geometric mean
    s = 0.0
    n = 0
    for p in prices:
        if p and p > 0:
            s += math.log(p)
            n += 1
    return math.exp(s / n) if n else None


def fetch_btc_daily_closes(days: int = 220):
    # CoinGecko market_chart returns prices (ms, price) with hourly granularity for shorter windows,
    # but for 200+ days it typically returns daily-ish points. We'll downsample by date.
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": str(days), "interval": "daily"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("prices", [])

    by_date = {}
    for ts_ms, price in data:
        d = dt.datetime.utcfromtimestamp(ts_ms / 1000).date()
        by_date[d] = float(price)

    # return sorted closes
    closes = [by_date[d] for d in sorted(by_date.keys())]
    return closes


def fetch_btc_spot_coinbase():
    r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10)
    r.raise_for_status()
    return float(r.json()["data"]["amount"])


def exp_price(today: dt.date):
    days = (today - GENESIS).days
    return 10 ** (A * math.log10(days) + B)


def ahr999_value(price: float, gma200: float, exp_p: float):
    return (price / gma200) * (price / exp_p)


def main():
    today = dt.datetime.utcnow().date()

    closes = fetch_btc_daily_closes(240)
    if len(closes) < 200:
        raise RuntimeError(f"Not enough daily closes from CoinGecko: got {len(closes)}")

    gma200 = gma(closes[-200:])
    p = fetch_btc_spot_coinbase()
    e = exp_price(today)
    val = ahr999_value(p, gma200, e)

    print("=== Ahr999 (Self-calc B) ===")
    print(f"BTC spot (Coinbase): ${p:,.2f}")
    print(f"GMA200 (CG daily):   ${gma200:,.2f}")
    print(f"ExpPrice (fixed):    ${e:,.2f}  [a={A}, b={B}]")
    print(f"Ahr999:              {val:.4f}")


if __name__ == "__main__":
    main()
