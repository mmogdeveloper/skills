import requests
import sys

def get_pulse(cg_api_key):
    # Sources
    CB_URL = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    CG_URL = "https://api.coingecko.com/api/v3/simple/price"
    
    pulse_data = {}

    # 1. Get Coinbase Instant Price
    try:
        cb_res = requests.get(CB_URL, timeout=5)
        pulse_data['cb_price'] = float(cb_res.json()['data']['amount'])
    except:
        pulse_data['cb_price'] = None

    # 2. Get CoinGecko Market Metrics
    try:
        cg_headers = {"x-cg-demo-api-key": cg_api_key}
        cg_params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        cg_res = requests.get(CG_URL, headers=cg_headers, params=cg_params, timeout=5)
        cg_data = cg_res.json()['bitcoin']
        pulse_data['cg_price'] = cg_data['usd']
        pulse_data['change_24h'] = cg_data['usd_24h_change']
        pulse_data['vol_24h'] = cg_data['usd_24h_vol']
    except:
        pulse_data['cg_price'] = None

    # Output Summary
    print("=== CRYPTO PULSE [BTC] ===")
    if pulse_data['cb_price']:
        print(f"Coinbase (Spot): ${pulse_data['cb_price']:,.2f}")
    if pulse_data['cg_price']:
        print(f"Global Avg:      ${pulse_data['cg_price']:,.2f}")
        print(f"24h Change:      {pulse_data['change_24h']:.2f}%")
        print(f"24h Volume:      ${pulse_data['vol_24h']/1e9:.2f}B")
    
    # Pragmatic Analysis
    if pulse_data['cb_price'] and pulse_data['cg_price']:
        diff = pulse_data['cb_price'] - pulse_data['cg_price']
        if abs(diff) > 50:
            print(f"Alert: High Spread (${diff:.2f}) - High Volatility Detected.")
        
        if pulse_data['change_24h'] < -5:
            print("Status: Blood on the streets. Watch for bottom support.")
        elif pulse_data['change_24h'] > 5:
            print("Status: Strong momentum. Watch for resistance.")
        else:
            print("Status: Ranging/Consolidating.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing CG API Key")
    else:
        get_pulse(sys.argv[1])
