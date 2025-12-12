document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const symbolInput = document.getElementById('symbol-input');
    const resultContainer = document.getElementById('result-container');
    const resultOutput = document.getElementById('result-output');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Market Info Elements
    const marketInfo = document.getElementById('market-info');
    const displaySymbol = document.getElementById('tikz-symbol');
    const displayPrice = document.getElementById('tikz-price');
    const displayChange = document.getElementById('tikz-change');

    // News Elements
    const newsSection = document.getElementById('news-section');
    const newsList = document.getElementById('news-list');

    // Chart Elements
    const chartCard = document.getElementById('chart-card');
    const chartContainer = document.getElementById('chart-container');
    let chart;
    let candleSeries;

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
            tradeFeedback.textContent = "❌ Please search for a stock first.";
            tradeFeedback.style.color = "#ef4444";
            return;
        }

        const action = document.getElementById('trade-action').value;
        const qty = parseInt(document.getElementById('trade-qty').value);
        const priceText = displayPrice.textContent.replace(/,/g, '');
        const price = parseFloat(priceText);

        if (isNaN(price) || price <= 0) {
            tradeFeedback.textContent = "❌ Invalid Price Data.";
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

    // Backtest Button
    const btnBacktest = document.getElementById('btn-run-backtest');
    const backtestOverlay = document.getElementById('backtest-overlay');

    btnBacktest.addEventListener('click', async () => {
        const symbol = displaySymbol.textContent;
        if (!symbol || symbol === "SYMBOL") return;

        btnBacktest.textContent = "Running... ⏳";
        backtestOverlay.style.display = 'block';
        document.getElementById('bt-return').textContent = "...";

        try {
            const res = await fetch(`http://localhost:5000/backtest/${symbol}`);
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

            btnBacktest.textContent = "Run Backtest 🔙";

        } catch (e) {
            console.error(e);
            btnBacktest.textContent = "Error";
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

            if (data.error) {
                if (isInitialLoad) showError(data.error);
                return;
            }

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
                if (isInitialLoad) chart.timeScale().fitContent();
            }

            // Company Profile & Holders (Only render on initial load)
            if (isInitialLoad && data.profile) {
                const companySection = document.getElementById('company-section');
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
            }

            // Analysis
            const analysisResult = analyst.analyze(data);
            const formattedText = analyst.formatOutput(analysisResult);
            resultOutput.innerHTML = parseMarkdown(formattedText);

            if (isInitialLoad) resultContainer.style.display = 'block';

            // --- Investment Calculator Logic (Time-Based) ---
            const calcSection = document.getElementById('calculator-section');
            const budgetInput = document.getElementById('calc-budget');
            const durationInput = document.getElementById('calc-duration-val'); // New
            const unitInput = document.getElementById('calc-duration-unit'); // New
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
                    { name: "🏰 Bear Case", target1Y: cons.targetLow, color: "#f87171" },
                    { name: "⚖️ Base Case", target1Y: cons.targetMean, color: "#fbbf24" },
                    { name: "🚀 Bull Case", target1Y: cons.targetHigh, color: "#34d399" }
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
                    const profitClass = profit >= 0 ? 'text-success' : 'text-danger';
                    const profitColor = profit >= 0 ? '#34d399' : '#f87171';
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
        resultOutput.innerHTML = `<div style="color: #ef4444; font-weight: bold; text-align: center;">❌ Error: ${msg}</div>`;
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
            html = html.replace("SIGNAL: BUY", "SIGNAL: <span class='signal-buy'>BUY</span>");
        } else if (html.includes("SIGNAL: SELL")) {
            html = html.replace("SIGNAL: SELL", "SIGNAL: <span class='signal-sell'>SELL</span>");
        } else if (html.includes("SIGNAL: WAIT")) {
            html = html.replace("SIGNAL: WAIT", "SIGNAL: <span class='signal-wait'>WAIT</span>");
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
                    // Optional: Scroll to top or hide discovery? 
                    // Let's keep it visible for now or maybe collapse it.
                });

                discoveryGrid.appendChild(card);
            });

        } catch (e) {
            console.error("Discovery Load Error", e);
        }
    }

    // Call on Init
    loadDiscovery();

    // NEW: Check for targetStock from Screener
    const target = localStorage.getItem('targetStock');
    if (target) {
        symbolInput.value = target;
        localStorage.removeItem('targetStock'); // Clear it
        // Trigger search
        searchForm.dispatchEvent(new Event('submit'));
    }
});
