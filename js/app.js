document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const symbolInput = document.getElementById('symbol-input');
    const resultContainer = document.getElementById('result-container');
    const resultOutput = document.getElementById('result-output');
    const loadingSpinner = document.getElementById('loading-spinner');
    let currentSymbol = null;

    // Market Info Elements
    const marketInfo = document.getElementById('market-info');
    const displaySymbol = document.getElementById('tikz-symbol');
    const displayPrice = document.getElementById('tikz-price');
    const displayChange = document.getElementById('tikz-change');

    // News Elements
    const newsSection = document.getElementById('news-section');

    const newsList = document.getElementById('news-list');
    const companySection = document.getElementById('company-section');

    // Chart Elements
    const chartCard = document.getElementById('chart-card');
    const chartContainer = document.getElementById('chart-container');
    let chart;
    let candleSeries, ema50Series, ema200Series, volumeSeries;

    // Initialize Analyst & Portfolio
    const analyst = new StockifyAnalyst();
    const portfolio = new PortfolioManager();

    // Trading Elements
    const walletBalance = document.getElementById('wallet-balance');
    const tradingPanel = document.getElementById('trading-panel');
    const tradeFeedback = document.getElementById('trade-feedback');
    const btnTrade = document.getElementById('btn-execute-trade');

    function updateWalletUI() {
        const data = portfolio.getPortfolioSummary();
        walletBalance.textContent = data.balance.toLocaleString(undefined, { minimumFractionDigits: 2 });
    }

    // Initial Wallet Load
    updateWalletUI();

    btnTrade.addEventListener('click', () => {
        const symbol = displaySymbol.textContent; // Get from current analysis
        if (!symbol || symbol === "SYMBOL") {
            tradeFeedback.textContent = i18n.t('err_search_first');
            tradeFeedback.style.color = "#ef4444";
            return;
        }

        const action = document.getElementById('trade-action').value;
        const qty = parseInt(document.getElementById('trade-qty').value);
        const priceText = displayPrice.textContent.replace(/,/g, '');
        const price = parseFloat(priceText);

        if (isNaN(price) || price <= 0) {
            tradeFeedback.textContent = i18n.t('err_invalid_price');
            return;
        }

        let result;
        if (action === "BUY") {
            result = portfolio.buy(symbol, price, qty);
        } else {
            result = portfolio.sell(symbol, price, qty);
        }

        tradeFeedback.textContent = result.message;
        tradeFeedback.style.color = result.success ? "#22c55e" : "#ef4444";

        if (result.success) {
            updateWalletUI();
        }
    });

    // Initialize Chart
    function initChart() {
        if (chart) return; // Already initialized

        try {
            console.log("Initializing Chart...");
            chart = LightweightCharts.createChart(chartContainer, {
                width: chartContainer.clientWidth,
                height: 450, // Force height if container is 0
                layout: {
                    background: { type: 'solid', color: '#1e293b' }, // Matches --card-bg
                    textColor: '#94a3b8',
                },
                grid: {
                    vertLines: { color: '#334155' },
                    horzLines: { color: '#334155' },
                },
                rightPriceScale: {
                    borderColor: '#334155',
                },
                timeScale: {
                    borderColor: '#334155',
                },
            });
            console.log("Chart created:", chart);

            candleSeries = chart.addCandlestickSeries({
                upColor: '#22c55e',
                downColor: '#ef4444',
                borderVisible: false,
                wickUpColor: '#22c55e',
                wickDownColor: '#ef4444',
            });

            // EMA 50 (Green)
            ema50Series = chart.addLineSeries({
                color: '#22c55e',
                lineWidth: 1,
                crosshairMarkerVisible: false,
                priceLineVisible: false, // Don't show horizontal line for EMA
                lastValueVisible: false,
            });

            // EMA 200 (Red)
            ema200Series = chart.addLineSeries({
                color: '#ef4444',
                lineWidth: 2,
                crosshairMarkerVisible: false,
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Volume (Histogram) - Separate Scale
            volumeSeries = chart.addHistogramSeries({
                priceFormat: { type: 'volume' },
                priceScaleId: '', // Overlay
                color: '#26a69a',
            });

            // Configure Scales to separate Price and Volume
            chart.priceScale('right').applyOptions({
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.3, // Leave space for volume
                },
            });

            volumeSeries.priceScale().applyOptions({
                scaleMargins: {
                    top: 0.8, // Volume only in bottom 20%
                    bottom: 0,
                },
            });
        } catch (error) {
            console.error("Error creating chart:", error);
            chartCard.innerHTML = `<div style="color:red; text-align:center; padding:1rem;">Error loading chart: ${error.message}</div>`;
        }

        // Handle Resize
        const resizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== chartContainer) { return; }
            const newRect = entries[0].contentRect;
            if (chart) {
                chart.applyOptions({ width: newRect.width, height: newRect.height });
            }
        });
        resizeObserver.observe(chartContainer);
    }

    // --- Tab Switching Logic ---
    window.switchTab = (tabName) => {
        // Update Buttons
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        if (tabName === 'chart') document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        if (tabName === 'fund') document.querySelector('.tab-btn:nth-child(2)').classList.add('active');

        // Update Views
        if (tabName === 'chart') {
            document.getElementById('chart-container').style.display = 'block';
            document.getElementById('fundamentals-view').style.display = 'none';
        } else {
            document.getElementById('chart-container').style.display = 'none';
            document.getElementById('fundamentals-view').style.display = 'block';
        }
    }

    // Backtest Button
    const btnBacktest = document.getElementById('btn-run-backtest');
    const backtestOverlay = document.getElementById('backtest-overlay');
    const btModal = document.getElementById('bt-modal');
    const closeBtModal = document.getElementById('close-bt-modal');
    const btnStartBt = document.getElementById('btn-start-bt');

    // Config Inputs
    const slRange = document.getElementById('in-sl');
    const rsiBuyRange = document.getElementById('in-rsi-buy');
    const rsiSellRange = document.getElementById('in-rsi-sell');
    const dispSl = document.getElementById('disp-sl');
    const dispRsiBuy = document.getElementById('disp-rsi-buy');
    const dispRsiSell = document.getElementById('disp-rsi-sell');

    // 1. Open Configuration
    btnBacktest.addEventListener('click', () => {
        if (!currentSymbol) return;
        btModal.style.display = 'flex';
    });

    // 2. Slider Logic
    if (slRange) slRange.oninput = (e) => dispSl.textContent = e.target.value;
    if (rsiBuyRange) rsiBuyRange.oninput = (e) => dispRsiBuy.textContent = e.target.value;
    if (rsiSellRange) rsiSellRange.oninput = (e) => dispRsiSell.textContent = e.target.value;

    // 3. Close Logic
    if (closeBtModal) closeBtModal.onclick = () => btModal.style.display = 'none';
    window.onclick = (e) => { if (e.target == btModal) btModal.style.display = 'none'; };

    // 4. Run Logic
    if (btnStartBt) btnStartBt.addEventListener('click', async () => {
        btModal.style.display = 'none';
        backtestOverlay.style.display = 'block';
        document.getElementById('bt-return').textContent = "Running...";

        try {
            const params = {
                rsi_buy: rsiBuyRange.value,
                rsi_sell: rsiSellRange.value,
                stop_loss: slRange.value
            };

            const res = await fetch('http://localhost:5000/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: currentSymbol, params: params })
            });

            const data = await res.json();

            if (data.error) {
                backtestOverlay.innerHTML = `<div style="color:red;">Error: ${data.error}</div>`;
                return;
            }

            const returnEl = document.getElementById('bt-return');
            const winEl = document.getElementById('bt-winrate');
            const tradeEl = document.getElementById('bt-trades');

            const ret = data.return_pct;
            returnEl.textContent = `${ret > 0 ? '+' : ''}${ret.toFixed(2)}%`;
            returnEl.style.color = ret >= 0 ? '#22c55e' : '#ef4444';

            winEl.textContent = `${data.win_rate.toFixed(1)}%`;
            tradeEl.textContent = data.total_trades;

            btnBacktest.textContent = "Adjust Strategy ⚙️";

        } catch (e) {
            console.error(e);
            backtestOverlay.innerHTML = `<div style="color:red;">Connection Error</div>`;
        }
    });

    let updateInterval;

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = symbolInput.value.trim();
        if (!symbol) return;

        // Reset UI
        resultContainer.style.display = 'none';
        marketInfo.style.display = 'none';
        newsSection.style.display = 'none';
        chartCard.style.display = 'none';
        tradingPanel.style.display = 'none'; // Hide trading initially
        tradeFeedback.textContent = "";

        const companySection = document.getElementById('company-section');
        if (companySection) companySection.style.display = 'none';

        loadingSpinner.style.display = 'block';
        resultOutput.innerHTML = '';
        newsList.innerHTML = '';

        // Clear previous interval
        if (updateInterval) clearInterval(updateInterval);

        // Initial Fetch
        await updateData(symbol, true);

        // Start Auto-Refresh (every 5 seconds)
        updateInterval = setInterval(() => {
            updateData(symbol, false);
        }, 5000);
    });

    async function updateData(symbol, isInitialLoad) {
        try {
            const response = await fetch(`http://localhost:5000/analyze/${symbol}`);
            const data = await response.json();

            currentSymbol = symbol;

            if (data.error) {
                if (isInitialLoad) showError(data.error);
                return;
            }

            // Update Star UI
            updateStarUI(data.symbol);

            // Update UI with Data
            displaySymbol.textContent = data.symbol;
            displayPrice.textContent = data.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

            const change = data.change_percent;
            const changeSign = change >= 0 ? '+' : '';
            displayChange.textContent = `${changeSign}${change.toFixed(2)}%`;
            displayChange.className = `change-display ${change >= 0 ? 'text-up' : 'text-down'}`;

            // Render Stats
            document.getElementById('stats-grid').style.display = 'grid';
            document.getElementById('stat-open').textContent = data.stats.open.toLocaleString(undefined, { minimumFractionDigits: 2 });
            document.getElementById('stat-high').textContent = data.stats.high.toLocaleString(undefined, { minimumFractionDigits: 2 });
            document.getElementById('stat-low').textContent = data.stats.low.toLocaleString(undefined, { minimumFractionDigits: 2 });
            document.getElementById('stat-prev').textContent = data.stats.prev_close.toLocaleString(undefined, { minimumFractionDigits: 2 });

            marketInfo.style.display = 'flex';

            // Show Trading Panel
            tradingPanel.style.display = 'block';

            // Chart
            chartCard.style.display = 'block';
            if (!chart) initChart();

            if (data.history && data.history.length > 0) {
                candleSeries.setData(data.history);

                // Set EMA Data
                const ema50Data = data.history.filter(h => h.ema50).map(h => ({ time: h.time, value: h.ema50 }));
                const ema200Data = data.history.filter(h => h.ema200).map(h => ({ time: h.time, value: h.ema200 }));

                if (ema50Series) ema50Series.setData(ema50Data);
                if (ema200Series) ema200Series.setData(ema200Data);

                // Set Volume Data
                const volumeData = data.history.map(h => ({
                    time: h.time,
                    value: h.volume,
                    color: h.close >= h.open ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'
                }));
                if (volumeSeries) volumeSeries.setData(volumeData);

                // Set Markers (Signals) on Latest logic
                const lastCandle = data.history[data.history.length - 1];
                const markers = [];

                // Parse Analyst Signal
                // We run analyst.analyze(data) later, but we can peek at the signal logic or wait for it
                // For simplicity, let's use the 'macd_bull' and 'rsi' from the server calculation if available,
                // or just rely on the text signal.
                // Better approach: Let's use the visual "Signal" badge logic from earlier or re-run simple logic here.

                // Let's use the computed EMA crossover for a clear visual marker
                const isUptrend = lastCandle.close > lastCandle.ema200;
                let text = "";
                let shape = "";
                let color = "";

                if (data.rsi < 30) {
                    text = "OVERSOLD"; shape = "arrowUp"; color = "#22c55e";
                } else if (data.rsi > 70) {
                    text = "OVERBOUGHT"; shape = "arrowDown"; color = "#ef4444";
                }

                if (text) {
                    markers.push({
                        time: lastCandle.time,
                        position: shape === 'arrowUp' ? 'belowBar' : 'aboveBar',
                        color: color,
                        shape: shape,
                        text: text,
                    });
                }

                candleSeries.setMarkers(markers);

                if (isInitialLoad) chart.timeScale().fitContent();
            }

            // Company Profile & Holders (Only render on initial load)
            if (companySection && data.profile.summary) {
                document.getElementById('prof-sector').textContent = data.profile.sector || '-';
                document.getElementById('prof-industry').textContent = data.profile.industry || '-';
                document.getElementById('prof-summary').textContent = data.profile.summary;

                const holdersList = document.getElementById('holders-list');
                holdersList.innerHTML = '';
                if (data.holders && data.holders.length > 0) {
                    data.holders.forEach(h => {
                        const li = document.createElement('li');
                        li.innerHTML = `<span class="holder-val">${h.value}</span> <span class="holder-desc">${h.desc}</span>`;
                        holdersList.appendChild(li);
                    });
                } else {
                    holdersList.innerHTML = '<li>Data not available</li>';
                }
                companySection.style.display = 'grid';
            }


            // Populate Fundamentals (Every update)
            if (data.fundamentals) {
                const f = data.fundamentals;
                // Helper to format
                const fmt = (v) => v !== undefined && v !== null ? v.toFixed(2) : '-';

                document.getElementById('val-pe').textContent = fmt(f.valuation.trailingPE);
                document.getElementById('val-eps').textContent = fmt(f.valuation.trailingEps);
                document.getElementById('val-pb').textContent = fmt(f.valuation.priceToBook);
                document.getElementById('val-roe').textContent = fmt(f.profitability.returnOnEquity * 100) + '%';
                document.getElementById('val-de').textContent = fmt(f.health.debtToEquity);

                // Fair Value Logic
                const fv = f.fairValue;
                const fvBox = document.getElementById('val-fair');
                const fvStatus = document.getElementById('val-status');
                const meter = document.getElementById('val-meter');

                if (fv) {
                    fvBox.textContent = fv.toFixed(2);
                    const upside = ((fv - data.price) / data.price) * 100;

                    if (upside > 0) { // Undervalued
                        fvStatus.textContent = `${i18n.t('fund_undervalued')} (+${upside.toFixed(1)}%)`;
                        fvStatus.style.color = '#22c55e';
                        fvStatus.style.background = 'rgba(34, 197, 94, 0.1)';
                        meter.style.width = Math.min(100, 50 + (upside / 2)) + '%'; // Shift right
                    } else { // Overvalued
                        fvStatus.textContent = `${i18n.t('fund_overvalued')} (${upside.toFixed(1)}%)`;
                        fvStatus.style.color = '#ef4444';
                        fvStatus.style.background = 'rgba(239, 68, 68, 0.1)';
                        meter.style.width = Math.max(0, 50 + (upside / 2)) + '%'; // Shift left
                    }
                } else {
                    fvBox.textContent = 'N/A';
                    fvStatus.textContent = 'Insufficient Data';
                    meter.style.width = '50%';
                }
            }


            // Analysis
            const analysisResult = analyst.analyze(data);
            const formattedText = analyst.formatOutput(analysisResult);
            resultOutput.innerHTML = parseMarkdown(formattedText);

            // Render detailed Technical Scorecard
            if (data.technical_analysis) {
                renderTechnicalScore(data.technical_analysis);
            }

            if (isInitialLoad) resultContainer.style.display = 'block';

            // --- Investment Calculator Logic (Time-Based) ---
            const calcSection = document.getElementById('calculator-section');
            let budgetInput = document.getElementById('calc-budget');
            let durationInput = document.getElementById('calc-duration-val'); // New
            let unitInput = document.getElementById('calc-duration-unit'); // New
            const calcBody = document.getElementById('calc-body');

            // Define calculation function
            const renderCalculator = () => {
                if (!data.fundamentals || !data.fundamentals.consensus || !data.fundamentals.consensus.targetMean) {
                    calcSection.style.display = 'none';
                    return;
                }

                calcSection.style.display = 'block';
                const budget = parseFloat(budgetInput.value) || 0;
                let durationVal = parseFloat(durationInput.value) || 1;
                const unit = unitInput.value;
                const currentPrice = data.price;
                const cons = data.fundamentals.consensus;

                // Convert time to YEARS
                let timeInYears = 1;
                if (unit === 'days') timeInYears = durationVal / 365;
                else if (unit === 'months') timeInYears = durationVal / 12;
                else timeInYears = durationVal;

                // Scenarios from Analyst 1-Year Targets
                const scenarios = [
                    { name: i18n.t('scen_bear'), target1Y: cons.targetLow, color: "#f87171" },
                    { name: i18n.t('scen_base'), target1Y: cons.targetMean, color: "#fbbf24" },
                    { name: i18n.t('scen_bull'), target1Y: cons.targetHigh, color: "#34d399" }
                ];

                calcBody.innerHTML = '';

                scenarios.forEach(scen => {
                    if (!scen.target1Y) return;

                    // 1. Calculate Implied Annual Growth Rate (CAGR) based on 1Y Target
                    // Formula: Rate = (Target - Current) / Current
                    // This creates a linear/CAGR slope.
                    const annualRate = (scen.target1Y - currentPrice) / currentPrice;

                    // 2. Project Future Price based on Time
                    // Formula: FV = PV * (1 + r)^t
                    // Note: If annualRate is negative, it decays.
                    const projectedPrice = currentPrice * Math.pow((1 + annualRate), timeInYears);

                    const shares = budget / currentPrice;
                    const futureValue = shares * projectedPrice;
                    const profit = futureValue - budget;
                    const totalGrowth = ((projectedPrice - currentPrice) / currentPrice) * 100;

                    const row = document.createElement('tr');
                    const profitClass = profit >= 0 ? 'text-up' : 'text-down';
                    const profitColor = profit >= 0 ? 'var(--success-color)' : 'var(--danger-color)';
                    const sign = profit >= 0 ? '+' : '';

                    row.innerHTML = `
                        <td style="color: ${scen.color}; font-weight: bold;">${scen.name}</td>
                        <td>${projectedPrice.toFixed(2)}</td>
                        <td style="color: ${profitColor}">${sign}${totalGrowth.toFixed(2)}%</td>
                        <td style="font-weight: bold;">${futureValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
                        <td style="color: ${profitColor}; font-weight: bold;">${sign}${profit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</td>
                    `;
                    calcBody.appendChild(row);
                });
            };

            // Run initial calc
            renderCalculator();

            // Bind events for live calculation
            [budgetInput, durationInput, unitInput].forEach(input => {
                if (input) {
                    const clone = input.cloneNode(true);
                    input.parentNode.replaceChild(clone, input);
                    clone.addEventListener(input.id === 'calc-duration-unit' ? 'change' : 'input', renderCalculator);
                    // Update reference for closure (re-get the element after replacement)
                    if (input.id === 'calc-budget') budgetInput = document.getElementById('calc-budget');
                    if (input.id === 'calc-duration-val') durationInput = document.getElementById('calc-duration-val');
                    if (input.id === 'calc-duration-unit') unitInput = document.getElementById('calc-duration-unit');
                }
            });
            // -----------------------------------

            // News (Only render on initial load)
            if (isInitialLoad && data.news && data.news.length > 0) {
                renderNews(data.news);
            }

        } catch (err) {
            console.error(err);
            if (isInitialLoad) showError("Connection Error. Ensure server is running.");
        } finally {
            if (isInitialLoad) loadingSpinner.style.display = 'none';
        }
    }

    function renderNews(newsItems) {
        newsList.innerHTML = '';
        newsItems.slice(0, 8).forEach(item => {
            const card = document.createElement('a');
            const sentimentClass = item.sentiment || 'Neutral';
            card.className = `news-card ${sentimentClass}`;
            card.href = item.link;
            card.target = '_blank';

            let dateStr = item.providerPublishTime;
            try {
                const d = new Date(item.providerPublishTime);
                if (!isNaN(d)) dateStr = d.toLocaleDateString();
            } catch (e) { }

            let sentimentBadge = "";
            if (item.sentiment === "Positive") sentimentBadge = "<span class='sentiment-badge Positive'>Bullish 🐂</span>";
            if (item.sentiment === "Negative") sentimentBadge = "<span class='sentiment-badge Negative'>Bearish 🐻</span>";

            card.innerHTML = `
                <div class="news-title">${item.title} ${sentimentBadge}</div>
                <div class="news-meta">
                    <span>${item.publisher}</span>
                    <span>${dateStr}</span>
                </div>
            `;
            newsList.appendChild(card);
        });
        newsSection.style.display = 'block';
    }

    function showError(msg) {
        resultContainer.style.display = 'block';
        resultOutput.innerHTML = `<div style="color: #ef4444; font-weight: bold; text-align: center;">❌ ${i18n.t('error')}: ${msg}</div>`;
    }

    /**
     * Very basic markdown parser for display purposes
     */
    function parseMarkdown(text) {
        let html = text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Colorize the Signal
        if (html.includes("SIGNAL: BUY")) {
            html = html.replace("SIGNAL: BUY", `${i18n.t('col_signal')}: <span class='signal-buy'>${i18n.t('sig_buy')}</span>`);
        } else if (html.includes("SIGNAL: SELL")) {
            html = html.replace("SIGNAL: SELL", `${i18n.t('col_signal')}: <span class='signal-sell'>${i18n.t('sig_sell')}</span>`);
        } else if (html.includes("SIGNAL: WAIT")) {
            html = html.replace("SIGNAL: WAIT", `${i18n.t('col_signal')}: <span class='signal-wait'>${i18n.t('sig_wait')}</span>`);
        }

        return html;
    }

    // --- AI DISCOVERY DASHBOARD ---
    const discoverySection = document.getElementById('discovery-section');
    const discoveryGrid = document.getElementById('discovery-grid');

    async function loadDiscovery() {
        if (!discoverySection) return;

        discoverySection.style.display = 'block'; // Show container

        try {
            const res = await fetch('http://localhost:5000/discover');
            const opps = await res.json();

            if (opps.error) {
                discoveryGrid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:red;">Failed to load Discovery</div>`;
                return;
            }

            discoveryGrid.innerHTML = '';

            opps.forEach(stock => {
                const isPositive = stock.change >= 0;
                const changeClass = isPositive ? 'text-up' : 'text-down';
                const sign = isPositive ? '+' : '';

                // Card Color Hint based on signal
                let borderStyle = '';
                let sigColor = 'var(--text-secondary)';

                if (stock.signal.includes('Bullish')) {
                    borderStyle = 'border-color: rgba(34, 197, 94, 0.4);';
                    sigColor = '#22c55e';
                } else if (stock.signal.includes('Strong')) {
                    borderStyle = 'border-color: rgba(34, 197, 94, 0.8); box-shadow: 0 0 10px rgba(34, 197, 94, 0.2);';
                    sigColor = '#22c55e';
                }

                const card = document.createElement('div');
                card.className = 'discovery-card';
                card.style = borderStyle;
                card.innerHTML = `
                    <span class="disc-tag">${stock.category}</span>
                    <span class="disc-symbol">${stock.symbol}</span>
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span class="disc-price">${stock.price.toFixed(2)}</span>
                        <span class="disc-change ${changeClass}">${sign}${stock.change.toFixed(2)}%</span>
                    </div>
                    <span class="disc-sig" style="color: ${sigColor}">${stock.signal}</span>
                `;

                card.addEventListener('click', () => {
                    symbolInput.value = stock.symbol;
                    searchForm.dispatchEvent(new Event('submit'));
                });

                discoveryGrid.appendChild(card);
            });

        } catch (e) {
            console.error("Discovery Load Error", e);
        }
    }

    async function loadStockList() {
        try {
            const res = await fetch('http://localhost:5000/stocks');
            const stocks = await res.json();
            const dataList = document.getElementById('stock-list');

            dataList.innerHTML = '';
            stocks.forEach(symbol => {
                const option = document.createElement('option');
                option.value = symbol;
                dataList.appendChild(option);
            });
        } catch (e) {
            console.error("Failed to load stock list", e);
        }
    }

    // Call on Init
    loadStockList();
    loadDiscovery();

    // NEW: Check for targetStock from Screener
    const target = localStorage.getItem('targetStock');
    if (target) {
        symbolInput.value = target;
        localStorage.removeItem('targetStock'); // Clear it
        // Trigger search
        searchForm.dispatchEvent(new Event('submit'));
    }

    // I18N Listener
    window.addEventListener('langChange', () => {
        // Reload discovery
        loadDiscovery();

        // Re-render data if displaying
        if (currentSymbol) {
            updateData(currentSymbol, false);
        }

        // Update Wallet
        updateWalletUI();

        // Update Wallet
        updateWalletUI();

        // Update Favorites Title
        document.querySelector('[data-i18n="favorites"]').textContent = i18n.t('favorites');
    });

    // --- FAVORITES LOGIC ---
    const favSection = document.getElementById('favorites-section');
    const favGrid = document.getElementById('fav-grid');
    const btnFav = document.getElementById('btn-fav');

    function renderFavorites() {
        const list = watchlist.getList();
        if (list.length === 0) {
            favSection.style.display = 'block';
            favGrid.innerHTML = `<span style="color:var(--text-secondary); font-size:0.9rem;">${i18n.t('no_favs')}</span>`;
            return;
        }

        favSection.style.display = 'block';
        favGrid.innerHTML = '';

        list.forEach(symbol => {
            const tag = document.createElement('div');
            tag.className = 'fav-tag';
            tag.style = "background: rgba(255, 255, 255, 0.1); padding: 0.3rem 0.8rem; border-radius: 20px; cursor: pointer; border: 1px solid var(--glass-border); display: flex; align-items: center; gap: 0.5rem;";
            tag.innerHTML = `<span>${symbol}</span> <span style="font-size:0.8rem; color:#ef4444;" class="rem-fav">✖</span>`;

            // Navigate on click
            tag.addEventListener('click', (e) => {
                if (e.target.classList.contains('rem-fav')) return; // handled below
                symbolInput.value = symbol;
                searchForm.dispatchEvent(new Event('submit'));
            });

            // Remove btn
            tag.querySelector('.rem-fav').addEventListener('click', (e) => {
                e.stopPropagation();
                watchlist.remove(symbol);
                renderFavorites();
                // Update Star if current symbol
                if (currentSymbol === symbol) updateStarUI(symbol);
            });

            favGrid.appendChild(tag);
        });
    }

    function updateStarUI(symbol) {
        if (!symbol) return;
        const processSymbol = symbol.toUpperCase();
        if (watchlist.has(processSymbol)) {
            btnFav.innerHTML = '★'; // Solid Star
            btnFav.style.color = '#fbbf24'; // Gold
            btnFav.title = i18n.t('rem_fav');
        } else {
            btnFav.innerHTML = '☆'; // Hollow Star
            btnFav.style.color = 'var(--text-secondary)';
            btnFav.title = i18n.t('add_fav');
        }
    }

    btnFav.addEventListener('click', () => {
        if (!currentSymbol) return;
        watchlist.toggle(currentSymbol);
        updateStarUI(currentSymbol);
        renderFavorites();
    });

    // Listen for custom event from other tabs/modules
    window.addEventListener('favChange', () => {
        renderFavorites();
        if (currentSymbol) updateStarUI(currentSymbol);
    });

    // Init
    renderFavorites();

    // --- Tab Switching Logic ---
    window.switchTab = (tab) => {
        const chartC = document.getElementById('chart-container');
        const fundV = document.getElementById('fundamentals-view');
        const techV = document.getElementById('technical-view');
        const btns = document.querySelectorAll('.tab-btn');

        // Hide all
        chartC.style.display = 'none';
        fundV.style.display = 'none';
        techV.style.display = 'none';
        btns.forEach(b => b.classList.remove('active'));

        // Show selected
        if (tab === 'chart') {
            chartC.style.display = 'block';
            btns[0].classList.add('active');
        } else if (tab === 'fund') {
            fundV.style.display = 'block';
            btns[1].classList.add('active');
        } else if (tab === 'tech') {
            techV.style.display = 'block';
            btns[2].classList.add('active');
        }
    };

    // --- Technical Scorecard Render ---
    function renderTechnicalScore(techData) {
        if (!techData || !techData.score) return;

        // 1. Score Dial
        const scoreVal = document.getElementById('tech-score-val');
        const scoreCircle = document.getElementById('tech-score-circle');
        const sentiment = document.getElementById('tech-sentiment');

        scoreVal.textContent = techData.score;
        sentiment.textContent = techData.sentiment;

        // Color Logic
        let color = '#fbbf24'; // Neutral
        if (techData.score >= 65) color = '#22c55e'; // Green
        if (techData.score <= 35) color = '#ef4444'; // Red

        scoreCircle.style.borderColor = color;
        scoreVal.style.color = color;
        sentiment.style.color = color;

        // 2. Signals Table
        const tbody = document.getElementById('tech-signals-body');
        tbody.innerHTML = '';

        techData.signals.forEach(sig => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05);">${sig.name}</td>
                <td style="padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05); font-weight:bold;">${sig.val}</td>
                <td style="padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span class="signal-badge ${sig.act}">${sig.act}</span>
                </td>
                <td style="padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05); opacity:0.8; font-size:0.9rem;">${sig.desc}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Handle URL Params (e.g. from Heatmap)
    const urlParams = new URLSearchParams(window.location.search);
    const urlSymbol = urlParams.get('symbol');
    if (urlSymbol) {
        symbolInput.value = urlSymbol;
        setTimeout(() => searchForm.dispatchEvent(new Event('submit')), 100);
    }
});
let currentSymbol = null; // Track current symbol global or scoped up
