// =====================================================================
// 👁️ PKA FEEDER.JS : THE OMNISCIENT DATA INJECTOR (V3 FINAL)
// 100% API-FREE | Live Global Markets (60 Assets) | Web News Scraper
// =====================================================================

const fs = require('fs');
const path = require('path');
const analyze = require("tradingview-technical-analysis"); // 📈 TradingView Native
const { search } = require("duck-duck-scrape"); // 🕸️ DuckDuckGo Scraper

// 📁 PATHS
const textMemoryPath = path.join(__dirname, "data", "memory.json");
const marketMemoryPath = path.join(__dirname, "data", "market_memory.json");

// Ensure data directory exists
if (!fs.existsSync(path.join(__dirname, "data"))) fs.mkdirSync(path.join(__dirname, "data"), { recursive: true });

// =========================================================
// 🌍 GLOBAL ASSET UNIVERSE (60 Top Tier Assets Synced with Evolve)
// =========================================================
const MARKET_ASSETS = {
    CRYPTO: [
        "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:BNBUSDT", "BINANCE:SOLUSDT", "BINANCE:XRPUSDT",
        "BINANCE:ADAUSDT", "BINANCE:DOGEUSDT", "BINANCE:AVAXUSDT", "BINANCE:LINKUSDT", "BINANCE:MATICUSDT",
        "BINANCE:DOTUSDT", "BINANCE:TRXUSDT", "BINANCE:SHIBUSDT", "BINANCE:LTCUSDT", "BINANCE:BCHUSDT"
    ],
    FOREX: [
        "OANDA:XAUUSD", "OANDA:EURUSD", "OANDA:GBPUSD", "OANDA:USDJPY", "OANDA:USDCAD",
        "OANDA:AUDUSD", "OANDA:NZDUSD", "OANDA:USDCHF", "OANDA:EURGBP", "OANDA:EURJPY",
        "OANDA:GBPJPY", "OANDA:AUDJPY", "OANDA:EURCHF", "OANDA:AUDNZD", "OANDA:XAGUSD" // 🏆 Gold & Silver
    ],
    STOCKS_INDIA: [
        "NSE:RELIANCE", "NSE:TCS", "NSE:HDFCBANK", "NSE:INFY", "NSE:ICICIBANK",
        "NSE:SBIN", "NSE:BHARTIARTL", "NSE:ITC", "NSE:HINDUNILVR", "NSE:LT",
        "NSE:TATAMOTORS", "NSE:SUNPHARMA", "NSE:M&M", "NSE:MARUTI", "NSE:AXISBANK"
    ],
    STOCKS_GLOBAL: [
        "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:GOOGL", "NASDAQ:AMZN", "NASDAQ:NVDA",
        "NASDAQ:TSLA", "NASDAQ:META", "NYSE:BRK.B", "NYSE:LLY", "NYSE:V",
        "NYSE:JPM", "NYSE:UNH", "NYSE:WMT", "NYSE:MA", "NYSE:PG"
    ]
};

class PKA_DataFeeder {
    constructor() {
        console.log("👁️ [PKA SENSES] API-Free Feeder Core Online.");

        // Ensure Market Memory File exists
        if (!fs.existsSync(marketMemoryPath)) {
            fs.writeFileSync(marketMemoryPath, JSON.stringify({ history: [] }, null, 2));
        }
    }

    // =========================================================
    // 🧹 1. SMART HYPER-CLEANUP (Protects DNA while cleaning junk)
    // =========================================================
    cleanKnowledgeBase() {
        console.log("🧹 [FEEDER] Running Neural Knowledge Cleanup...");
        try {
            if (!fs.existsSync(textMemoryPath)) return console.log("⚠️ memory.json not found. Skipping.");

            let memory = JSON.parse(fs.readFileSync(textMemoryPath, 'utf8'));

            const cleanText = (text) => {
                if (!text) return "";
                return text.replace(/<[^>]*>/g, ' ')
                           .replace(/\[(?!TRADE|MUTATE|SYS|TERMUX|MARKET)[^\]]*\]/gi, ' ') // Keep AGI Tags, remove other brackets
                           .replace(/\b(display|block|font|size|width|margin|color|css)\b/gi, ' ')
                           .replace(/\s+/g, ' ')
                           .trim();
            };

            // Clean Short-Term History
            if (memory.history) {
                memory.history = memory.history.map(node => ({ ...node, text: cleanText(node.text) })).filter(node => node.text.length > 2);
            }
            // Clean Long-Term Core Beliefs
            if (memory.longTerm) {
                memory.longTerm = memory.longTerm.map(node => ({ ...node, text: cleanText(node.text) })).filter(node => node.text.length > 2);
            }

            fs.writeFileSync(textMemoryPath, JSON.stringify(memory, null, 2));
            console.log("🚀 [SYSTEM_HEALED] Memory Sanitized & DNA Protected!");

        } catch (e) {
            console.error("❌ Critical Knowledge Error: " + e.message);
        }
    }

    // =========================================================
    // 📡 2. LIVE MARKET INJECTION (TradingView 60-Asset Scanner)
    // =========================================================
    async fetchAndStoreMarketData() {
        console.log(`\n📡 [FEEDER] Pulling Global Market Snapshot via TradingView...`);
        let snapshot = {
            timestamp: new Date().toISOString(),
            markets: {}
        };

        // Har market category se 1 random asset uthayenge ek single snapshot ke liye
        const targets = [
            MARKET_ASSETS.CRYPTO[Math.floor(Math.random() * MARKET_ASSETS.CRYPTO.length)],
            MARKET_ASSETS.FOREX[Math.floor(Math.random() * MARKET_ASSETS.FOREX.length)],
            MARKET_ASSETS.STOCKS_INDIA[Math.floor(Math.random() * MARKET_ASSETS.STOCKS_INDIA.length)],
            MARKET_ASSETS.STOCKS_GLOBAL[Math.floor(Math.random() * MARKET_ASSETS.STOCKS_GLOBAL.length)]
        ];

        try {
            const tvResults = await analyze(targets, ['1d']);

            targets.forEach(ticker => {
                if (tvResults[ticker] && tvResults[ticker].signals) {
                    const signals = tvResults[ticker].signals['1d'];
                    snapshot.markets[ticker] = {
                        recommendation: signals["Recommend.All"] || "NEUTRAL",
                        buyStrength: signals.BUY,
                        sellStrength: signals.SELL
                    };
                } else {
                    snapshot.markets[ticker] = { status: "Data Unavailable" };
                }
            });

            // 💾 SAVE TO PKA's LONG-TERM MARKET MEMORY
            let memory = JSON.parse(fs.readFileSync(marketMemoryPath, 'utf8'));
            if (memory.history.length > 1000) memory.history.shift(); // Prevent phone lag
            memory.history.push(snapshot);
            
            fs.writeFileSync(marketMemoryPath, JSON.stringify(memory, null, 2));
            console.log(`🧠 [FEEDER SUCCESS] Multi-Market Snapshot injected into memory.`);

        } catch (e) {
            console.error("❌ TradingView Fetch Error:", e.message);
        }
    }

    // =========================================================
    // 📰 3. AUTONOMOUS NEWS INJECTOR (DuckDuckGo Sentiment)
    // =========================================================
    async injectLiveNews() {
        console.log(`📰 [SENSES] Scanning Deep Web for Global Financial News...`);
        
        // Randomly search for Crypto, Forex, or Stock news
        const topics = ["Gold XAUUSD live market news", "Crypto Bitcoin sudden price movement reasons", "Stock market global crash or rally today"];
        const query = topics[Math.floor(Math.random() * topics.length)];

        try {
            const searchResults = await search(query, { safeSearch: "moderate", time: "d" }); // 'd' means past day news
            
            if (searchResults.results && searchResults.results.length > 0) {
                const newsSnippet = searchResults.results[0].description;
                
                // PKA ki memory me as a 'System' inject karna
                let textMemory = JSON.parse(fs.readFileSync(textMemoryPath, 'utf8'));
                
                textMemory.history.push({
                    id: `NEWS-${Date.now()}`,
                    role: "system",
                    text: `[LIVE WEB NEWS]: ${newsSnippet}`,
                    importance: 15,
                    category: "market_sentiment",
                    time: new Date().toLocaleString()
                });

                fs.writeFileSync(textMemoryPath, JSON.stringify(textMemory, null, 2));
                console.log(`✅ [NEWS INJECTED] PKA just read the latest news: ${newsSnippet.substring(0, 50)}...`);
            }
        } catch (e) {
            console.log("⚠️ DuckScraper offline for news. Skipping cycle.");
        }
    }

    // =========================================================
    // ⚙️ 4. AUTONOMOUS FEEDER LOOP
    // =========================================================
    start() {
        console.log("🔄 Starting God-Mode Autonomous Feeder Loop...");

        // On Startup
        this.cleanKnowledgeBase();
        this.fetchAndStoreMarketData();
        this.injectLiveNews();

        // Continuous Senses (Every 5 minutes)
        setInterval(() => {
            this.cleanKnowledgeBase();
            this.fetchAndStoreMarketData();
            this.injectLiveNews();
        }, 300000); // 300,000 ms = 5 minutes
    }
}

// 🚀 IGNITION
const feeder = new PKA_DataFeeder();
if (require.main === module) {
    feeder.start();
}

module.exports = feeder;
