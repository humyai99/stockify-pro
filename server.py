import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta

# Fix for yfinance blocking on cloud servers
# Set custom headers to mimic browser requests
yf_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Create custom session with headers
session = requests.Session()
session.headers.update(yf_headers)

# Disable yfinance cache to avoid issues
try:
    yf.set_tz_cache_location("/tmp/yfinance_cache")
except:
    pass

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}}) # Allow All Origins

@app.route('/')
def root():
    return app.send_static_file('index.html')

# Master Watchlist - Source of Truth
MASTER_WATCHLIST = [
    # US Tech & Bluechip
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMD", "META", "AMZN", "NFLX", "INTC", "IBM", "ORCL",
    "JPM", "BAC", "WMT", "KO", "DIS", "MCD", "NKE",
    # Crypto
    "BTC-USD", "ETH-USD", "DOGE-USD", "SOL-USD", "MSTR", "COIN", 
    # China / HK
    "BABA", "JD", "PDD", "BIDU", "0700.HK", "9988.HK", "0992.HK", "BYDDF",
    # Japan (Tokyo)
    "7203.T", "6758.T", "7974.T", "9984.T", # Toyota, Sony, Nintendo, Softbank
    # Europe (ADRs often easier for free data)
    "NVO", "ASML", "SAP", "AZN", "SHEL", "LVMUY",
    # TH Bluechips & Growth
    "PTT.BK", "AOT.BK", "CPALL.BK", "DELTA.BK", "SCB.BK", "KBANK.BK", "BDMS.BK", "ADVANC.BK",
    "HANA.BK", "KCE.BK", "JTS.BK", "FORTH.BK", "SABUY.BK", "GULF.BK", "EA.BK", "JMART.BK"
]

@app.route('/stocks')
def get_all_stocks():
    """Returns the master list of supported stocks."""
    return jsonify(sorted(list(set(MASTER_WATCHLIST))))

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


# --- Helper: Detailed Technical Score ---
def calculate_technical_score(df_in):
    if df_in.empty or len(df_in) < 30: return {}
    
    c = df_in['Close']
    h = df_in['High']
    l = df_in['Low']
    curr_close = c.iloc[-1]
    
    # 1. RSI (Calculate manually here to be self-contained or rely on passed DF if columns exist)
    # We will assume DF passed in has basics, but let's re-calc to be safe/independent
    delta = c.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = gain / loss
    rsi_series = 100 - (100 / (1 + rs))
    curr_rsi = rsi_series.iloc[-1]
    
    # 2. MACD
    exp12 = c.ewm(span=12, adjust=False).mean()
    exp26 = c.ewm(span=26, adjust=False).mean()
    macd_line = exp12 - exp26
    sig_line = macd_line.ewm(span=9, adjust=False).mean()
    curr_macd = macd_line.iloc[-1]
    curr_sig = sig_line.iloc[-1]
    
    # 3. Bollinger
    sma20 = c.rolling(window=20).mean()
    std20 = c.rolling(window=20).std()
    upper = sma20 + (std20 * 2)
    lower = sma20 - (std20 * 2)
    curr_upper = upper.iloc[-1]
    curr_lower = lower.iloc[-1]
    
    # 4. Stochastic
    ll = l.rolling(window=14).min()
    hh = h.rolling(window=14).max()
    k_series = ((c - ll) / (hh - ll)) * 100
    d_series = k_series.rolling(window=3).mean()
    curr_k = k_series.iloc[-1]
    curr_d = d_series.iloc[-1]
    
    # 5. ADX
    tr1 = h - l
    tr2 = abs(h - c.shift(1))
    tr3 = abs(l - c.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    plus_di = 100 * (pd.Series(plus_dm, index=df_in.index).rolling(14).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df_in.index).rolling(14).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_series = dx.rolling(14).mean()
    curr_adx = adx_series.iloc[-1]

    score = 0
    signals = []
    
    # -- Logic --
    # RSI
    if curr_rsi < 30: score+=1.5; signals.append({"name":"RSI","val":f"{curr_rsi:.1f}","act":"BUY","desc":"Oversold"})
    elif curr_rsi > 70: score-=1.5; signals.append({"name":"RSI","val":f"{curr_rsi:.1f}","act":"SELL","desc":"Overbought"})
    else: signals.append({"name":"RSI","val":f"{curr_rsi:.1f}","act":"NEUTRAL","desc":"Neutral Zone"})
    
    # MACD
    if curr_macd > curr_sig: score+=1.5; signals.append({"name":"MACD","val":"Bull","act":"BUY","desc":"Bullish Crossover"})
    else: score-=1.5; signals.append({"name":"MACD","val":"Bear","act":"SELL","desc":"Bearish Crossover"})
    
    # Bollinger
    pct_b = (curr_close - curr_lower) / (curr_upper - curr_lower)
    if pct_b < 0.05: score+=1; signals.append({"name":"Bollinger","val":"Low","act":"BUY","desc":"Price near Lower Band"})
    elif pct_b > 0.95: score-=1; signals.append({"name":"Bollinger","val":"High","act":"SELL","desc":"Price near Upper Band"})
    else: signals.append({"name":"Bollinger","val":"Mid","act":"NEUTRAL","desc":"Within Bands"})
    
    # Stochastic
    if curr_k < 20: score+=1; signals.append({"name":"Stochastic","val":f"{curr_k:.0f}","act":"BUY","desc":"Oversold"})
    elif curr_k > 80: score-=1; signals.append({"name":"Stochastic","val":f"{curr_k:.0f}","act":"SELL","desc":"Overbought"})
    else: signals.append({"name":"Stochastic","val":f"{curr_k:.0f}","act":"NEUTRAL","desc":"Neutral"})
    
    # ADX (Trend Strength)
    trend_s = "Weak"
    if curr_adx > 25: trend_s = "Strong"
    if curr_adx > 50: trend_s = "Very Strong"
    signals.append({"name":"ADX","val":f"{curr_adx:.1f}","act":"INFO","desc":f"{trend_s} Trend"})
    
    # Final Score 0-100
    # Range is roughly -5 to +5. Center at 50.
    final_score = 50 + (score * 10)
    final_score = max(0, min(100, final_score))
    
    sentiment = "Neutral"
    if final_score >= 65: sentiment = "Bullish"
    if final_score >= 80: sentiment = "Strong Buy"
    if final_score <= 35: sentiment = "Bearish"
    if final_score <= 20: sentiment = "Strong Sell"

    return {
        "score": round(final_score, 1),
        "sentiment": sentiment,
        "signals": signals
    }

@app.route('/analyze/<symbol>', methods=['GET'])

def analyze(symbol):
    try:
        # 1. Fetch Data (1 Year to ensure enough data for EMA200)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", auto_adjust=True)

        if df.empty:
            return jsonify({"error": "No data found for symbol"}), 404

        # 2. Calculate Indicators (Manual Calculation using Pandas)
        close = df['Close']

        # EMA 200
        # EMA 200 & EMA 50
        df['EMA200'] = close.ewm(span=200, adjust=False).mean()
        df['EMA50'] = close.ewm(span=50, adjust=False).mean()

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
                "close": float(row['Close']),
                "volume": int(row['Volume']),
                "ema50": float(row['EMA50']) if not pd.isna(row['EMA50']) else None,
                "ema200": float(row['EMA200']) if not pd.isna(row['EMA200']) else None
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
            # --- EXTRACT FUNDAMENTALS ---
            fundamentals = {
                "valuation": {
                    "marketCap": info.get('marketCap'),
                    "trailingPE": info.get('trailingPE'),
                    "forwardPE": info.get('forwardPE'),
                    "pegRatio": info.get('pegRatio'),
                    "priceToBook": info.get('priceToBook'),
                    "priceToSales": info.get('priceToSalesTrailing12Months'),
                    "enterpriseValue": info.get('enterpriseValue'),
                    "trailingEps": info.get('trailingEps')
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
                    "recommendation": info.get('recommendationKey'),
                    "numberOfAnalysts": info.get('numberOfAnalystOpinions')
                }
            }

            # --- FAIR VALUE CALCULATION (Graham's Number Approximation) ---
            # V = Sqrt(22.5 * EPS * BVPS)
            fair_value = None
            try:
                eps = info.get('trailingEps')
                book_val = info.get('bookValue')
                if eps is not None and book_val is not None and eps > 0 and book_val > 0:
                     fair_value = (22.5 * eps * book_val) ** 0.5
            except:
                pass
            
            fundamentals['fairValue'] = fair_value

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
            
            
        # Calculate Technical Score (Detailed)
        tech_score_data = calculate_technical_score(df)

        result = {
            "symbol": symbol.upper(),
            "price": float(latest['Close']),
            "change": float(price_change),
            "change_percent": float(price_change_percent),
            "ema200": float(ema200),
            "rsi": rsi_val,
            "technical_analysis": tech_score_data, # Detailed Score
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

# --- SECTOR ROTATION ANALYSIS ---
# US Sector ETFs for analysis
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV", 
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication": "XLC"
}

@app.route('/sectors', methods=['GET'])
def sector_analysis():
    try:
        results = []
        symbols = list(SECTOR_ETFS.values())
        
        # Fetch all sector ETFs
        data = yf.download(symbols, period="3mo", group_by='ticker', progress=False, auto_adjust=True)
        
        for sector_name, symbol in SECTOR_ETFS.items():
            try:
                if len(symbols) > 1:
                    df = data[symbol].copy()
                else:
                    df = data.copy()
                
                if df.empty: continue
                df.dropna(subset=['Close'], inplace=True)
                
                close = df['Close']
                volume = df['Volume']
                
                if len(close) < 20: continue
                
                # Calculations
                current = float(close.iloc[-1])
                prev_day = float(close.iloc[-2]) if len(close) > 1 else current
                week_ago = float(close.iloc[-5]) if len(close) >= 5 else current
                month_ago = float(close.iloc[-22]) if len(close) >= 22 else current
                
                # Performance
                change_1d = ((current - prev_day) / prev_day) * 100
                change_1w = ((current - week_ago) / week_ago) * 100
                change_1m = ((current - month_ago) / month_ago) * 100
                
                # Volume analysis (money flow proxy)
                avg_vol = float(volume.tail(20).mean())
                current_vol = float(volume.iloc[-1])
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
                
                # Relative Strength (vs SPY)
                # Simplified: just use momentum score
                momentum = change_1w + (change_1m * 0.5)
                
                # Trend
                ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
                ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
                trend = "UP" if current > ema20 > ema50 else ("DOWN" if current < ema20 < ema50 else "SIDEWAYS")
                
                results.append({
                    "sector": sector_name,
                    "symbol": symbol,
                    "price": round(current, 2),
                    "change_1d": round(change_1d, 2),
                    "change_1w": round(change_1w, 2),
                    "change_1m": round(change_1m, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "momentum": round(momentum, 2),
                    "trend": trend
                })
                
            except Exception as e:
                print(f"Sector error {symbol}: {e}")
                continue
        
        # Sort by momentum (strongest first)
        results.sort(key=lambda x: x['momentum'], reverse=True)
        
        # Add rankings
        for i, r in enumerate(results):
            r['rank'] = i + 1
            if i < 3:
                r['status'] = "LEADING"
            elif i >= len(results) - 3:
                r['status'] = "LAGGING"
            else:
                r['status'] = "NEUTRAL"
        
        return jsonify({
            "sectors": results,
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Sector Analysis Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- VOLATILITY DASHBOARD ---
@app.route('/volatility', methods=['GET'])
def volatility_dashboard():
    try:
        # 1. VIX (Fear Index)
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="1mo")
        
        vix_current = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 0
        vix_prev = float(vix_hist['Close'].iloc[-2]) if len(vix_hist) > 1 else vix_current
        vix_change = ((vix_current - vix_prev) / vix_prev) * 100 if vix_prev > 0 else 0
        vix_high_30d = float(vix_hist['High'].max()) if not vix_hist.empty else 0
        vix_low_30d = float(vix_hist['Low'].min()) if not vix_hist.empty else 0
        
        # VIX interpretation
        if vix_current < 15:
            vix_status = "EXTREME GREED"
            vix_color = "#22c55e"
        elif vix_current < 20:
            vix_status = "LOW FEAR"
            vix_color = "#84cc16"
        elif vix_current < 25:
            vix_status = "NEUTRAL"
            vix_color = "#fbbf24"
        elif vix_current < 30:
            vix_status = "ELEVATED FEAR"
            vix_color = "#f97316"
        else:
            vix_status = "EXTREME FEAR"
            vix_color = "#ef4444"
        
        # 2. ATR Rankings (Top volatile stocks)
        atr_symbols = ['TSLA', 'NVDA', 'AMD', 'META', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'COIN', 'MSTR']
        atr_data = yf.download(atr_symbols, period="1mo", group_by='ticker', progress=False, auto_adjust=True)
        
        atr_results = []
        for sym in atr_symbols:
            try:
                if len(atr_symbols) > 1:
                    df = atr_data[sym].copy()
                else:
                    df = atr_data.copy()
                    
                if df.empty: continue
                df.dropna(inplace=True)
                
                high = df['High']
                low = df['Low']
                close = df['Close']
                
                # ATR Calculation (14-period)
                tr1 = high - low
                tr2 = abs(high - close.shift(1))
                tr3 = abs(low - close.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # ATR as % of price
                current_price = float(close.iloc[-1])
                atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
                
                # Daily range
                daily_range = ((float(high.iloc[-1]) - float(low.iloc[-1])) / float(low.iloc[-1])) * 100
                
                atr_results.append({
                    "symbol": sym,
                    "price": round(current_price, 2),
                    "atr": round(float(atr), 2),
                    "atr_pct": round(float(atr_pct), 2),
                    "daily_range": round(daily_range, 2)
                })
            except Exception as e:
                print(f"ATR error {sym}: {e}")
                continue
        
        # Sort by ATR%
        atr_results.sort(key=lambda x: x['atr_pct'], reverse=True)
        
        # 3. Market Breadth (simplified)
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="3mo")
        
        if not spy_hist.empty:
            spy_close = spy_hist['Close']
            spy_current = float(spy_close.iloc[-1])
            spy_ema20 = float(spy_close.ewm(span=20).mean().iloc[-1])
            spy_ema50 = float(spy_close.ewm(span=50).mean().iloc[-1])
            
            # Historical volatility (20-day)
            returns = spy_close.pct_change().dropna()
            hist_vol = float(returns.tail(20).std() * (252 ** 0.5) * 100)  # Annualized
            
            market_trend = "BULLISH" if spy_current > spy_ema20 > spy_ema50 else (
                "BEARISH" if spy_current < spy_ema20 < spy_ema50 else "MIXED"
            )
        else:
            spy_current = 0
            hist_vol = 0
            market_trend = "UNKNOWN"
        
        # 4. Put/Call Ratio (simulated - would need options data)
        # Using VIX as proxy
        pcr = round(vix_current / 20, 2)  # Simplified ratio
        
        return jsonify({
            "vix": {
                "current": round(vix_current, 2),
                "change": round(vix_change, 2),
                "high_30d": round(vix_high_30d, 2),
                "low_30d": round(vix_low_30d, 2),
                "status": vix_status,
                "color": vix_color
            },
            "atr_rankings": atr_results[:10],
            "market": {
                "spy_price": round(spy_current, 2),
                "hist_volatility": round(hist_vol, 2),
                "trend": market_trend,
                "pcr": pcr
            },
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Volatility Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- EARNINGS CALENDAR ---
@app.route('/earnings', methods=['GET'])
def earnings_calendar():
    try:
        # Major stocks to track earnings
        earnings_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
            'JPM', 'WMT', 'DIS', 'NFLX', 'AMD'
        ]
        
        results = []
        
        for symbol in earnings_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info or {}
                
                # Get basic info
                price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
                name = info.get('shortName', symbol)
                eps_ttm = info.get('trailingEps')
                eps_fwd = info.get('forwardEps')
                pe = info.get('trailingPE')
                
                # Try to get next earnings date
                next_earnings_str = None
                try:
                    cal = ticker.calendar
                    if cal is not None:
                        if isinstance(cal, dict) and 'Earnings Date' in cal:
                            ed = cal['Earnings Date']
                            if ed and len(ed) > 0:
                                next_earnings_str = str(ed[0])[:10]
                        elif hasattr(cal, 'columns') and 'Earnings Date' in cal.columns:
                            ed = cal['Earnings Date'].iloc[0] if len(cal) > 0 else None
                            if ed:
                                next_earnings_str = str(ed)[:10]
                except Exception as e:
                    print(f"Calendar error {symbol}: {e}")
                
                # Simple earnings history (mock if not available)
                recent_earnings = []
                try:
                    # Try earnings_dates instead
                    dates = ticker.earnings_dates
                    if dates is not None and len(dates) > 0:
                        for idx, row in dates.head(4).iterrows():
                            eps_a = row.get('Reported EPS')
                            eps_e = row.get('EPS Estimate')
                            # Check for NaN and None
                            if eps_a is not None and eps_e is not None:
                                try:
                                    eps_a = float(eps_a)
                                    eps_e = float(eps_e)
                                    # Skip if NaN
                                    if pd.isna(eps_a) or pd.isna(eps_e):
                                        continue
                                    surp = eps_a - eps_e
                                    surp_pct = (surp / abs(eps_e) * 100) if eps_e != 0 else 0
                                    beat = eps_a > eps_e
                                    recent_earnings.append({
                                        "quarter": str(idx)[:10],
                                        "eps_actual": round(eps_a, 3),
                                        "eps_estimate": round(eps_e, 3),
                                        "surprise": round(surp, 3),
                                        "surprise_pct": round(surp_pct, 2),
                                        "beat": beat
                                    })
                                except:
                                    pass
                except Exception as e:
                    print(f"Earnings dates error {symbol}: {e}")
                
                # Beat rate
                beats = [e for e in recent_earnings if e.get('beat') == True]
                beat_rate = (len(beats) / len(recent_earnings) * 100) if recent_earnings else 50
                
                # Safe number conversion
                def safe_float(val, decimals=2):
                    if val is None:
                        return None
                    try:
                        f = float(val)
                        if pd.isna(f):
                            return None
                        return round(f, decimals)
                    except:
                        return None
                
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "price": safe_float(price, 2) or 0,
                    "next_earnings": next_earnings_str,
                    "earnings_history": recent_earnings,
                    "beat_rate": round(beat_rate, 0),
                    "eps_ttm": safe_float(eps_ttm, 2),
                    "eps_fwd": safe_float(eps_fwd, 2),
                    "pe": safe_float(pe, 1)
                })
                
            except Exception as e:
                print(f"Earnings error {symbol}: {e}")
                # Add minimal entry even on error
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "price": 0,
                    "next_earnings": None,
                    "earnings_history": [],
                    "beat_rate": 0,
                    "eps_ttm": None,
                    "eps_fwd": None,
                    "pe": None
                })
        
        return jsonify({
            "earnings": results,
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Earnings Calendar Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- DIVIDEND TRACKER ---
@app.route('/dividends/<symbol>', methods=['GET'])
def get_dividends(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info or {}
        
        # Safe float helper
        def safe_num(val, decimals=2):
            if val is None: return None
            try:
                f = float(val)
                return None if pd.isna(f) else round(f, decimals)
            except: return None
        
        # Get dividend info
        div_yield = safe_num(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0
        div_rate = safe_num(info.get('dividendRate'), 2)
        payout_ratio = safe_num(info.get('payoutRatio', 0) * 100, 1) if info.get('payoutRatio') else None
        ex_div_date = info.get('exDividendDate')
        
        # Format ex-dividend date
        if ex_div_date:
            from datetime import datetime as dt
            try:
                ex_div_str = dt.fromtimestamp(ex_div_date).strftime('%Y-%m-%d')
            except:
                ex_div_str = str(ex_div_date)
        else:
            ex_div_str = None
        
        # Get dividend history
        div_history = []
        try:
            divs = ticker.dividends
            if divs is not None and len(divs) > 0:
                for date, amount in divs.tail(12).items():
                    if not pd.isna(amount):
                        div_history.append({
                            "date": str(date.date()),
                            "amount": round(float(amount), 4)
                        })
        except Exception as e:
            print(f"Dividend history error: {e}")
        
        # Calculate annual dividend
        annual_div = sum([d['amount'] for d in div_history[-4:]]) if len(div_history) >= 4 else (div_rate or 0)
        
        price = safe_num(info.get('currentPrice') or info.get('regularMarketPrice'), 2)
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "price": price or 0,
            "dividend_yield": div_yield,
            "dividend_rate": div_rate,
            "annual_dividend": round(annual_div, 2),
            "payout_ratio": payout_ratio,
            "ex_dividend_date": ex_div_str,
            "dividend_history": div_history,
            "frequency": "Quarterly" if len(div_history) >= 4 else "Annual",
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Dividend Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- INSTITUTIONAL OWNERSHIP ---
@app.route('/institutional/<symbol>', methods=['GET'])
def get_institutional(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info or {}
        
        def safe_num(val, decimals=2):
            if val is None: return None
            try:
                f = float(val)
                return None if pd.isna(f) else round(f, decimals)
            except: return None
        
        # Get major holders
        major_holders = []
        try:
            mh = ticker.major_holders
            if mh is not None and len(mh) > 0:
                for idx, row in mh.iterrows():
                    major_holders.append({
                        "value": str(row.iloc[0]),
                        "description": str(row.iloc[1]) if len(row) > 1 else ""
                    })
        except Exception as e:
            print(f"Major holders error: {e}")
        
        # Get institutional holders
        inst_holders = []
        try:
            ih = ticker.institutional_holders
            if ih is not None and len(ih) > 0:
                for idx, row in ih.head(10).iterrows():
                    shares = row.get('Shares')
                    value = row.get('Value')
                    inst_holders.append({
                        "holder": str(row.get('Holder', 'Unknown')),
                        "shares": int(shares) if shares and not pd.isna(shares) else 0,
                        "value": int(value) if value and not pd.isna(value) else 0,
                        "pct_out": safe_num(row.get('pctHeld', 0) * 100, 2) if row.get('pctHeld') else None
                    })
        except Exception as e:
            print(f"Institutional holders error: {e}")
        
        # Insider transactions
        insider_trans = []
        try:
            it = ticker.insider_transactions
            if it is not None and len(it) > 0:
                for idx, row in it.head(10).iterrows():
                    insider_trans.append({
                        "insider": str(row.get('Insider', 'Unknown')),
                        "relation": str(row.get('Relation', '')),
                        "shares": int(row.get('Shares', 0)) if not pd.isna(row.get('Shares', 0)) else 0,
                        "transaction": str(row.get('Transaction', '')),
                        "date": str(row.get('Start Date', ''))[:10] if row.get('Start Date') else ''
                    })
        except Exception as e:
            print(f"Insider transactions error: {e}")
        
        inst_ownership = safe_num(info.get('heldPercentInstitutions', 0) * 100, 2) if info.get('heldPercentInstitutions') else 0
        insider_ownership = safe_num(info.get('heldPercentInsiders', 0) * 100, 2) if info.get('heldPercentInsiders') else 0
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "institutional_ownership": inst_ownership,
            "insider_ownership": insider_ownership,
            "major_holders": major_holders,
            "top_institutions": inst_holders,
            "insider_transactions": insider_trans,
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Institutional Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- INSIDER TRADING TRACKER ---
@app.route('/insider-tracker/<symbol>', methods=['GET'])
def insider_tracker(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info or {}
        
        insider_trans = []
        try:
            insider_data = ticker.insider_transactions
            if insider_data is not None and len(insider_data) > 0:
                for idx, row in insider_data.head(50).iterrows():
                    try:
                        trans_type = str(row.get('Transaction', '')).lower()
                        shares = int(row.get('Shares', 0)) if row.get('Shares') else 0
                        value = int(row.get('Value', 0)) if row.get('Value') else 0
                        
                        is_buy = 'buy' in trans_type or 'purchase' in trans_type
                        is_sell = 'sell' in trans_type or 'sale' in trans_type
                        
                        insider_trans.append({
                            "date": str(row.get('Start Date', ''))[:10],
                            "insider": str(row.get('Insider', 'Unknown')),
                            "relation": str(row.get('Relation', '')),
                            "transaction": str(row.get('Transaction', '')),
                            "shares": shares,
                            "value": value,
                            "is_buy": is_buy,
                            "is_sell": is_sell
                        })
                    except:
                        continue
        except Exception as e:
            print(f"Insider trans error: {e}")
        
        # Analysis
        recent_10 = insider_trans[:10]
        buys = sum(1 for t in recent_10 if t['is_buy'])
        sells = sum(1 for t in recent_10 if t['is_sell'])
        
        sentiment = "Bullish" if buys > sells else "Bearish" if sells > buys else "Neutral"
        sentiment_color = "#22c55e" if buys > sells else "#ef4444" if sells > buys else "#fbbf24"
        
        # Cluster detection
        cluster = buys >= 3
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "transactions": insider_trans,
            "analysis": {
                "sentiment": sentiment,
                "sentiment_color": sentiment_color,
                "buys_10d": buys,
                "sells_10d": sells,
                "cluster_detected": cluster
            }
        })
    except Exception as e:
        print(f"Insider Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- DARK POOL TRACKER ---
@app.route('/darkpool', methods=['GET'])
def dark_pool_tracker():
    try:
        symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN', 'META', 'AMD', 'NFLX', 'DIS']
        results = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1mo")
                
                if len(hist) < 5:
                    continue
                
                avg_vol = hist['Volume'].mean()
                recent_vol = hist['Volume'].iloc[-1]
                ratio = recent_vol / avg_vol if avg_vol > 0 else 0
                
                if ratio > 1.5:  # 50% above average
                    results.append({
                        "symbol": symbol,
                        "date": str(hist.index[-1].date()),
                        "volume": int(recent_vol),
                        "avg_volume": int(avg_vol),
                        "ratio": round(ratio, 2),
                        "price": round(hist['Close'].iloc[-1], 2),
                        "change_pct": round((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100, 2)
                    })
            except:
                continue
        
        results.sort(key=lambda x: x['ratio'], reverse=True)
        return jsonify({"unusual_volume": results[:15]})
    except Exception as e:
        print(f"Darkpool Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- NEWS SENTIMENT ---
@app.route('/sentiment/<symbol>', methods=['GET'])
def get_sentiment(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info or {}
        
        # Positive and negative keywords
        positive_words = ['surge', 'jump', 'gain', 'rise', 'rally', 'beat', 'upgrade', 'buy', 
                          'bullish', 'growth', 'profit', 'success', 'breakthrough', 'outperform',
                          'soar', 'strong', 'record', 'positive', 'boost', 'win', 'up', 'high']
        negative_words = ['fall', 'drop', 'decline', 'loss', 'miss', 'downgrade', 'sell',
                          'bearish', 'risk', 'warning', 'crash', 'cut', 'lawsuit', 'investigation',
                          'plunge', 'weak', 'down', 'negative', 'concern', 'fear', 'tumble', 'low']
        
        news_items = []
        total_sentiment = 0
        
        # Try yfinance news first
        try:
            news = ticker.news
            print(f"yfinance news for {symbol}: {len(news) if news else 0} items")
            if news:
                for item in news[:10]:
                    title = item.get('title', '') or ''
                    link = item.get('link', '') or ''
                    publisher = item.get('publisher', '') or 'Unknown'
                    pub_time = item.get('providerPublishTime', 0) or 0
                    
                    # Skip empty titles
                    if not title.strip():
                        continue
                    
                    # Simple sentiment analysis
                    title_lower = title.lower()
                    pos_count = sum(1 for w in positive_words if w in title_lower)
                    neg_count = sum(1 for w in negative_words if w in title_lower)
                    
                    if pos_count > neg_count:
                        sentiment = "positive"
                        score = min((pos_count - neg_count) * 25, 100)
                    elif neg_count > pos_count:
                        sentiment = "negative"
                        score = -min((neg_count - pos_count) * 25, 100)
                    else:
                        sentiment = "neutral"
                        score = 0
                    
                    total_sentiment += score
                    
                    # Format date
                    date_str = ""
                    if pub_time > 0:
                        try:
                            from datetime import datetime as dt
                            date_str = dt.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
                        except:
                            pass
                    
                    news_items.append({
                        "title": title,
                        "link": link,
                        "publisher": publisher,
                        "date": date_str,
                        "sentiment": sentiment,
                        "score": score
                    })
        except Exception as e:
            print(f"yfinance news error: {e}")
        
        # Fallback: Try Google News RSS if no valid news
        if len(news_items) < 3:
            print(f"Trying Google News RSS for {symbol}...")
            try:
                import urllib.request
                from xml.etree import ElementTree
                
                company_name = info.get('shortName', symbol)
                if company_name:
                    company_name = company_name.split()[0]  # First word only
                rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
                
                req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as response:
                    xml_data = response.read()
                    root = ElementTree.fromstring(xml_data)
                    
                    for item in root.findall('.//item')[:10]:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        pub_elem = item.find('pubDate')
                        source_elem = item.find('source')
                        
                        title = title_elem.text if title_elem is not None and title_elem.text else ''
                        link = link_elem.text if link_elem is not None and link_elem.text else ''
                        pub_date = pub_elem.text if pub_elem is not None and pub_elem.text else ''
                        source = source_elem.text if source_elem is not None and source_elem.text else 'Google News'
                        
                        # Skip empty titles
                        if not title.strip():
                            continue
                        
                        # Sentiment analysis
                        title_lower = title.lower()
                        pos_count = sum(1 for w in positive_words if w in title_lower)
                        neg_count = sum(1 for w in negative_words if w in title_lower)
                        
                        if pos_count > neg_count:
                            sentiment = "positive"
                            score = min((pos_count - neg_count) * 25, 100)
                        elif neg_count > pos_count:
                            sentiment = "negative"
                            score = -min((neg_count - pos_count) * 25, 100)
                        else:
                            sentiment = "neutral"
                            score = 0
                        
                        total_sentiment += score
                        
                        # Parse date (format: "Sat, 14 Dec 2024 15:30:00 GMT")
                        date_display = pub_date[:16] if pub_date else ""
                        
                        news_items.append({
                            "title": title,
                            "link": link,
                            "publisher": source,
                            "date": date_display,
                            "sentiment": sentiment,
                            "score": score
                        })
                print(f"Got {len(news_items)} news from Google RSS")
            except Exception as e:
                print(f"Google News RSS error: {e}")
        
        # Calculate overall sentiment
        if news_items:
            avg_sentiment = total_sentiment / len(news_items)
            if avg_sentiment > 20:
                overall = "Bullish"
                overall_color = "#22c55e"
            elif avg_sentiment < -20:
                overall = "Bearish"
                overall_color = "#ef4444"
            else:
                overall = "Neutral"
                overall_color = "#fbbf24"
        else:
            avg_sentiment = 0
            overall = "No Data"
            overall_color = "#6b7280"
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "overall_sentiment": overall,
            "sentiment_score": round(avg_sentiment, 1),
            "sentiment_color": overall_color,
            "news_count": len(news_items),
            "news": news_items,
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Sentiment Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- AI PRICE PREDICTION ---
@app.route('/predict/<symbol>', methods=['GET'])
def predict_price(symbol):
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info or {}
        
        # Get historical data
        hist = ticker.history(period="3mo")
        if hist.empty or len(hist) < 30:
            return jsonify({"error": "Insufficient data for prediction"}), 400
        
        close = hist['Close']
        
        def safe_num(val, decimals=2):
            if val is None: return None
            try:
                f = float(val)
                return None if pd.isna(f) else round(f, decimals)
            except: return None
        
        # Current price
        current_price = float(close.iloc[-1])
        
        # Calculate indicators for prediction
        # 1. Linear Trend (simple slope)
        x = np.arange(len(close))
        y = close.values
        slope, intercept = np.polyfit(x, y, 1)
        trend_direction = "UP" if slope > 0 else "DOWN"
        
        # 2. Moving averages
        ma5 = close.rolling(5).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        
        # 3. Volatility (std dev)
        volatility = close.pct_change().std() * np.sqrt(252) * 100  # Annualized
        
        # 4. Momentum (rate of change)
        roc = ((close.iloc[-1] / close.iloc[-20]) - 1) * 100
        
        # Simple prediction: project trend forward
        predictions = []
        base_price = current_price
        daily_change = slope
        
        for day in range(1, 8):
            pred_price = base_price + (daily_change * day)
            # Add some variance based on volatility
            predictions.append({
                "day": day,
                "price": round(pred_price, 2),
                "low": round(pred_price * (1 - volatility/100/10), 2),
                "high": round(pred_price * (1 + volatility/100/10), 2)
            })
        
        # Confidence score (based on trend strength and volatility)
        trend_strength = abs(roc)
        confidence = max(20, min(90, 70 - volatility + trend_strength))
        
        # Prediction summary
        predicted_7d = predictions[-1]['price']
        change_pct = ((predicted_7d / current_price) - 1) * 100
        
        if change_pct > 3:
            signal = "STRONG BUY"
            signal_color = "#22c55e"
        elif change_pct > 1:
            signal = "BUY"
            signal_color = "#4ade80"
        elif change_pct < -3:
            signal = "STRONG SELL"
            signal_color = "#ef4444"
        elif change_pct < -1:
            signal = "SELL"
            signal_color = "#f87171"
        else:
            signal = "HOLD"
            signal_color = "#fbbf24"
        
        return jsonify({
            "symbol": symbol.upper(),
            "name": info.get('shortName', symbol),
            "current_price": round(current_price, 2),
            "predictions": predictions,
            "predicted_7d": round(predicted_7d, 2),
            "change_pct": round(change_pct, 2),
            "trend": trend_direction,
            "volatility": round(volatility, 2),
            "momentum": round(roc, 2),
            "confidence": round(confidence, 0),
            "signal": signal,
            "signal_color": signal_color,
            "ma5": safe_num(ma5, 2),
            "ma20": safe_num(ma20, 2),
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- STOCK COMPARISON TOOL ---
@app.route('/compare', methods=['POST'])
def compare_stocks():
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols or len(symbols) < 2:
            return jsonify({"error": "Please provide at least 2 symbols"}), 400
        
        if len(symbols) > 5:
            return jsonify({"error": "Maximum 5 symbols allowed"}), 400
        
        def safe_num(val, decimals=2):
            if val is None: return None
            try:
                f = float(val)
                return None if pd.isna(f) else round(f, decimals)
            except: return None
        
        results = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol.upper())
                info = ticker.info or {}
                hist = ticker.history(period="1y")
                
                if hist.empty:
                    results.append({
                        "symbol": symbol.upper(),
                        "error": "No data available"
                    })
                    continue
                
                # Price data
                current_price = safe_num(info.get('currentPrice') or info.get('regularMarketPrice'), 2)
                
                # Valuation
                pe = safe_num(info.get('trailingPE'), 2)
                pb = safe_num(info.get('priceToBook'), 2)
                peg = safe_num(info.get('pegRatio'), 2)
                ps = safe_num(info.get('priceToSalesTrailing12Months'), 2)
                
                # Profitability
                roe = safe_num(info.get('returnOnEquity', 0) * 100, 2) if info.get('returnOnEquity') else None
                roe_percent = safe_num(info.get('returnOnAssets', 0) * 100, 2) if info.get('returnOnAssets') else None
                profit_margin = safe_num(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else None
                
                # Growth
                revenue_growth = safe_num(info.get('revenueGrowth', 0) * 100, 1) if info.get('revenueGrowth') else None
                earnings_growth = safe_num(info.get('earningsGrowth', 0) * 100, 1) if info.get('earningsGrowth') else None
                
                # Dividend
                dividend_yield = safe_num(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else None
                payout_ratio = safe_num(info.get('payoutRatio', 0) * 100, 1) if info.get('payoutRatio') else None
                
                # Financials
                market_cap = info.get('marketCap', 0)
                debt_to_equity = safe_num(info.get('debtToEquity'), 2)
                current_ratio = safe_num(info.get('currentRatio'), 2)
                
                # Performance
                ytd_return = None
                if len(hist) > 0:
                    year_start = hist[hist.index >= f"{datetime.now().year}-01-01"]
                    if len(year_start) > 1:
                        ytd_return = safe_num((year_start['Close'].iloc[-1] / year_start['Close'].iloc[0] - 1) * 100, 2)
                
                one_year_return = None
                if len(hist) >= 252:
                    one_year_return = safe_num((hist['Close'].iloc[-1] / hist['Close'].iloc[-252] - 1) * 100, 2)
                
                # Technical
                volatility = safe_num(hist['Close'].pct_change().std() * np.sqrt(252) * 100, 2)
                beta = safe_num(info.get('beta'), 2)
                
                # RSI calculation
                rsi = None
                if len(hist) >= 14:
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_series = 100 - (100 / (1 + rs))
                    rsi = safe_num(rsi_series.iloc[-1], 1)
                
                # Analyst recommendation
                recommendation = info.get('recommendationKey', 'N/A')
                target_price = safe_num(info.get('targetMeanPrice'), 2)
                
                results.append({
                    "symbol": symbol.upper(),
                    "name": info.get('shortName', symbol),
                    
                    # Price
                    "price": current_price or 0,
                    
                    # Valuation
                    "pe": pe,
                    "pb": pb,
                    "peg": peg,
                    "ps": ps,
                    
                    # Profitability
                    "roe": roe,
                    "roa": roe_percent,
                    "profit_margin": profit_margin,
                    
                    # Growth
                    "revenue_growth": revenue_growth,
                    "earnings_growth": earnings_growth,
                    
                    # Dividend
                    "dividend_yield": dividend_yield,
                    "payout_ratio": payout_ratio,
                    
                    # Financials
                    "market_cap": market_cap,
                    "debt_to_equity": debt_to_equity,
                    "current_ratio": current_ratio,
                    
                    # Performance
                    "ytd_return": ytd_return,
                    "one_year_return": one_year_return,
                    
                    # Technical
                    "volatility": volatility,
                    "beta": beta,
                    "rsi": rsi,
                    
                    # Analyst
                    "recommendation": recommendation,
                    "target_price": target_price,
                    
                    # Historical prices for chart
                    "history": [
                        {"date": str(d.date()), "price": round(float(p), 2)}
                        for d, p in hist['Close'].tail(90).items()
                    ]
                })
                
            except Exception as e:
                print(f"Comparison error for {symbol}: {e}")
                results.append({
                    "symbol": symbol.upper(),
                    "error": str(e)
                })
        
        return jsonify({
            "stocks": results,
            "updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Compare Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- FINANCIAL CALENDAR ---
@app.route('/calendar', methods=['GET'])
def financial_calendar():
    try:
        events = []
        
        # 1. ECONOMIC EVENTS (Manual/Curated)
        economic_events = [
            {
                "type": "economic",
                "title": "FOMC Meeting",
                "date": "2024-12-18",
                "time": "14:00",
                "importance": "critical",
                "description": "Federal Reserve Interest Rate Decision"
            },
            {
                "type": "economic",
                "title": "Non-Farm Payrolls",
                "date": "2025-01-03",
                "time": "08:30",
                "importance": "critical",
                "description": "US Employment Report"
            },
            {
                "type": "economic",
                "title": "CPI Report",
                "date": "2025-01-15",
                "time": "08:30",
                "importance": "high",
                "description": "Consumer Price Index"
            },
            {
                "type": "economic",
                "title": "GDP Report",
                "date": "2025-01-25",
                "time": "08:30",
                "importance": "high",
                "description": "Q4 GDP Growth"
            }
        ]
        
        events.extend(economic_events)
        
        # 2. Simplified earnings placeholders
        earnings_events = [
            {"type": "earnings", "symbol": "AAPL", "title": "AAPL Earnings Report", "date": "2025-01-30", "time": "", "importance": "high", "company": "Apple Inc."},
            {"type": "earnings", "symbol": "MSFT", "title": "MSFT Earnings Report", "date": "2025-01-28", "time": "", "importance": "high", "company": "Microsoft"},
            {"type": "earnings", "symbol": "GOOGL", "title": "GOOGL Earnings Report", "date": "2025-02-04", "time": "", "importance": "high", "company": "Alphabet"},
        ]
        
        events.extend(earnings_events)
        
        # Sort by date
        events.sort(key=lambda x: x['date'])
        
        return jsonify({
            "events": events,
            "start_date": datetime.now().strftime('%Y-%m-%d'),
            "end_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "total_events": len(events)
        })
        
    except Exception as e:
        print(f"Calendar Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/screen', methods=['GET'])
def screen_stocks():
    try:
        # Predefined Watchlist (Major US & Thai Stocks)
        symbols = MASTER_WATCHLIST
        
        # Bulk Fetch (1 Year history for EMA200)
        # yfinance.download can handle multiple tickers
        print(f"Scanning {len(symbols)} stocks...")
        data = yf.download(symbols, period="1y", group_by='ticker', progress=False, auto_adjust=True)
        
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

@app.route('/backtest', methods=['POST'])
def backtest_stock():
    try:
        req_data = request.json
        symbol = req_data.get('symbol')
        params = req_data.get('params', {})
        
        # Strategy Parameters
        p_rsi_buy = float(params.get('rsi_buy', 30))
        p_rsi_sell = float(params.get('rsi_sell', 70))
        p_stop_loss = float(params.get('stop_loss', 5)) / 100.0 # Convert 5 to 0.05
        # p_take_profit = float(params.get('take_profit', 0)) # Not used yet in old logic but good to have
        
        # Fetch 2 Years of data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", auto_adjust=True)
        
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
            
            # Logic (Parameterized)
            is_uptrend = price > row['EMA200']
            macd_bull = row['MACD_Line'] > row['MACD_Signal']
            rsi = row['RSI']
            
            # SIGNAL GENERATION
            action = "WAIT"
            
            # BUY Logic
            if position == 0:
                # Require Uptrend AND RSI < BUY_THRESHOLD AND MACD Bull
                if is_uptrend:
                    if (rsi > p_rsi_buy and rsi < 55) and macd_bull:
                        action = "BUY"
            
            # SELL Logic
            elif position > 0:
                # Stop Loss
                pct_change = (price - entry_price) / entry_price
                
                if pct_change < -p_stop_loss: # Stop Loss
                    action = "SELL"
                elif not is_uptrend and rsi > 50: # Trend Broken
                    action = "SELL"
                elif rsi > p_rsi_sell: # Take Profit / Overbought
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
            "equity_curve": equity_curve, 
            "trades": trades[-5:]
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
        watchlist = MASTER_WATCHLIST
        
        # Bulk Fetch (1mo is enough for Trend + RSI) - OPTIMIZED SPEED
        print("Fetching Discovery Data...")
        数据 = yf.download(watchlist, period="1mo", group_by='ticker', progress=False, auto_adjust=True)
        data = 数据 # Just preventing variable rename issue if any

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

def analyze_streaks():
    """
    Analyzes watchlist for consecutive daily streaks (Up/Down).
    Returns lists of gainers and losers.
    """
    try:
        watchlist = MASTER_WATCHLIST
        
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

@app.route('/heatmap', methods=['GET'])
def get_heatmap():
    try:
        # Download 2 days to calculate % change
        # Using period="2d" is safer to get prev close
        # group_by='ticker' ensures data[symbol] is a DataFrame
        data = yf.download(MASTER_WATCHLIST, period="2d", group_by='ticker', auto_adjust=True, progress=False)
        
        heatmap_data = []
        
        for symbol in MASTER_WATCHLIST:
            try:
                # Handle DataFrame lookup
                if len(MASTER_WATCHLIST) > 1:
                    if symbol not in data.columns.levels[0]: continue
                    df_sym = data[symbol]
                else:
                    df_sym = data # If only 1 symbol
                
                if df_sym.empty or len(df_sym) < 2:
                    continue
                
                # Calculate Change
                # Handle cases where data is missing for some days
                df_sym = df_sym.dropna(subset=['Close'])
                if len(df_sym) < 2: continue

                prev_close = df_sym['Close'].iloc[-2]
                curr_close = df_sym['Close'].iloc[-1]
                change_pct = ((curr_close - prev_close) / prev_close) * 100
                
                # Mock Sector/MarketCap proxies
                sector = "Other"
                if ".BK" in symbol: sector = "Thailand"
                elif "USD" in symbol: sector = "Crypto"
                elif ".T" in symbol: sector = "Japan"
                elif ".HK" in symbol: sector = "China"
                elif symbol in ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN"]: sector = "US Tech"
                
                # Market Cap Proxy: Volume * Price (Daily Turnover)
                # Since we don't have Market Cap in history
                if 'Volume' in df_sym.columns:
                    vol = df_sym['Volume'].iloc[-1]
                    turnover = vol * curr_close
                else: 
                    turnover = 1000000 # Default

                heatmap_data.append({
                    "symbol": symbol,
                    "change": round(change_pct, 2),
                    "sector": sector,
                    "value": turnover, 
                    "price": round(curr_close, 2)
                })
            except Exception as e:
                continue
        
        # Sort by Value (Size) descending
        heatmap_data.sort(key=lambda x: x['value'], reverse=True)
        return jsonify(heatmap_data)

    except Exception as e:
        print(f"Heatmap Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/heatmap_view')
def heatmap_page():
    return app.send_static_file('heatmap.html')

@app.route('/trends')
def trends_page():
    return app.send_static_file('trends.html')

if __name__ == '__main__':
    print("Stockify Data Server Running on port 5000...")
    app.run(debug=True, port=5000)