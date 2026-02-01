import requests
import time
import sys

def get_btc_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = float(data['price'])
        print(f"BTC/USDT (Binance): ${price:,.2f}")
    except Exception as e:
        print(f"Error fetching price: {e}")

if __name__ == "__main__":
    get_btc_price()
