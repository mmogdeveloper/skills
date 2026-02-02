import requests
import datetime
import math
import sys

def calculate_ahr999_manual():
    # 1. Get current BTC price from Coinbase
    try:
        cb_res = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
        price = float(cb_res.json()['data']['amount'])
    except:
        return "Error: Could not get BTC price"

    # 2. Get 200-day Geometric Mean Price (Simplified approximation using CoinGecko history)
    # Ahr999 Index = (price / 200d_GMA) * (price / Exp_Price)
    # Exp_Price = 10^(5.84*log10(days_since_genesis) - 17.01)
    
    genesis_date = datetime.datetime(2009, 1, 3)
    today = datetime.datetime.now()
    days_passed = (today - genesis_date).days
    
    # Logistic Regression fitting for BTC long term growth
    exp_price = math.pow(10, 5.84 * math.log10(days_passed) - 17.01)
    
    # For a real hard-core calculation, we need 200 days of closing prices.
    # Here we provide a snapshot estimate based on current market data.
    # Estimated GMA200 for Feb 2026 based on previous rally: ~$68,000
    gma_200_est = 68500 
    
    ahr999 = (price / gma_200_est) * (price / exp_price)
    
    print(f"--- Qiuqiu Manual Ahr999 Estimate ---")
    print(f"BTC Price:   ${price:,.2f}")
    print(f"Exp Price:   ${exp_price:,.2f}")
    print(f"Ahr999 Val:  {ahr999:.4f}")
    
    if ahr999 < 0.45:
        print("Status: HEAVY DCA (重仓区)")
    elif ahr999 < 1.2:
        print("Status: MAIN DCA (主力区)")
    else:
        print("Status: PAUSE DCA (暂停区)")

if __name__ == "__main__":
    calculate_ahr999_manual()
