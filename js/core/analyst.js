/**
 * StockifyAnalyst Class
 * Implements the "Stockify Pro" logic for Technical Analysis.
 */
class StockifyAnalyst {
    constructor() {
        // Configuration for Risk Management
        this.STOP_LOSS_PCT = 0.025; // 2.5% Average (2-3% range)
        this.RISK_REWARD_RATIO = 2; // 1:2
    }

    /**
     * Analyze market data and generate a signal.
     * @param {Object} data - Input data { price, ema200, rsi, macd: { line, signal } }
     * @returns {Object} result - Structured analysis result
     */
    analyze(data) {
        const { price, ema200, rsi, macd } = data;

        // 1. Trend Identification
        const isUptrend = price > ema200;
        const trend = isUptrend ? "UP" : "DOWN";

        // 2. Signal Generation
        let signal = "WAIT";
        let confidence = "Low";
        let reason = "";

        // Buy Logic
        // RSI > 30 (Rebound check - Simplified: if in buy zone 30-50 and Trend UP)
        // OR MACD Line > Signal
        const macdCrossUp = macd.line > macd.signal; // Crossover or positive spread
        const macdCrossDown = macd.line < macd.signal;

        // Refined Logic based on Prompt:
        // Buy: RSI > 30 (Assuming rebound from oversold) OR MACD Crossover UP
        // Sell: RSI < 70 (Assuming pullback from overbought) OR MACD Crossover DOWN

        if (isUptrend) {
            // Looking for BUY dips
            if (rsi > 30 && rsi < 55 && macdCrossUp) {
                signal = "BUY";
                confidence = "High"; // Trend-following + confluence
                reason = "Trend UP + RSI acceptable + MACD Bullish";
            } else if (rsi > 30 && rsi < 50) {
                // Weak buy setup
                signal = "BUY";
                confidence = "Medium";
                reason = "Trend UP + RSI Rebound Potential";
            } else if (macdCrossUp) {
                signal = "BUY";
                confidence = "Medium";
                reason = "Trend UP + MACD Bullish Crossover";
            } else {
                reason = "Trend UP but waiting for cleaner entry (RSI/MACD neutral)";
            }
        } else {
            // Looking for SELL rallies
            if (rsi < 70 && rsi > 45 && macdCrossDown) {
                signal = "SELL";
                confidence = "High";
                reason = "Trend DOWN + RSI acceptable + MACD Bearish";
            } else if (rsi < 70 && rsi > 50) {
                signal = "SELL";
                confidence = "Medium";
                reason = "Trend DOWN + RSI Pullback Potential";
            } else if (macdCrossDown) {
                signal = "SELL";
                confidence = "Medium";
                reason = "Trend DOWN + MACD Bearish Crossover";
            } else {
                reason = "Trend DOWN but waiting for cleaner entry";
            }
        }

        // Wait Override
        if (rsi >= 45 && rsi <= 55 && Math.abs(macd.line - macd.signal) < 0.1) {
            signal = "WAIT";
            confidence = "High";
            reason = "Market is ranging (RSI neutral, MACD flat)";
        }

        // 3. Risk Management & Trade Setup (Calculate for all scenarios to provide guidance)
        // Standard setup: Buy Limit at -2%, SL at -5%, TP at +10% (Risk:Reward 1:2)
        // If Signal is SELL, invert logic.

        let entry = price;
        let buyLimit = price;
        let sl = price;
        let tp = price;

        if (signal === "SELL") {
            // Short Setup
            entry = price;
            buyLimit = price * 1.02; // BOUNCE to sell
            sl = price * 1.05;
            tp = price * 0.90;
        } else {
            // Long Setup (Default)
            entry = price;
            buyLimit = price * 0.98; // DIP to buy
            sl = price * 0.95;
            tp = price * 1.10;
        }

        return {
            signal,
            trend,
            confidence,
            reason,
            marketData: data,
            tradeSetup: { entry, buyLimit, sl, tp }
        };
    }

    generateOptionsStrategy(data) {
        const price = data.price;
        const ema = data.ema200;
        const macd = data.macd.line;
        const signal = data.macd.signal;

        let strategy = "ตลาดไซด์เวย์ / Iron Condor 🦅";
        let reason = "แนวโน้มออกข้าง พิจารณาเก็บค่าพรีเมียม (Collecting Premium)";

        if (price > ema && macd > signal && macd > 0) {
            strategy = "เปิดสถานะ Long Call 🟢";
            reason = "แนวโน้มขาขึ้นแข็งแกร่ง (ราคา > EMA200) และ MACD เป็นกระทิง ซื้อตามโมเมนตัมขาขึ้น";
        } else if (price < ema && macd < signal && macd < 0) {
            strategy = "เปิดสถานะ Long Put 🔴";
            reason = "แนวโน้มขาลงแข็งแกร่ง (ราคา < EMA200) และ MACD เป็นหมี ซื้อตามโมเมนตัมขาลง";
        } else if (price > ema && macd < signal) {
            strategy = "รอ / ขาย Covered Call ⚠️";
            reason = "ขาขึ้นเริ่มอ่อนกำลัง ระวังการย่อตัวหรือพักฐาน";
        } else if (price < ema && macd > signal) {
            strategy = "รอ / ขาย Put Spread ⚠️";
            reason = "ขาลงเริ่มแผ่ว ระวังการกลับตัวหรือพักฐาน";
        }

        return `
### 🎯 กลยุทธ์ออปชั่น (Options Strategy)
*   **คำแนะนำ**: ${strategy}
*   **เหตุผล**: ${reason}
`;
    }

    /**
     * Determine high-level market context and timing advice.
     */
    getMarketContext(data) {
        const { price, ema200, rsi } = data;
        const isUptrend = price > ema200;

        let health = "";
        let timing = "";
        let healthEmoji = "";

        // 1. Market Health (Overall Trend)
        if (isUptrend) {
            if (price > ema200 * 1.05) {
                health = "ดีมาก (Strong Bullish) - ตลาดเป็นขาขึ้นแข็งแกร่ง";
                healthEmoji = "🟢";
            } else {
                health = "ดี (Bullish) - ตราดเป็นขาขึ้นแต่อยู่ในช่วงพักตัว";
                healthEmoji = "🟢";
            }
        } else {
            if (price < ema200 * 0.95) {
                health = "แย่ (Strong Bearish) - ตลาดเป็นขาลงชัดเจน";
                healthEmoji = "🔴";
            } else {
                health = "ระมัดระวัง (Bearish) - ราคาอยู่ต่ำกว่าเส้นค่าเฉลี่ย";
                healthEmoji = "🟠";
            }
        }

        // 2. Timing (Entry/Exit Timing)
        if (isUptrend) {
            if (rsi < 40) {
                timing = "✅ จังหวะดีมาก (Best Entry) - ราคาย่อตัวลงมาในเทรนด์ขาขึ้น";
            } else if (rsi > 70) {
                timing = "⚠️ ไล่ราคาเกินไป (Overextended) - ควรรอให้ราคาย่อตัวก่อน";
            } else if (rsi >= 40 && rsi <= 60) {
                timing = "🆗 สะสมได้ (Accumulate) - ราคากลางๆ เข้าซื้อได้บางส่วน";
            } else {
                timing = "⏸️ รอสัญญาณชัดเจนกว่านี้";
            }
        } else {
            // Downtrend
            if (rsi > 60) {
                timing = "🔻 จังหวะ Short/ขายทำกำไร (Bounce Sell) - ราคาเด้งขึ้นมาในขาลง";
            } else if (rsi < 30) {
                timing = "⚠️ ระวังการเด้งสวน (Oversold Bounce) - อย่าเพิ่ง Short ตาม";
            } else {
                timing = "⛔ ไม่ควรลงทุนขาขึ้น (Avoid Long) - ตลาดยังมีความเสี่ยงสูง";
            }
        }

        return { health, timing, healthEmoji };
    }

    /**
     * Analyze Fundamental Data
     * @param {Object} fundamentals - The fundamental data object
     * @param {Number} currentPrice - Current stock price
     */
    analyzeFundamentals(fundamentals, currentPrice) {
        if (!fundamentals || !fundamentals.valuation) return "ไม่มีข้อมูลพื้นฐานเพียงพอ (Insufficient Data)";

        const val = fundamentals.valuation;
        const prof = fundamentals.profitability;
        const grow = fundamentals.growth;
        const cons = fundamentals.consensus;

        let output = `📊 **วิเคราะห์ปัจจัยพื้นฐานเชิงลึก (Deep Fundamental Analysis)**\n`;

        // 1. Valuation Analysis
        let peStatus = "N/A";
        let pe = val.trailingPE;
        if (pe) {
            if (pe < 15) peStatus = "ถูก (Undervalued) 🟢";
            else if (pe > 30) peStatus = "แพง (Overvalued) 🔴";
            else peStatus = "ราคาเหมาะสม (Fair Value) 🟡";
        }

        let peg = val.pegRatio;
        let pegStatus = "N/A";
        if (peg) {
            if (peg < 1) pegStatus = "เติบโตดีเทียบกับราคา (Cheap for Growth) 🟢";
            else if (peg > 2) pegStatus = "ราคาโตเกินพื้นฐาน (Expensive for Growth) 🔴";
            else pegStatus = "สมเหตุสมผล (Reasonable) 🟡";
        }

        output += `**1. ความถูกแพงของราคา (Valuation):**\n`;
        output += `*   **P/E Ratio:** ${pe ? pe.toFixed(2) : 'N/A'} - ${peStatus}\n`;
        output += `*   **PEG Ratio:** ${peg ? peg.toFixed(2) : 'N/A'} - ${pegStatus}\n`;

        // 2. Profitability Analysis
        let margin = prof.profitMargins;
        let marginStatus = "";
        if (margin) {
            marginStatus = (margin > 0.20) ? "กำไรสูงมาก (High Efficiency) ⭐" : (margin > 0.10) ? "กำไรดี (Good) 🟢" : "กำไรบาง (Low Margin) ⚠️";
        }

        let roe = prof.returnOnEquity;
        let roeStatus = "";
        if (roe) {
            roeStatus = (roe > 0.15) ? "ผู้บริหารเก่ง (Excellent) 🏆" : (roe > 0.08) ? "มาตรฐาน (Standard)" : "ผลตอบแทนต่ำ (Low Return) ⚠️";
        }

        output += `\n**2. ประสิทธิภาพการทำกำไร (Profitability):**\n`;
        output += `*   **Net Margin:** ${margin ? (margin * 100).toFixed(2) + '%' : 'N/A'} - ${marginStatus}\n`;
        output += `*   **ROE:** ${roe ? (roe * 100).toFixed(2) + '%' : 'N/A'} - ${roeStatus}\n`;

        // 3. Analyst Consensus
        if (fundamentals.consensus) {
            output += `\n👥 **มุมมองนักวิเคราะห์ (Analyst Consensus - 12M Forecast)**\n`;

            const rec = fundamentals.consensus.recommendation ? fundamentals.consensus.recommendation.toUpperCase() : "N/A";
            const mean = fundamentals.consensus.targetMean;
            const high = fundamentals.consensus.targetHigh;
            const low = fundamentals.consensus.targetLow;
            const num = fundamentals.consensus.numberOfAnalysts || 0;

            output += `* **คำแนะนำ:** ${rec}`;
            if (num > 0) output += ` (จาก ${num} โบรกเกอร์)`;
            output += `\n`;

            if (mean) {
                const upside = ((mean - currentPrice) / currentPrice) * 100;
                const upsideIcon = upside > 0 ? "🚀" : "🔻";
                output += `* **ราคาเป้าหมายเฉลี่ย (Average):** ${mean.toFixed(2)} (${upsideIcon} ${upside.toFixed(2)}%)\n`;
            }

            if (high) {
                const highUpside = ((high - currentPrice) / currentPrice) * 100;
                output += `* **เป้าหมายสูงสุด (Max Bull Case):** ${high.toFixed(2)} (+${highUpside.toFixed(2)}%) 🌟\n`;
            }

            if (low) {
                output += `* **เป้าหมายต่ำสุด (Min Bear Case):** ${low.toFixed(2)}\n`;
            }

            output += `* *หมายเหตุ: เป็นราคาคาดการณ์ในอีก 1 ปีข้างหน้า (12-Month Target)*\n`;
        }

        output += `\n`;
        return output;
    }

    /**
     * Format the result into the requested Thai Markdown text.
     */
    formatOutput(result) {
        const { signal, trend, confidence, reason, marketData, tradeSetup } = result;
        const context = this.getMarketContext(marketData);

        const trendText = trend === "UP" ? "ขาขึ้น (Uptrend)" : "ขาลง (Downtrend)";
        const trendEmoji = trend === "UP" ? "📈" : "📉";

        // Technical Evidence explanation
        const rsiVal = marketData.rsi;
        let momText = `RSI อยู่ที่ ${rsiVal.toFixed(2)}`;
        if (rsiVal > 70) momText += " (Overbought - โซนซื้อมากเกินไป)";
        else if (rsiVal < 30) momText += " (Oversold - โซนขายมากเกินไป)";
        else momText += " (Neutral - โซนกลาง)";

        if (marketData.macd.line > marketData.macd.signal) {
            momText += ", MACD ตัดขึ้น (Bullish)";
        } else {
            momText += ", MACD ตัดลง (Bearish)";
        }

        // --- NEW SECTION: Market Context ---
        let output = `🌤️ **สภาพตลาดและคำแนะนำ (Market Context)**\n`;
        output += `* **สภาพตลาด:** ${context.health} ${context.healthEmoji}\n`;
        output += `* **จังหวะการลงทุน:** ${context.timing}\n`;

        if (marketData.sentiment_meter) {
            const sm = marketData.sentiment_meter;
            let gauge = "😐 Neutral";
            if (sm.score > 60) gauge = "🤑 Greed (ตลาดกำลังโลภ)";
            else if (sm.score > 80) gauge = "🤯 Extreme Greed (ระวังดอย)";
            else if (sm.score < 40) gauge = "😨 Fear (ตลาดกลัว)";
            else if (sm.score < 20) gauge = "😱 Extreme Fear (จังหวะเก็บของ)";

            // Visual Bar
            const barLength = 10;
            const fill = Math.round((sm.score / 100) * barLength);
            const empty = barLength - fill;
            const bar = "🟩".repeat(fill) + "⬜".repeat(empty);

            output += `* **Sentiment:** ${bar} ${sm.score.toFixed(0)}/100 (${gauge})\n`;
        }
        output += `\n`; // End Section
        // ------------------------------------

        output += `🚩 **STOCKIFY SIGNAL: ${signal}**\n*(ความมั่นใจ: ${confidence})*\n\n`;

        // --- NEW SECTION: Fundamental Analysis ---
        if (marketData.fundamentals) {
            output += this.analyzeFundamentals(marketData.fundamentals, marketData.price);
        }
        // -----------------------------------------

        output += `📊 **บทวิเคราะห์ทางเทคนิค:**\n`;
        output += `* **เทรนด์หลัก:** ${trendText} ${trendEmoji} (EMA)\n`;
        output += `* **โมเมนตัม:** ${momText}\n`;
        output += `* **สรุปสถานการณ์:** ${reason} ซึ่งสนับสนุนสัญญาณ ${signal}\n\n`;

        // Trade Setup Section
        if (tradeSetup) {
            output += `🎯 **แผนการเทรด (Trade Setup):**\n`;

            // Emoji logic based on direction
            const isLong = signal !== "SELL";
            const tpEmoji = isLong ? "💰" : "📉";
            const slEmoji = "🛑";

            output += `🔵 **ราคาเป้าหมาย (Take Profit):** ${tradeSetup.tp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${tpEmoji}\n`;
            output += `🟢 **ราคาซื้อ (Entry):** ${tradeSetup.entry.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n`;
            output += `🟡 **ราคาตั้งรับ (Buy Limit):** ${tradeSetup.buyLimit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (รอราคาพักตัว)\n`;
            output += `🔴 **จุดตัดขาดทุน (Stop Loss):** ${tradeSetup.sl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${slEmoji}\n`;

            let advice = "\n⚠️ **คำแนะนำ:** ";
            if (signal === "BUY") advice += "ควรแบ่งไม้ซื้อ (Scale In) เมื่อราคาย่อตัวลงมาที่แนวรับ";
            else if (signal === "SELL") advice += "รอเด้งเพื่อ Short, อย่า Short สวนเทรนด์ขาขึ้นแรงๆ";
            else advice += "ตลาดผันผวน ควรลดขนาด Position Size ลง";

            output += `${advice}\n`;
        }

        // Add Options Strategy
        output += this.generateOptionsStrategy(marketData);

        return output;
    }
}
