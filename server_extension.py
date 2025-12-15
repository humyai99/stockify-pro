
def analyze_streaks():
    """
    Analyzes watchlist for consecutive daily streaks (Up/Down).
    Returns lists of gainers and losers.
    """
    try:
        watchlist = [
            "NVDA", "TSLA", "AMD", "META", "MSFT", "GOOGL", "AMZN",
            "MSTR", "COIN",
            "DELTA.BK", "HANA.BK", "KCE.BK",
            "ADVANC.BK", "AOT.BK", "PTT.BK", "CPALL.BK", "BDMS.BK", "SCB.BK", "KBANK.BK",
            "JTS.BK", "FORTH.BK", "SABUY.BK"
        ]
        
        # optimized: fetch 1mo history for all
        data = yf.download(watchlist, period="1mo", group_by='ticker', progress=False, auto_adjust=True)
        
        gainers = []
        losers = []
        
        for symbol in watchlist:
            try:
                if len(watchlist) > 1:
                    df = data[symbol].copy()
                else:
                    df = data.copy()
                
                if df.empty or 'Close' not in df: continue
                
                df.dropna(subset=['Close'], inplace=True)
                if len(df) < 5: continue
                
                close = df['Close']
                streak = 0
                direction = "Neutral" # Up, Down
                
                # Iterate backwards from result
                # Start from last day vs previous day
                # We need to count how many consecutive days match the direction of the latest movement
                
                # Check latest day direction
                today = close.iloc[-1]
                yesterday = close.iloc[-2]
                
                if today > yesterday:
                    direction = "Up"
                elif today < yesterday:
                    direction = "Down"
                else:
                    continue # No streak if flat
                    
                streak = 1
                
                # Loop back
                for i in range(len(close)-2, 0, -1):
                    current = close.iloc[i]
                    prev = close.iloc[i-1]
                    
                    if direction == "Up":
                        if current > prev: streak += 1
                        else: break
                    elif direction == "Down":
                        if current < prev: streak += 1
                        else: break
                
                # Filter for significance (e.g. at least 3 days)
                if streak >= 3:
                     pct_tot = ((today - close.iloc[-(streak+1)]) / close.iloc[-(streak+1)]) * 100
                     
                     item = {
                         "symbol": symbol,
                         "price": float(today),
                         "streak": streak,
                         "total_change": float(pct_tot)
                     }
                     
                     if direction == "Up": gainers.append(item)
                     else: losers.append(item)
                     
            except Exception as e:
                continue
                
        # Sort by streak length descendant
        gainers.sort(key=lambda x: x['streak'], reverse=True)
        losers.sort(key=lambda x: x['streak'], reverse=True)
        
        return {"gainers": gainers, "losers": losers}

    except Exception as e:
        print(f"Streak Analysis Error: {e}")
        return {"gainers": [], "losers": []}

@app.route('/streaks', methods=['GET'])
def get_streaks():
    return jsonify(analyze_streaks())

@app.route('/trends')
def trends_page():
    return app.send_static_file('trends.html')
