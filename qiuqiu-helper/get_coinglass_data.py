import requests
import sys

def get_coinglass_data(api_key):
    # CoinGlass API v2 Base URL
    base_url = "https://open-api.coinglass.com/public/v2"
    headers = {
        "accept": "application/json",
        "coinglassApiKeys": api_key
    }
    
    analysis = {}
    
    try:
        # 1. Open Interest (BTC)
        oi_res = requests.get(f"{base_url}/open_interest?symbol=BTC", headers=headers, timeout=10)
        if oi_res.status_code == 200:
            oi_data = oi_res.json().get('data', [])
            if oi_data:
                # Total OI is usually the first item or aggregated
                total_oi = sum(item.get('openInterest', 0) for item in oi_data)
                analysis['oi'] = total_oi
        
        # 2. Funding Rate (BTC)
        fr_res = requests.get(f"{base_url}/funding_rate?symbol=BTC", headers=headers, timeout=10)
        if fr_res.status_code == 200:
            fr_data = fr_res.json().get('data', [])
            if fr_data:
                # Get average funding rate across major exchanges
                avg_fr = sum(item.get('uMarginRate', 0) for item in fr_data) / len(fr_data)
                analysis['funding'] = avg_fr

        # 3. Liquidation (Last 1h/24h)
        liq_res = requests.get(f"{base_url}/liquidation/symbol?symbol=BTC&interval=h1", headers=headers, timeout=10)
        if liq_res.status_code == 200:
            liq_data = liq_res.json().get('data', [])
            if liq_data:
                short_liq = sum(item.get('shortVolUsd', 0) for item in liq_data)
                long_liq = sum(item.get('longVolUsd', 0) for item in liq_data)
                analysis['short_liq'] = short_liq
                analysis['long_liq'] = long_liq

        return analysis
    except Exception as e:
        print(f"Error fetching from CoinGlass: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <api_key>")
    else:
        result = get_coinglass_data(sys.argv[1])
        if result:
            print("--- CoinGlass Derivatives Insight ---")
            if 'oi' in result: print(f"Open Interest (BTC): ${result['oi']/1e9:.2f}B")
            if 'funding' in result: print(f"Avg Funding Rate:    {result['funding']:.4f}%")
            if 'long_liq' in result: print(f"1h Long Liq:         ${result['long_liq']/1e6:.2f}M")
            if 'short_liq' in result: print(f"1h Short Liq:        ${result['short_liq']/1e6:.2f}M")
