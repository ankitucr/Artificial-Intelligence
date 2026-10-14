// =====================================================================
// 👁️ PKA MARKET_STREAM.JS - THE OMNISCIENT EYES [FINAL GOD-MODE]
// TradingView Technicals + DuckDuckGo Sentiment (100% API-FREE)
// =====================================================================

const analyze = require("tradingview-technical-analysis");
const { search } = require("duck-duck-scrape");

class MarketStreamer {
    constructor() {
        console.log("👁️ [PKA_EYES] Market Streamer V3.0 (API-Free) Online.");
        this.marketState = { crypto: {}, stocks: {}, web_sentiment: "Neutral", overall_mood: "Neutral" };
    }

    // 🪙 CRYPTO VISION (TradingView Native)
    async fetchCryptoPulse(symbol, exchange = "BINANCE") {
        try {
            const ticker = `${exchange}:${symbol}`;
            const res = await analyze([ticker], ['1d']);
            
            if (!res || !res[ticker] || !res[ticker].signals) return null;

            const signals = res[ticker].signals['1d'];
            const recommendation = signals["Recommend.All"] || "NEUTRAL";
            
            let mood = recommendation;
            if (recommendation.includes("STRONG_BUY")) mood = "Aggressive Bull 🚀";
            else if (recommendation.includes("STRONG_SELL")) mood = "Severe Bear 📉";

            this.marketState.crypto[symbol] = { 
                recommendation: recommendation, 
                buy_pressure: signals.BUY,
                sell_pressure: signals.SELL,
                mood: mood 
            };
            return this.marketState.crypto[symbol];
        } catch (e) { return null; }
    }

    // 📈 GLOBAL STOCKS VISION (TradingView Native)
    async fetchStockPulse(symbol, exchange) { 
        try {
            const ticker = `${exchange}:${symbol}`;
            const res = await analyze([ticker], ['1d']);
            
            if (!res || !res[ticker] || !res[ticker].signals) return null;

            const signals = res[ticker].signals['1d'];
            const recommendation = signals["Recommend.All"] || "NEUTRAL";

            this.marketState.stocks[symbol] = { 
                recommendation: recommendation,
                buy_pressure: signals.BUY,
                sell_pressure: signals.SELL
            };
            return this.marketState.stocks[symbol];
        } catch (e) { return null; }
    }

    // 🕸️ DUCKDUCKGO WEB SENTIMENT (The True Market Whisperer)
    async fetchWebSentiment() {
        console.log("🕸️ [WEB_EYES] Scanning Deep Web for global market sentiment...");
        try {
            // Searching for the latest market news from the past 24 hours
            const query = "global stock market and crypto sentiment news today";
            const searchResults = await search(query, { safeSearch: "moderate", time: "d" });
            
            if (searchResults.results && searchResults.results.length > 0) {
                // Combine title and description for analysis
                const headline = searchResults.results[0].title + " " + searchResults.results[0].description;
                
                // PKA's own AI Sentiment Logic
                let bullScore = (headline.match(/(rally|surge|high|buy|bull|gain|up)/gi) || []).length;
                let bearScore = (headline.match(/(crash|drop|low|sell|bear|loss|down)/gi) || []).length;

                let mood = "Neutral";
                if (bullScore > bearScore) mood = "Web is Bullish 🌐🚀";
                else if (bearScore > bullScore) mood = "Web is Bearish 🌐📉";

                this.marketState.web_sentiment = {
                    mood: mood,
                    bull_keywords_found: bullScore,
                    bear_keywords_found: bearScore,
                    latest_headline: headline.substring(0, 100) + "..."
                };
            }
        } catch (e) {
            console.log("⚠️ DuckScraper offline. Skipping web sentiment.");
        }
    }

    // 🧠 THE COMBINED PULSE (Syncing everything for PKA Brain)
    async getGlobalMarketPulse() {
        console.log("\n🌀 [SCAN] Initiating API-Free Global Market Sync...");

        // 1. Fetching all market data & web news concurrently (Super Fast!)
        await Promise.all([
            this.fetchCryptoPulse("BTCUSDT", "BINANCE"),
            this.fetchCryptoPulse("ETHUSDT", "BINANCE"),
            this.fetchStockPulse("NIFTY", "NSE"), // Indian Market (Nifty 50)
            this.fetchStockPulse("AAPL", "NASDAQ"), // US Market (Apple)
            this.fetchWebSentiment() // 🟢 NEW: DuckDuckGo Sentiment
        ]);

        // 2. Calculate Overall AI Sentiment (Combining Technicals + Web News)
        let bullCount = 0;
        let bearCount = 0;
        
        const allAssets = [...Object.values(this.marketState.crypto), ...Object.values(this.marketState.stocks)];
        allAssets.forEach(c => { 
            if(c.recommendation && c.recommendation.includes("BUY")) bullCount++; 
            if(c.recommendation && c.recommendation.includes("SELL")) bearCount++; 
        });

        // Web sentiment carries 2x weight because news drives the market!
        if (this.marketState.web_sentiment && this.marketState.web_sentiment.mood.includes("Bullish")) bullCount += 2; 
        if (this.marketState.web_sentiment && this.marketState.web_sentiment.mood.includes("Bearish")) bearCount += 2;

        if (bullCount > bearCount) this.marketState.overall_mood = "Bullish Lean 📈";
        else if (bearCount > bullCount) this.marketState.overall_mood = "Bearish Lean 📉";
        else this.marketState.overall_mood = "Neutral Market ⚖️";

        return {
            timestamp: new Date().toISOString(),
            sentiment: this.marketState.overall_mood,
            data: this.marketState
        };
    }
}

module.exports = new MarketStreamer();
