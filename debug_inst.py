import yfinance as yf
import pandas as pd

try:
    symbol = "AAPL"
    print(f"Fetching data for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    print("\n--- INSTITUTIONAL HOLDERS ---")
    inst = ticker.institutional_holders
    if inst is not None:
        print(inst)
        print("\nColumns:", inst.columns)
        # Iterate
        for index, row in inst.head().iterrows():
            print(f"Row: {row.values}")
    else:
        print("Institutional holders is None")
        
    print("\n--- MUTUALFUND HOLDERS ---")
    mf = ticker.mutualfund_holders
    if mf is not None:
        print(mf.head())
    else:
        print("Mutualfund holders is None")

except Exception as e:
    print(f"Error: {e}")
