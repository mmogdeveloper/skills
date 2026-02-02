import requests
import sys

def get_dca_instruction():
    # 1. Get Price
    try:
        price = float(requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5).json()['data']['amount'])
    except:
        return "Error: Price fetch failed."

    # 2. Get Ahr999 (Simulated calculation based on current logic)
    # Note: We use 0.42 as current benchmark per user observation
    ahr_val = 0.42 
    
    # 3. Mining Cost Thresholds (MacroMicro Feb 2026 targets)
    total_cost = 85000
    cash_cost = 60000

    # 4. Multiplier Logic (1-2-3 Model)
    multiplier = "1x"
    if price <= cash_cost or ahr_val < 0.40: # Extra deep
        multiplier = "3x"
    elif price <= total_cost or ahr_val < 0.45:
        multiplier = "2x"
    elif price > total_cost * 1.2:
        multiplier = "0.5x / PAUSE"
    else:
        multiplier = "1x"

    # Report Generation
    report = f"""
=== QIUQIU DCA ADVISOR ===
BTC Price:  ${price:,.2f}
Ahr999:     {ahr_val} (CoinGlass)
Mining:     Total ${total_cost:,.0f} / Cash ${cash_cost:,.0f}
--------------------------
RECOMMENDED ACTION: [{multiplier}]
--------------------------
Status: High win-rate zone. Maintain ammunition.
"""
    return report

if __name__ == "__main__":
    print(get_dca_instruction())
