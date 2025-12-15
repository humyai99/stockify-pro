/**
 * PortfolioManager Class
 * Handles Paper Trading logic: Buy, Sell, Balance, and Persistence.
 */
class PortfolioManager {
    constructor() {
        this.storageKey = 'stockify_portfolio_v1';
        this.data = this.loadData();
    }

    loadData() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
            return JSON.parse(stored);
        } else {
            // Initial State
            return {
                balance: 1000000, // Start with 1 Million THB/USD
                positions: [], // Array of { symbol, avgPrice, qty, entryDate }
                history: []   // Array of closed trades
            };
        }
    }

    saveData() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.data));
    }

    resetPortfolio() {
        localStorage.removeItem(this.storageKey);
        this.data = this.loadData();
        return this.data;
    }

    /**
     * Execute a BUY Order
     */
    buy(symbol, price, qty) {
        const cost = price * qty;
        if (cost > this.data.balance) {
            return { success: false, message: "ยอดเงินไม่พอ (Insufficient Balance)" };
        }

        // Deduct Balance
        this.data.balance -= cost;

        // Check if position exists
        const existing = this.data.positions.find(p => p.symbol === symbol);
        if (existing) {
            // Average Down
            const totalCost = (existing.avgPrice * existing.qty) + cost;
            existing.qty += qty;
            existing.avgPrice = totalCost / existing.qty;
        } else {
            // New Position
            this.data.positions.push({
                symbol: symbol,
                avgPrice: price,
                qty: qty,
                entryDate: new Date().toISOString()
            });
        }

        this.saveData();
        return { success: true, message: `ซื้อ ${symbol} จำนวน ${qty} หุ้น สำเร็จ!` };
    }

    /**
     * Execute a SELL Order
     */
    sell(symbol, price, qty) {
        const index = this.data.positions.findIndex(p => p.symbol === symbol);
        if (index === -1) {
            return { success: false, message: "ไม่พบหุ้นในพอร์ต (Position not found)" };
        }

        const pos = this.data.positions[index];
        if (qty > pos.qty) {
            return { success: false, message: "จำนวนหุ้นไม่พอขาย (Insufficient Quantity)" };
        }

        // Calculate Realized P/L
        const sellValue = price * qty;
        const buyCost = pos.avgPrice * qty;
        const profit = sellValue - buyCost;
        const profitPct = (profit / buyCost) * 100;

        // Add to Balance
        this.data.balance += sellValue;

        // Update Position
        pos.qty -= qty;
        if (pos.qty === 0) {
            this.data.positions.splice(index, 1); // Remove empty position
        }

        // Add to History
        this.data.history.unshift({
            symbol: symbol,
            action: 'SELL',
            price: price,
            qty: qty,
            profit: profit,
            date: new Date().toISOString()
        });

        this.saveData();
        return {
            success: true,
            message: `ขาย ${symbol} สำเร็จ! กำไร: ${profit.toFixed(2)} (${profitPct.toFixed(2)}%)`
        };
    }

    getPortfolioSummary() {
        return {
            balance: this.data.balance,
            positionCount: this.data.positions.length,
            positions: this.data.positions
        };
    }
}
