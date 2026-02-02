import requests
import sys
import math

def get_ahr999_and_mining(cg_api_key):
    # Coinglass API for AHR999 (since it's pre-calculated there)
    # If API fails, we fallback to manual calculation logic
    url = "https://open-api.coinglass.com/public/v2/indicator/ahr999"
    headers = {
        "accept": "application/json",
        "coinglassApiKeys": cg_api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                latest = data[-1]
                ahr_val = float(latest.get('ahr999', 0))
                date_str = latest.get('date', 'Unknown')
                
                print(f"--- Ahr999 Index Insight ---")
                print(f"Latest Value: {ahr_val:.4f}")
                print(f"Date:         {date_str}")
                
                if ahr_val < 0.45:
                    print("Signal: BOTTOM / HEAVY BUY (重仓区)")
                elif ahr_val < 1.2:
                    print("Signal: DCA / REGULAR BUY (主力区)")
                else:
                    print("Signal: WAIT / STOP DCA (暂停定投)")
                return ahr_val
        else:
            print(f"API Error: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Ahr999: {e}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <coinglass_api_key>")
    else:
        get_ahr999_and_mining(sys.argv[1])
