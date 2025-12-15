import yfinance as yf
import json

try:
    symbol = "AAPL"
    print(f"Fetching info for {symbol}...")
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # Print interesting keys for Fundamental/Marketing analysis
    keys_of_interest = [
        'marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE', 'pegRatio',
        'priceToSalesTrailing12Months', 'profitMargins', 'grossMargins', 'operatingMargins',
        'revenueGrowth', 'earningsGrowth', 'returnOnAssets', 'returnOnEquity',
        'totalCash', 'totalDebt', 'quickRatio', 'currentRatio',
        'recommendationKey', 'targetMeanPrice', 'numberOfAnalystOpinions',
        'sector', 'industry', 'longBusinessSummary' 
    ]
    
    print("\n--- FUNDAMENTAL DATA ---")
    for key in keys_of_interest:
        print(f"{key}: {info.get(key, 'N/A')}")

except Exception as e:
    print(f"Error: {e}")
