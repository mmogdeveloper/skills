import requests
import sys

def test_coinglass_v2(api_key):
    # Coinglass v2 API often expects the key in 'coinglassApiKeys' header
    url = "https://open-api.coinglass.com/public/v2/open_interest?symbol=BTC"
    headers = {
        "accept": "application/json",
        "coinglassApiKeys": api_key
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_coinglass_v2(sys.argv[1])
