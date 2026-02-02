import requests
import sys

def get_coinglass_ahr999(api_key):
    # CoinGlass API v2 Indicator endpoint for ahr999
    # Note: Using the historical endpoint to get the latest point
    url = "https://open-api.coinglass.com/public/v2/indicator/ahr999"
    headers = {
        "accept": "application/json",
        "coinglassApiKeys": api_key
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get('success') and res_json.get('data'):
                # Data is usually a list of daily values
                latest = res_json['data'][-1]
                val = latest.get('ahr999')
                date = latest.get('date')
                print(f"--- CoinGlass Ahr999 Official ---")
                print(f"Value: {val}")
                print(f"Date:  {date}")
                
                if val < 0.45:
                    print("Status: BOTTOM (重仓区/抄底)")
                elif val < 1.2:
                    print("Status: DCA (主力区/定投)")
                else:
                    print("Status: WAIT (暂停区/持币)")
            else:
                print(f"API Error: {res_json.get('msg', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"Fetch Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <api_key>")
    else:
        get_coinglass_ahr999(sys.argv[1])
