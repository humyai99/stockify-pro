import yfinance as yf
import pandas as pd

try:
    symbol = "AAPL"
    print(f"Fetching data for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    print("\n--- MAJOR HOLDERS ---")
    major = ticker.major_holders
    if major is not None:
        print(major)
        print("\nColumns:", major.columns)
        print("Shape:", major.shape)
        # Try iterating
        print("\nIterating:")
        for index, row in major.iterrows():
            print(f"Row {index}: 0={row.iloc[0]}, 1={row.iloc[1]}")
    else:
        print("Major holders is None")

    print("\n--- INSTITUTIONAL HOLDERS ---")
    inst = ticker.institutional_holders
    if inst is not None:
        print(inst.head())
        print("\nColumns:", inst.columns)
    else:
        print("Institutional holders is None")

except Exception as e:
    print(f"Error: {e}")
