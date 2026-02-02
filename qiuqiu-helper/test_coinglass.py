import requests
import sys

def test_coinglass(api_key):
    # Testing with a simpler v2 endpoint
    url = "https://open-api.coinglass.com/public/v2/indicator/liquidation_symbol?symbol=BTC&interval=h1"
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
    test_coinglass(sys.argv[1])
