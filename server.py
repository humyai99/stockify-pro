import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}}) # Allow All Origins

@app.route('/')
def root():
    return app.send_static_file('index.html')

def analyze_sentiment(text):
    """
    Enhanced keyword-based sentiment analysis.
    Returns: Score between -1.0 (Bearish) and 1.0 (Bullish)
    """
    text_lower = text.lower()
    
    # Bullish Keywords
    positive_words = [
        "surge", "soar", "jump", "climb", "rise", "gain", "rally", "up",
        "bull", "profit", "record", "high", "buy", "outperform", "strong", 
        "growth", "beat", "positive", "dividend", "upgrade", "approve", "deal"
    ]
    
    # Bearish Keywords
    negative_words = [
        "plunge", "dive", "drop", "fall", "slide", "down", "crash", "slump",
        "bear", "loss", "miss", "low", "sell", "underperform", "weak",
        "negative", "downgrade", "debt", "risk", "lawsuit", "cut", "ban", "warn"
    ]
    
    score = 0
    for word in positive_words:
        if word in text_lower: score += 1
        
    for word in negative_words:
        if word in text_lower: score -= 1
        
    # Normalize roughly between -1 and 1 based on word content intensity
    if score > 0: return min(score * 0.2, 1.0)
    if score < 0: return max(score * 0.2, -1.0)
    return 0.0

def fetch_google_news(symbol):
    """
    Fetches news from Google News RSS for the given symbol.
    """
    try:
        # Search query: symbol + " stock" to filter relevant news
        url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return []
            
        root = ET.fromstring(response.content)
        news_items = []
        
        # Limit to top 8 items
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            # Use 'source' tag if available, otherwise default
            source_elem = item.find('source')
            publisher = source_elem.text if source_elem is not None else "Google News"
            
            sentiment = analyze_sentiment(title)
            
            news_items.append({
                "title": title,
                "link": link,
                "publisher": publisher,
                "providerPublishTime": pub_date, # Format: Mon, 12 Dec 2025 ...
                "sentiment": sentiment
            })
            
        return news_items
    except Exception as e:
        print(f"Google News Fetch Error: {e}")
        return []

@app.route('/analyze/<symbol>', methods=['GET'])
def analyze(symbol):
    try:
        # 1. Fetch Data (1 Year to ensure enough data for EMA200)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")

        if df.empty:
            return jsonify({"error": "No data found for symbol"}), 404

        # 2. Calculate Indicators (Manual Calculation using Pandas)
        close = df['Close']

        # EMA 200
        df['EMA200'] = close.ewm(span=200, adjust=False).mean()

        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        # Wilder's Smoothing for RSI
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp12 - exp26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        df['MACD_Line'] = macd_line
        df['MACD_Signal'] = signal_line
        df['MACD_Hist'] = histogram

        # 3. Get Latest Values
        latest = df.iloc[-1]
        
        # Calculate Price Change
        # Use previous close from history if available, else 0 change
        if len(df) > 1:
            prev_close = df.iloc[-2]['Close']
            price_change = latest['Close'] - prev_close
            price_change_percent = (price_change / prev_close) * 100
        else:
            price_change = 0.0
            price_change_percent = 0.0

        # Handle cases where EMA200 might be NaN
        ema200 = latest['EMA200']
        if pd.isna(ema200):
            ema200 = latest['Close'] # Fallback

        # Handle NaNs in other indicators if data is too short
        rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50.0
        macd_l = float(latest['MACD_Line']) if not pd.isna(latest['MACD_Line']) else 0.0
        macd_s = float(latest['MACD_Signal']) if not pd.isna(latest['MACD_Signal']) else 0.0
        macd_h = float(latest['MACD_Hist']) if not pd.isna(latest['MACD_Hist']) else 0.0

        # Fetch News from Google
        news = fetch_google_news(symbol)

        # Prepare History for Chart (Last 200 candles)
        # Lightweight Charts expects: { time: 'YYYY-MM-DD', open: ..., high: ..., low: ..., close: ... }
        history = []
        recent_df = df.tail(200) # Limit data to keep payload small
        for index, row in recent_df.iterrows():
            # Format date as YYYY-MM-DD string
            date_str = index.strftime('%Y-%m-%d')
            history.append({
                "time": date_str,
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close'])
            })

        # detailed Stats
        prev_close_val = 0.0
        if len(df) > 1:
            prev_close_val = float(df.iloc[-2]['Close'])

        stats = {
            "open": float(latest['Open']),
            "high": float(latest['High']),
            "low": float(latest['Low']),
            "volume": int(latest['Volume']),
            "prev_close": prev_close_val
        }
        
        # --- FEAR & GREED CALCULATION ---
        # 1. Technical Sentiment (RSI)
        # RSI < 30 = Fear (score 0-30), RSI > 70 = Greed (score 70-100)
        tech_score = rsi_val 
        
        # 2. visual Sentiment (News)
        # News score is -1 to 1. Map to 0-100.
        # -1 -> 0, 0 -> 50, 1 -> 100
        avg_news_score = 0
        if news:
            total_s = sum([n['sentiment'] for n in news]) # sentiment is now float
            avg_news_score = total_s / len(news) if len(news) > 0 else 0
        
        news_score_norm = (avg_news_score + 1) * 50 # Normalize to 0-100
        
        # Weighted Average: 70% Technical, 30% News
        fear_greed_score = (tech_score * 0.7) + (news_score_norm * 0.3)
        
        # Fetch Company Profile & Shareholders
        profile = {}
        holders = []
        fundamentals = {} # NEW: Detailed Analysis Data

        try:
            info = ticker.info
            profile = {
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "summary": info.get('longBusinessSummary', 'No summary available.')
            }
            
            # --- EXTRACT FUNDAMENTALS ---
            fundamentals = {
                "valuation": {
                    "marketCap": info.get('marketCap'),
                    "trailingPE": info.get('trailingPE'),
                    "forwardPE": info.get('forwardPE'),
                    "pegRatio": info.get('pegRatio'),
                    "priceToBook": info.get('priceToBook'),
                    "priceToSales": info.get('priceToSalesTrailing12Months')
                },
                "profitability": {
                    "grossMargins": info.get('grossMargins'),
                    "operatingMargins": info.get('operatingMargins'),
                    "profitMargins": info.get('profitMargins'),
                    "returnOnEquity": info.get('returnOnEquity'),
                    "returnOnAssets": info.get('returnOnAssets')
                },
                "growth": {
                    "revenueGrowth": info.get('revenueGrowth'),
                    "earningsGrowth": info.get('earningsGrowth')
                },
                "health": {
                    "totalCash": info.get('totalCash'),
                    "totalDebt": info.get('totalDebt'),
                    "currentRatio": info.get('currentRatio'),
                    "quickRatio": info.get('quickRatio'),
                    "debtToEquity": info.get('debtToEquity')
                },
                "consensus": {
                    "targetMean": info.get('targetMeanPrice'),
                    "targetHigh": info.get('targetHighPrice'),
                    "targetLow": info.get('targetLowPrice'),
                    "recommendation": info.get('recommendationKey'), # e.g. "buy", "hold"
                    "numberOfAnalysts": info.get('numberOfAnalystOpinions')
                }
            }

            # Fetch Major Holders
            inst = ticker.institutional_holders
            if inst is not None and not inst.empty:
                for index, row in inst.head(5).iterrows():
                    pct = row.get('pctHeld', 0)
                    holder_name = row.get('Holder', 'Unknown')
                    holders.append({
                        "desc": holder_name,
                        "value": f"{pct*100:.2f}%"
                    })
            else:
                major = ticker.major_holders
                if major is not None and not major.empty:
                    for index, row in major.head(5).iterrows():
                        val = row.iloc[0]
                        desc = str(index)
                        holders.append({
                            "desc": desc,
                            "value": str(val)
                        })
        except Exception as e:
            print(f"Profile/Holders fetch error: {e}")
            
        result = {
            "symbol": symbol.upper(),
            "price": float(latest['Close']),
            "change_percent": float(price_change_percent),
            "ema200": float(ema200),
            "rsi": rsi_val,
            "macd": {
                "line": macd_l,
                "signal": macd_s,
                "histogram": macd_h
            },
            "news": news,
            "sentiment_meter": {
                "score": fear_greed_score,
                "description": "Greed" if fear_greed_score > 60 else ("Fear" if fear_greed_score < 40 else "Neutral")
            },
            "history": history,
            "stats": stats,
            "profile": profile,
            "holders": holders,
            "fundamentals": fundamentals # Include in response
        }

        return jsonify(result)

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/screen', methods=['GET'])
def screen_stocks():
    try:
        # Predefined Watchlist (Major US & Thai Stocks)
        symbols = [
            "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMD", "META", "AMZN", # US Tech
            "PTT.BK", "AOT.BK", "CPALL.BK", "DELTA.BK", "SCB.BK", "KBANK.BK", "BDMS.BK", "ADVANC.BK" # TH Bluechips
        ]
        
        # Bulk Fetch (1 Year history for EMA200)
        # yfinance.download can handle multiple tickers
        print(f"Scanning {len(symbols)} stocks...")
        data = yf.download(symbols, period="1y", group_by='ticker', progress=False)
        
        results = []
        
        for symbol in symbols:
            try:
                # Handle Multi-level columns from yfinance bulk download
                if len(symbols) > 1:
                    df = data[symbol].copy()
                else:
                    df = data.copy()
                
                if df.empty or 'Close' not in df:
                    continue
                    
                # Drop NaNs
                df.dropna(subset=['Close'], inplace=True)
                
                if len(df) < 50: continue

                # Calculate Technicals (Simplified for Screener speed)
                close = df['Close']
                latest_close = float(close.iloc[-1])
                
                # EMA 200
                ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
                
                # RSI 14
                delta = close.diff()
                gain = (delta.where(delta > 0, 0))
                loss = (-delta.where(delta < 0, 0))
                avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                latest_rsi = float(rsi.iloc[-1])
                
                # MACD
                exp12 = close.ewm(span=12, adjust=False).mean()
                exp26 = close.ewm(span=26, adjust=False).mean()
                macd_line = exp12 - exp26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                latest_macd = float(macd_line.iloc[-1])
                latest_signal = float(signal_line.iloc[-1])

                # Determine Signal
                signal = "WAIT"
                trend = "UP" if latest_close > ema200 else "DOWN"
                
                # Match logic with analyst.js roughly
                is_uptrend = latest_close > ema200
                macd_bull = latest_macd > latest_signal
                
                if is_uptrend:
                    if latest_rsi > 30 and latest_rsi < 55 and macd_bull:
                        signal = "BUY"
                    elif latest_rsi > 30 and latest_rsi < 50:
                         signal = "BUY (Weak)"
                else:
                    # Downtrend
                    if latest_rsi < 70 and latest_rsi > 45 and not macd_bull:
                        signal = "SELL"
                        
                # Fundamentals (Mock/Limited for speed in screener, avoid N+1 API calls)
                # In a real app, we would cache 'info' calls or fetch asynchronously.
                # For this demo, we skip detailed fundamentals in the list view to preserve speed.

                results.append({
                    "symbol": symbol,
                    "price": latest_close,
                    "rsi": latest_rsi,
                    "change": 0.0, # Bulk download doesn't give easy % change without prev fetch, skip for speed
                    "signal": signal,
                    "trend": trend,
                    "macd_bull": macd_bull
                })

            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue

        return jsonify({"count": len(results), "data": results})

    except Exception as e:
        print(f"Screener Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/backtest/<symbol>', methods=['GET'])
def backtest_stock(symbol):
    try:
        # Fetch 2 Years of data to have enough runway for EMA200 + Backtest
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y")
        
        if df.empty:
            return jsonify({"error": "No data found"}), 404

        # Calculate Indicators for the entrie dataframe
        close = df['Close']
        df['EMA200'] = close.ewm(span=200, adjust=False).mean()
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        df['MACD_Line'] = macd
        df['MACD_Signal'] = signal

        # Simulation
        capital = 10000.0  # Start with $10,000
        position = 0       # Number of shares
        entry_price = 0.0
        
        trades = []
        equity_curve = []
        
        # Start loop after EMA200 is valid (skip first 200 days)
        start_idx = 200
        if len(df) <= start_idx:
             return jsonify({"error": "Not enough data history for backtest"}), 400

        for i in range(start_idx, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            date = df.index[i].strftime('%Y-%m-%d')
            price = float(row['Close'])
            
            # Logic (Simplified Version of Analyst.js)
            is_uptrend = price > row['EMA200']
            macd_bull = row['MACD_Line'] > row['MACD_Signal']
            rsi = row['RSI']
            
            # SIGNAL GENERATION
            action = "WAIT"
            
            # BUY Logic
            if position == 0:
                # Same as Analyst: Uptrend + (RSI Dip or MACD Cross)
                if is_uptrend:
                    if (rsi > 30 and rsi < 55) and macd_bull:
                        action = "BUY"
            
            # SELL Logic
            elif position > 0:
                # Stop Loss (Fixed 5%) or Take Profit (Trend reversal)
                pct_change = (price - entry_price) / entry_price
                
                if pct_change < -0.05: # Stop Loss
                    action = "SELL"
                elif not is_uptrend and rsi > 50: # Trend Broken
                    action = "SELL"
                elif rsi > 70: # Take Profit on Overbought
                    action = "SELL"

            # EXECUTION
            if action == "BUY" and position == 0:
                position = capital / price
                entry_price = price
                trades.append({
                    "date": date,
                    "action": "BUY",
                    "price": price,
                    "value": capital
                })
            elif action == "SELL" and position > 0:
                capital = position * price
                trade_return = (price - entry_price) / entry_price
                trades.append({
                    "date": date,
                    "action": "SELL",
                    "price": price,
                    "value": capital,
                    "return": trade_return
                })
                position = 0
                entry_price = 0

            # Record Daily Equity
            current_equity = capital if position == 0 else position * price
            equity_curve.append({"time": date, "value": current_equity})

        # Calculate Stats
        total_return_pct = ((capital - 10000) / 10000) * 100
        winning_trades = [t for t in trades if t["action"] == "SELL" and t.get("return", 0) > 0]
        losing_trades = [t for t in trades if t["action"] == "SELL" and t.get("return", 0) <= 0]
        total_closed_trades = len(winning_trades) + len(losing_trades)
        
        win_rate = (len(winning_trades) / total_closed_trades * 100) if total_closed_trades > 0 else 0
        
        return jsonify({
            "initial_capital": 10000,
            "final_capital": capital,
            "return_pct": total_return_pct,
            "win_rate": win_rate,
            "total_trades": total_closed_trades,
            "equity_curve": equity_curve, # For Charting
            "trades": trades[-5:] # Last 5 trades for detail
        })

    except Exception as e:
        print(f"Backtest Error: {e}")
        return jsonify({"error": str(e)}), 500

# Simple In-Memory Cache
CACHE = {
    "discovery": None,
    "last_updated": 0
}
CACHE_DURATION = 300 # 5 Minutes

@app.route('/discover', methods=['GET'])
def discover_opportunities():
    global CACHE
    current_time = time.time()
    
    # Check Cache
    if CACHE["discovery"] and (current_time - CACHE["last_updated"] < CACHE_DURATION):
        print("Serving Discovery from Cache ⚡")
        return jsonify(CACHE["discovery"])

    try:
        # Curated Discovery List (Mix of Big Cap & Growth/Volatile)
        watchlist = [
            "NVDA", "TSLA", "AMD", "META", "MSFT", "GOOGL", "AMZN", # US Tech
            "MSTR", "COIN", # Crypto Proxies
            "DELTA.BK", "HANA.BK", "KCE.BK", # TH Electronics (Volatile)
            "ADVANC.BK", "AOT.BK", "PTT.BK", "CPALL.BK", "BDMS.BK", "SCB.BK", "KBANK.BK", # TH Bluechip
            "JTS.BK", "FORTH.BK", "SABUY.BK" # TH Growth/Speculative
        ]
        
        # Bulk Fetch (1mo is enough for Trend + RSI) - OPTIMIZED SPEED
        print("Fetching Discovery Data...")
        data = yf.download(watchlist, period="1mo", group_by='ticker', progress=False)
        
        opportunities = []
        
        for symbol in watchlist:
            try:
                if len(watchlist) > 1:
                    df = data[symbol].copy()
                else:
                    df = data.copy()
                
                if df.empty or 'Close' not in df: continue
                
                # Cleanup
                df.dropna(subset=['Close'], inplace=True)
                if len(df) < 15: continue # Require minimum data
                
                close = df['Close']
                price = float(close.iloc[-1])
                prev_price = float(close.iloc[-2])
                change_pct = ((price - prev_price) / prev_price) * 100
                
                # Indicators
                ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
                
                delta = close.diff()
                gain = (delta.where(delta > 0, 0))
                loss = (-delta.where(delta < 0, 0))
                avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
                rs = avg_gain / avg_loss
                rsi = float(100 - (100 / (1 + rs)).iloc[-1])
                
                # Filter Logic for "Discovery"
                signal_type = "Neutral"
                score = 0
                
                if price > ema50:
                    score += 1
                    if rsi > 50 and rsi < 75:
                        signal_type = "Bullish 🔥"
                        score += 2
                    elif rsi >= 75:
                        signal_type = "Strong Momentum 🚀"
                        score += 3
                elif rsi < 30:
                    signal_type = "Oversold Rebound? 🟢"
                    score += 1

                # Classify
                category = "US Tech"
                if ".BK" in symbol:
                    if symbol in ["JTS.BK", "FORTH.BK", "SABUY.BK", "DELTA.BK"]: category = "TH Growth 🚀"
                    else: category = "TH Bluechip 🇹🇭"
                elif symbol in ["MSTR", "COIN"]: category = "Crypto Proxy 🪙"
                
                if score > 0: # Only return interesting ones
                    opportunities.append({
                        "symbol": symbol,
                        "price": price,
                        "change": change_pct,
                        "rsi": rsi,
                        "signal": signal_type,
                        "category": category,
                        "score": score
                    })

            except Exception as e:
                continue

        # Sort by Score (Desc) then Change (Desc)
        opportunities.sort(key=lambda x: (x['score'], x['change']), reverse=True)
        results = opportunities[:8]
        
        # Update Cache
        CACHE["discovery"] = results
        CACHE["last_updated"] = current_time
        
        return jsonify(results)

    except Exception as e:
        print(f"Discover Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Stockify Data Server Running on port 5000...")
    app.run(debug=True, port=5000)



