class TranslationManager {
    constructor() {
        this.currentLang = localStorage.getItem('app_lang') || 'en';
        this.translations = {
            "en": {
                // Nav
                "nav_analyzer": "📊 Analyzer",
                "nav_screener": "🔍 Screener",
                "nav_trends": "🔥 Trends",
                "nav_portfolio": "💼 Portfolio",

                // Common
                "loading": "Loading...",
                "error": "Error",
                "refresh": "Refresh",
                "btn_analyze": "Analyze",
                "btn_buy": "Buy",
                "btn_sell": "Sell",
                "search_placeholder": "🔍 Search Symbol (e.g. AAPL, PTT.BK)",
                "search_tips": "💡 Tips: Type <strong>any</strong> symbol! (e.g., AAPL, 7203.T, 0700.HK, BTC-USD). Use <strong>.BK</strong> for Thai stocks.",
                "favorites": "Favorites ⭐",
                "add_fav": "Add to Favorites",
                "rem_fav": "Remove from Favorites",
                "no_favs": "No favorites yet. Star some stocks! ⭐",

                // Headers
                "analyzer_title": "Stockify Pro 🤖",
                "analyzer_sub": "AI-Powered Technical Analysis Assistant",
                "screener_title": "Stock Screener 🔍",
                "screener_sub": "Filter stocks based on technical signals",
                "trends_title": "Market Trends 🚀",
                "trends_sub": "Identify stocks with consistent consecutive movements",
                "portfolio_title": "Stockify Pro 💼",
                "portfolio_sub": "Your Virtual Portfolio",

                // Table Columns
                "col_symbol": "Symbol",
                "col_price": "Price",
                "col_change": "Change",
                "col_trend": "Trend",
                "col_rsi": "RSI",
                "col_signal": "Signal",
                "col_action": "Action",
                "col_qty": "Qty",
                "col_avg_price": "Avg Price",
                "col_value": "Value",
                "col_pl": "P/L",
                "col_scenario": "Scenario",
                "col_target": "Target Price",
                "col_upside": "% Upside",
                "col_future_val": "Future Value",

                // Trends Page
                "trend_scanning": "Scanning Sequences...",
                "trend_win": "Winning Streaks",
                "trend_win_desc": "Stocks closing HIGHER than the previous day for 3+ consecutive days.",
                "trend_lose": "Losing Streaks",
                "trend_lose_desc": "Stocks closing LOWER than the previous day for 3+ consecutive days.",
                "trend_no_data": "No streaks found.",

                // Screener Page
                "scan_results": "Market Scan Results",
                "scan_loading": "Scanning Market...",
                "scan_connect_fail": "Connection Failed",

                // Portfolio Page
                "total_balance": "Total Balance (Cash + Equity)",
                "avail_cash": "Available Cash",
                "reset_pf": "Reset Portfolio ⚠️",
                "curr_holdings": "Current Holdings",
                "trade_history": "Trade History",
                "no_history": "No trade history found.",
                "fetching_prices": "Fetching Live Prices... ⏳",
                "no_positions": "No open positions. Go to Analyzer to buy stocks! 🚀",

                // Analyzer / Stats
                "stat_open": "Open",
                "stat_high": "High",
                "stat_low": "Low",
                "stat_prev": "Prev Close",
                "comp_profile": "Company Profile",
                "comp_holders": "Major Shareholders",
                "inv_projector": "Investment Projector",
                "lbl_budget": "Budget",
                "lbl_duration": "Duration",
                "lbl_days": "Days",
                "lbl_months": "Months",
                "lbl_years": "Years",
                "disclaimer": "*Calculations based on Analyst Consensus Targets. Not financial advice.",

                // Trading Panel
                "paper_trading": "Paper Trading",
                "submit_order": "Submit Order 🚀",
                "lbl_qty": "Quantity",
                "lbl_action": "Action",
                "action_buy": "🟢 BUY (Long)",
                "action_sell": "🔴 SELL (Short/Close)",
                "trend_up": "UP",
                "trend_down": "DOWN",
                "trend_side": "SIDEWAYS",

                // Calculator & App
                "scen_bear": "🏰 Bear Case",
                "scen_base": "⚖️ Base Case",
                "scen_bull": "🚀 Bull Case",
                "err_search_first": "❌ Please search for a stock first.",
                "err_invalid_price": "❌ Invalid Price Data.",
                "sig_buy": "BUY",
                "sig_sell": "SELL",
                "sig_wait": "WAIT",

                // Fundamentals
                "fund_title": "Fundamental Radar 📊",
                "fund_fair_value": "Fair Value (Graham)",
                "fund_pe": "P/E Ratio",
                "fund_pb": "P/B Ratio",
                "fund_roe": "ROE",
                "fund_eps": "EPS",
                "fund_debt_eq": "Debt/Equity",
                "fund_undervalued": "Undervalued",
                "fund_overvalued": "Overvalued",

                // Technical Scorecard
                "tech_title": "Technical Scorecard 📝",
                "tech_score": "Technical Score",
                "tech_indicator": "Indicator",
                "tech_value": "Value",
                "tech_action": "Action",
                "tech_desc": "Description",

                // Sectors Page
                "nav_sectors": "🔄 Sectors",
                "sectors_title": "Sector Rotation Analysis 🔄",
                "sectors_sub": "Track money flow across market sectors",
                "sect_leading": "Leading (Top 3)",
                "sect_neutral": "Neutral",
                "sect_lagging": "Lagging (Bottom 3)",
                "sect_strongest": "Strongest Sector",
                "sect_avg_mom": "Avg Momentum",
                "sect_mkt_trend": "Market Trend",
                "sect_1d": "1 Day",
                "sect_1w": "1 Week",
                "sect_1m": "1 Month",
                "sect_volume": "Volume Ratio",
                "sect_momentum": "Momentum",

                // Volatility Page
                "nav_volatility": "⚡ Volatility",
                "vol_title": "Volatility Dashboard ⚡",
                "vol_sub": "Market Fear & Volatility Metrics",
                "vol_vix": "CBOE Volatility Index (VIX)",
                "vol_fear_meter": "Fear & Greed Meter",
                "vol_fear_score": "Fear Score (based on VIX)",
                "vol_market_overview": "Market Overview",
                "vol_spy_price": "SPY Price",
                "vol_hist_vol": "Historical Vol (20D)",
                "vol_market_trend": "Market Trend",
                "vol_pcr": "P/C Ratio (Proxy)",
                "vol_atr_ranking": "Most Volatile Stocks (ATR Ranking)",
                "vol_atr": "ATR ($)",
                "vol_atr_pct": "ATR %",
                "vol_daily_range": "Daily Range",
                "vol_extreme_greed": "EXTREME GREED",
                "vol_low_fear": "LOW FEAR",
                "vol_neutral": "NEUTRAL",
                "vol_elevated_fear": "ELEVATED FEAR",
                "vol_extreme_fear": "EXTREME FEAR",

                // Heatmap
                "nav_heatmap": "🗺️ Heatmap",
                "heatmap_title": "Market Heatmap 🗺️",
                "heatmap_sub": "Visual overview of market sectors",

                // Earnings Calendar
                "nav_earnings": "📅 Earnings",
                "earnings_title": "Earnings Calendar 📅",
                "earnings_sub": "Track earnings announcements and historical performance",
                "earnings_next": "Next Earnings",
                "earnings_beat_rate": "Beat Rate",
                "earnings_eps_ttm": "EPS (TTM)",
                "earnings_eps_fwd": "EPS (Fwd)",
                "earnings_pe": "P/E Ratio",
                "earnings_recent": "Recent Quarters",

                // Advanced Analysis
                "nav_advanced": "🧠 Advanced",
                "advanced_title": "Advanced Stock Analysis 🧠",
                "advanced_sub": "AI Prediction • Sentiment • Dividends • Institutional",
                "tab_prediction": "🤖 AI Prediction",
                "tab_sentiment": "📰 Sentiment",
                "tab_dividends": "💰 Dividends",
                "tab_institutional": "🏦 Institutional",

                // AI Prediction
                "pred_signal": "7-Day Signal",
                "pred_current": "Current Price",
                "pred_predicted": "Predicted (7D)",
                "pred_expected": "Expected Change",
                "pred_confidence": "Confidence",
                "pred_trend": "Trend",
                "pred_volatility": "Volatility",
                "pred_momentum": "Momentum",

                // Sentiment
                "sent_overall": "Overall Sentiment",
                "sent_score": "Sentiment Score",
                "sent_news_count": "News Articles",

                // Dividends
                "div_yield": "Dividend Yield",
                "div_annual": "Annual Dividend",
                "div_payout": "Payout Ratio",
                "div_ex_date": "Ex-Dividend Date",
                "div_history": "Dividend History",

                // Institutional
                "inst_ownership": "Institutional Ownership",
                "inst_insider": "Insider Ownership",
                "inst_top": "Top Institutional Holders",
                "inst_transactions": "Insider Transactions",
                "inst_holder": "Holder",
                "inst_shares": "Shares",
                "inst_value": "Value",
                "inst_insider_name": "Insider",
                "inst_transaction": "Transaction",
                "inst_date": "Date",

                // Stock Comparison
                "compare_title": "Stock Comparison Tool",
                "compare_sub": "Compare up to 5 stocks side-by-side",
                "compare_selected": "Selected Stocks",
                "compare_add": "Add Stock",
                "compare_compare": "Compare",
                "compare_chart": "Performance Comparison (90 Days)",
                "compare_table": "Detailed Comparison",
                "compare_metric": "Metric",

                // Navigation (additional)
                "nav_compare": "⚖️ Compare",
                "nav_calendar": "📆 Calendar",
                "nav_insider": "👔 Insider",
                "nav_darkpool": "🌊 Dark Pool",
                "nav_heatmap": "🗺️ Heatmap",

                // Financial Calendar
                "calendar_title": "Financial Calendar",
                "calendar_sub": "Track earnings, dividends & economic events",
                "filter_all": "All Events",
                "event_earnings": "📊 Earnings",
                "event_dividend": "💰 Dividends",
                "event_economic": "📈 Economic",

                // Insider Trading
                "insider_title": "Insider Trading Tracker",
                "insider_sub": "Track executive buy/sell transactions",

                // Dark Pool
                "darkpool_title": "Dark Pool & Block Trades",
                "darkpool_sub": "Unusual Volume Detection"
            },
            "th": {
                // Nav
                "nav_analyzer": "📊 วิเคราะห์หุ้น",
                "nav_screener": "🔍 สแกนหุ้น",
                "nav_trends": "🔥 หุ้นกระแส",
                "nav_portfolio": "💼 พอร์ตจำลอง",

                // Common
                "loading": "กำลังโหลด...",
                "error": "เกิดข้อผิดพลาด",
                "refresh": "รีเฟรช",
                "btn_analyze": "วิเคราะห์",
                "btn_buy": "ซื้อ",
                "btn_sell": "ขาย",
                "search_placeholder": "🔍 ค้นหาชื่อหุ้น (เช่น CPALL.BK, DELTA.BK)",
                "search_tips": "💡 เคล็ดลับ: พิมพ์ชื่อหุ้นได้ <strong>ทั่วโลก</strong>! (เช่น AAPL, 7203.T, 0700.HK, BTC-USD). หุ้นไทยต้องมี <strong>.BK</strong>",
                "favorites": "รายการโปรด ⭐",
                "add_fav": "เพิ่มในรายการโปรด",
                "rem_fav": "ลบออกจากรายการโปรด",
                "no_favs": "ยังไม่มีรายการโปรด กดดาวเพื่อบันทึก! ⭐",

                // Headers
                "analyzer_title": "Stockify Pro 🤖",
                "analyzer_sub": "ผู้ช่วยวิเคราะห์ทางเทคนิคด้วย AI",
                "screener_title": "สแกนหุ้น 🔍",
                "screener_sub": "คัดกรองหุ้นตามสัญญาณเทคนิค",
                "trends_title": "เทรนด์ตลาด 🚀",
                "trends_sub": "ค้นหาหุ้นที่มีการเคลื่อนไหวต่อเนื่อง",
                "portfolio_title": "พอร์ตของฉัน 💼",
                "portfolio_sub": "ระบบพอร์ตจำลองการลงทุน",

                // Table Columns
                "col_symbol": "ชื่อหุ้น",
                "col_price": "ราคา",
                "col_change": "เปลี่ยนแปลง",
                "col_trend": "แนวโน้ม",
                "col_rsi": "RSI",
                "col_signal": "สัญญาณ",
                "col_action": "ดำเนินการ",
                "col_qty": "จำนวน",
                "col_avg_price": "ราคาเฉลี่ย",
                "col_value": "มูลค่ารวม",
                "col_pl": "กำไร/ขาดทุน",
                "col_scenario": "กรณีจำลอง",
                "col_target": "ราคาเป้าหมาย",
                "col_upside": "% อัพไซด์",
                "col_future_val": "มูลค่าในอนาคต",

                // Trends Page
                "trend_scanning": "กำลังสแกนหาหุ้น...",
                "trend_win": "หุ้นขาขึ้นต่อเนื่อง (Winning Streaks)",
                "trend_win_desc": "หุ้นที่ปิดบวกติดต่อกัน 3 วันขึ้นไป",
                "trend_lose": "หุ้นขาลงต่อเนื่อง (Losing Streaks)",
                "trend_lose_desc": "หุ้นที่ปิดลบติดต่อกัน 3 วันขึ้นไป",
                "trend_no_data": "ไม่พบหุ้นในเกณฑ์นี้",

                // Screener Page
                "scan_results": "ผลการสแกนตลาด",
                "scan_loading": "กำลังสแกนตลาด...",
                "scan_connect_fail": "เชื่อมต่อล้มเหลว",

                // Portfolio Page
                "total_balance": "ยอดรวมสุทธิ (เงินสด + หุ้น)",
                "avail_cash": "เงินสดคงเหลือ",
                "reset_pf": "รีเซ็ตพอร์ต ⚠️",
                "curr_holdings": "หุ้นในพอร์ต",
                "trade_history": "ประวัติการเทรด",
                "no_history": "ไม่มีประวัติการเทรด",
                "fetching_prices": "กำลังดึงราคาล่าสุด... ⏳",
                "no_positions": "ไม่มีหุ้นในพอร์ต ไปที่หน้าวิเคราะห์เพื่อเริ่มลงทุน! 🚀",

                // Analyzer / Stats
                "stat_open": "ราคาเปิด",
                "stat_high": "สูงสุด",
                "stat_low": "ต่ำสุด",
                "stat_prev": "ปิดวันก่อน",
                "comp_profile": "ข้อมูลบริษัท",
                "comp_holders": "ผู้ถือหุ้นรายใหญ่",
                "inv_projector": "คาดการณ์ผลตอบแทน",
                "lbl_budget": "เงินลงทุน",
                "lbl_duration": "ระยะเวลา",
                "lbl_days": "วัน",
                "lbl_months": "เดือน",
                "lbl_years": "ปี",
                "disclaimer": "*คำนวณจากเป้าหมายราคาเฉลี่ยของนักวิเคราะห์ ไม่ใช่คำแนะนำการลงทุน",

                // Trading Panel
                "paper_trading": "ส่งคำสั่งซื้อขาย (จำลอง)",
                "submit_order": "ส่งคำสั่ง 🚀",
                "lbl_qty": "จำนวนหุ้น",
                "lbl_action": "คำสั่ง",
                "action_buy": "🟢 ซื้อ (Long)",
                "action_sell": "🔴 ขาย (Short/Close)",
                "trend_up": "ขาขึ้น",
                "trend_down": "ขาลง",
                "trend_side": "แกว่งตัว",

                // Calculator & App
                "scen_bear": "🏰 กรณีเลวร้าย (Bear Case)",
                "scen_base": "⚖️ กรณีปกติ (Base Case)",
                "scen_bull": "🚀 กรณีดีที่สุด (Bull Case)",
                "err_search_first": "❌ กรุณาค้นหาหุ้นก่อน",
                "err_invalid_price": "❌ ข้อมูลราคาไม่ถูกต้อง",
                "sig_buy": "ซื้อ",
                "sig_sell": "ขาย",
                "sig_wait": "ถือ",

                // Fundamentals
                "fund_title": "วิเคราะห์เจาะลึก 📊",
                "fund_fair_value": "ราคาที่เหมาะสม (Fair Value)",
                "fund_pe": "P/E Ratio",
                "fund_pb": "P/B Ratio",
                "fund_roe": "ROE",
                "fund_eps": "กำไรต่อหุ้น (EPS)",
                "fund_debt_eq": "หนี้สินต่อทุน",
                "fund_undervalued": "ถูกกว่ามูลค่าจริง",
                "fund_overvalued": "แพงกว่ามูลค่าจริง",

                // Technical Scorecard
                "tech_title": "สกอร์ทางเทคนิค 📝",
                "tech_score": "คะแนนเทคนิค",
                "tech_indicator": "ตัวชี้วัด",
                "tech_value": "ค่า",
                "tech_action": "สัญญาณ",
                "tech_desc": "คำอธิบาย",

                // Sectors Page
                "nav_sectors": "🔄 กลุ่มอุตฯ",
                "sectors_title": "วิเคราะห์การหมุนเวียนกลุ่ม 🔄",
                "sectors_sub": "ติดตามการไหลของเงินในแต่ละกลุ่มอุตสาหกรรม",
                "sect_leading": "กลุ่มนำ (Top 3)",
                "sect_neutral": "กลาง",
                "sect_lagging": "กลุ่มตาม (Bottom 3)",
                "sect_strongest": "กลุ่มแรงสุด",
                "sect_avg_mom": "Momentum เฉลี่ย",
                "sect_mkt_trend": "แนวโน้มตลาด",
                "sect_1d": "1 วัน",
                "sect_1w": "1 สัปดาห์",
                "sect_1m": "1 เดือน",
                "sect_volume": "สัดส่วน Volume",
                "sect_momentum": "โมเมนตัม",

                // Volatility Page
                "nav_volatility": "⚡ ความผันผวน",
                "vol_title": "แดชบอร์ดความผันผวน ⚡",
                "vol_sub": "ดัชนีความกลัวและความผันผวนของตลาด",
                "vol_vix": "ดัชนี VIX (Fear Index)",
                "vol_fear_meter": "มาตรวัดความกลัว/โลภ",
                "vol_fear_score": "คะแนนความกลัว (จาก VIX)",
                "vol_market_overview": "ภาพรวมตลาด",
                "vol_spy_price": "ราคา SPY",
                "vol_hist_vol": "ความผันผวนย้อนหลัง (20 วัน)",
                "vol_market_trend": "แนวโน้มตลาด",
                "vol_pcr": "สัดส่วน Put/Call",
                "vol_atr_ranking": "หุ้นผันผวนสูงสุด (ATR)",
                "vol_atr": "ATR ($)",
                "vol_atr_pct": "ATR %",
                "vol_daily_range": "ช่วงราคารายวัน",
                "vol_extreme_greed": "โลภสุดขีด",
                "vol_low_fear": "กลัวน้อย",
                "vol_neutral": "ปกติ",
                "vol_elevated_fear": "กลัวสูง",
                "vol_extreme_fear": "กลัวสุดขีด",

                // Heatmap
                "nav_heatmap": "🗺️ Heatmap",
                "heatmap_title": "แผนที่ตลาด 🗺️",
                "heatmap_sub": "ภาพรวมตลาดแบบ Visual",

                // Earnings Calendar
                "nav_earnings": "📅 งบกำไร",
                "earnings_title": "ปฏิทินประกาศงบ 📅",
                "earnings_sub": "ติดตามการประกาศงบและผลประกอบการ",
                "earnings_next": "วันประกาศงบถัดไป",
                "earnings_beat_rate": "อัตราเกินคาด",
                "earnings_eps_ttm": "EPS (TTM)",
                "earnings_eps_fwd": "EPS (คาดการณ์)",
                "earnings_pe": "P/E Ratio",
                "earnings_recent": "ไตรมาสล่าสุด",

                // Advanced Analysis
                "nav_advanced": "🧠 ขั้นสูง",
                "advanced_title": "วิเคราะห์หุ้นขั้นสูง 🧠",
                "advanced_sub": "AI คาดการณ์ • ข่าว • ปันผล • สถาบัน",
                "tab_prediction": "🤖 AI คาดการณ์",
                "tab_sentiment": "📰 ข่าว",
                "tab_dividends": "💰 ปันผล",
                "tab_institutional": "🏦 สถาบัน",

                // AI Prediction
                "pred_signal": "สัญญาณ 7 วัน",
                "pred_current": "ราคาปัจจุบัน",
                "pred_predicted": "คาดการณ์ (7วัน)",
                "pred_expected": "คาดการณ์เปลี่ยน",
                "pred_confidence": "ความมั่นใจ",
                "pred_trend": "แนวโน้ม",
                "pred_volatility": "ความผันผวน",
                "pred_momentum": "โมเมนตัม",

                // Sentiment
                "sent_overall": "ความเชื่อโดยรวม",
                "sent_score": "คะแนน",
                "sent_news_count": "จำนวนข่าว",

                // Dividends
                "div_yield": "ผลตอบแทน",
                "div_annual": "ปันผลต่อปี",
                "div_payout": "อัตราจ่าย",
                "div_ex_date": "วัน XD",
                "div_history": "ประวัติปันผล",

                // Institutional
                "inst_ownership": "สถาบันถือ",
                "inst_insider": "ผบริหารถือ",
                "inst_top": "สถาบันรายใหญ่",
                "inst_transactions": "ธุรกรรมผบริหาร",
                "inst_holder": "ผู้ถือ",
                "inst_shares": "จำนวน",
                "inst_value": "มูลค่า",
                "inst_insider_name": "ผบริหาร",
                "inst_transaction": "ธุรกรรม",
                "inst_date": "วันที่",

                // Stock Comparison
                "compare_title": "เปรียบเทียบหุ้น",
                "compare_sub": "เปรียบเทียบหุ้นสูงสุด 5 ตัว",
                "compare_selected": "หุ้นที่เลือก",
                "compare_add": "เพิ่มหุ้น",
                "compare_compare": "เปรียบเทียบ",
                "compare_chart": "กราฟเปรียบเทียบ (90 วัน)",
                "compare_table": "ตารางเปรียบเทียบ",
                "compare_metric": "ตัวชี้วัด",

                // Navigation (additional)
                "nav_compare": "⚖️ เปรียบเทียบ",
                "nav_calendar": "📆 ปฏิทิน",
                "nav_insider": "👔 ผู้บริหาร",
                "nav_darkpool": "🌊 Dark Pool",
                "nav_heatmap": "🗺️ Heatmap",

                // Financial Calendar
                "calendar_title": "ปฏิทินการเงิน",
                "calendar_sub": "ติดตามงบกำไร ปันผล และเหตุการณ์เศรษฐกิจ",
                "filter_all": "ทั้งหมด",
                "event_earnings": "📊 งบกำไร",
                "event_dividend": "💰 ปันผล",
                "event_economic": "📈 เศรษฐกิจ",

                // Insider Trading
                "insider_title": "ธุรกรรมผู้บริหาร",
                "insider_sub": "ติดตามการซื้อขายของผู้บริหาร",

                // Dark Pool
                "darkpool_title": "ธุรกรรมขนาดใหญ่",
                "darkpool_sub": "ตรวจหาปริมาณผิดปกติ"
            }
        };
    }

    init() {
        this.updatePage();
        this.renderSwitcher();
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('app_lang', lang);
            this.updatePage();
            // Trigger custom event for other scripts to re-render if needed
            window.dispatchEvent(new CustomEvent('langChange', { detail: lang }));
        }
    }

    toggle() {
        const newLang = this.currentLang === 'en' ? 'th' : 'en';
        this.setLanguage(newLang);
    }

    t(key) {
        return this.translations[this.currentLang][key] || key;
    }

    updatePage() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (this.translations[this.currentLang][key]) {
                // If it's an input with placeholder
                if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
                    el.placeholder = this.t(key);
                } else {
                    el.textContent = this.t(key);
                }
            }
        });

        // Update Toggle Button Text
        const btn = document.getElementById('lang-toggle');
        if (btn) {
            btn.innerHTML = this.currentLang === 'en' ? '🇹🇭 TH' : '🇬🇧 EN';
        }
    }

    renderSwitcher() {
        // Check if switcher exists, if not, create it in nav-bar
        if (!document.getElementById('lang-toggle')) {
            const nav = document.querySelector('.nav-bar');
            if (nav) {
                const btn = document.createElement('button');
                btn.id = 'lang-toggle';
                btn.className = 'nav-link';
                btn.style.cursor = 'pointer';
                btn.style.marginLeft = '1rem';
                btn.style.border = '1px solid var(--glass-border)';
                btn.onclick = () => this.toggle();
                nav.appendChild(btn);

                // Set initial text
                btn.innerHTML = this.currentLang === 'en' ? '🇹🇭 TH' : '🇬🇧 EN';
            }
        }
    }
}

// Initialize Global Instance
const i18n = new TranslationManager();
document.addEventListener('DOMContentLoaded', () => {
    i18n.init();
});
