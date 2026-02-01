import requests
import sys

def get_market_data(api_key):
    # CoinGecko Demo API base URL
    base_url = "https://api.coingecko.com/api/v3"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": api_key
    }
    
    try:
        # Get BTC market data
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }
        response = requests.get(f"{base_url}/simple/price", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()['bitcoin']
        
        # Get Global Market Cap & Fear/Greed (if available)
        # Note: Global data doesn't always need an ID
        
        print("--- CoinGecko Market Analysis ---")
        print(f"Global Avg Price: ${data['usd']:,.2f}")
        print(f"24h Change: {data['usd_24h_change']:.2f}%")
        print(f"24h Volume: ${data['usd_24h_vol']:,.0f}")
        
    except Exception as e:
        print(f"Error fetching from CoinGecko: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <api_key>")
    else:
        get_market_data(sys.argv[1])
