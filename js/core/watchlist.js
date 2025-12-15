/**
 * Watchlist Manager
 * Handles saving/removing favorite stocks in localStorage.
 */
class WatchlistManager {
    constructor() {
        this.STORAGE_KEY = 'stockify_watchlist';
        this.favorites = this.load();
    }

    load() {
        const data = localStorage.getItem(this.STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    }

    save() {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.favorites));
        // Dispatch event for UI updates
        window.dispatchEvent(new CustomEvent('favChange', { detail: this.favorites }));
    }

    add(symbol) {
        if (!symbol) return;
        symbol = symbol.toUpperCase();
        if (!this.favorites.includes(symbol)) {
            this.favorites.push(symbol);
            this.save();
            return true;
        }
        return false;
    }

    remove(symbol) {
        if (!symbol) return;
        symbol = symbol.toUpperCase();
        this.favorites = this.favorites.filter(s => s !== symbol);
        this.save();
    }

    toggle(symbol) {
        if (this.has(symbol)) {
            this.remove(symbol);
            return false; // Removed
        } else {
            this.add(symbol);
            return true; // Added
        }
    }

    has(symbol) {
        if (!symbol) return false;
        return this.favorites.includes(symbol.toUpperCase());
    }

    getList() {
        return this.favorites;
    }
}

const watchlist = new WatchlistManager();
