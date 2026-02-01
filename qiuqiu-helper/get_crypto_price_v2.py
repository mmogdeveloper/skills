import requests

def get_btc_price_okx():
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['code'] == '0':
            price = float(data['data'][0]['last'])
            print(f"BTC/USDT (OKX): ${price:,.2f}")
        else:
            print(f"OKX API Error: {data['msg']}")
    except Exception as e:
        print(f"Error fetching from OKX: {e}")

def get_btc_price_coinbase():
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = float(data['data']['amount'])
        print(f"BTC/USD (Coinbase): ${price:,.2f}")
    except Exception as e:
        print(f"Error fetching from Coinbase: {e}")

if __name__ == "__main__":
    get_btc_price_okx()
    get_btc_price_coinbase()
