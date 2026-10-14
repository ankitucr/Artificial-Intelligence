// =====================================================================
// 👁️ PKA FEEDER.JS : THE OMNISCIENT DATA INJECTOR (SENSES)
// Knowledge Cleanup + Live Market Data Fetcher
// =====================================================================

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// 🔑 API KEYS (evolve.js wali same keys yahan dalengi)
const CMC_API_KEY = "be505f9a91e64ce8b47c061d502227d1";
const META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJmYzMxZGIwMjQwMWM1NGY3YTI2MTRlYjFkMGRhZTVmMyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVzdC1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcnBjLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFhcGktcmVhbC10aW1lLXN0cmVhbWluZy1hcGkiLCJtZXRob2RzIjpbIm1ldGFhcGktYXBpOndzOnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtZXRhc3RhdHMtYXBpIiwibWV0aG9kcyI6WyJtZXRhc3RhdHMtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6InJpc2stbWFuYWdlbWVudC1hcGkiLCJtZXRob2RzIjpbInJpc2stbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoiY29weWZhY3RvcnktYXBpIiwibWV0aG9kcyI6WyJjb3B5ZmFjdG9yeS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibXQtbWFuYWdlci1hcGkiLCJtZXRob2RzIjpbIm10LW1hbmFnZXItYXBpOnJlc3Q6ZGVhbGluZzoqOioiLCJtdC1tYW5hZ2VyLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJiaWxsaW5nLWFwaSIsIm1ldGhvZHMiOlsiYmlsbGluZy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfV0sImlnbm9yZVJhdGVMaW1pdHMiOmZhbHNlLCJ0b2tlbklkIjoiMjAyMTAyMTMiLCJpbXBlcnNvbmF0ZWQiOmZhbHNlLCJyZWFsVXNlcklkIjoiZmMzMWRiMDI0MDFjNTRmN2EyNjE0ZWIxZDBkYWU1ZjMiLCJpYXQiOjE3NzE3ODAxNDh9.BUzQmwj9y8RkC39O5PnoL12dPGmCUr4VysZUuyBKGB57CCuZr7Wds24SvWXZRY6G2iQijQ21ioKrqrRZchn1QfKfJ9ITBMjFuQdI6s065ubiCG-Mrsagtzwo_7-LJ0ZAmJD87Aog3bFHjF83zY57azsfKNy9XkTuvQG5kvClcSUK0oSyNDv9INv2aP5jRFP91lHZAiDUO2cN8Ufx_M9bsq4Hw-kW-FAaZT_icqUKSKXhgIcrtooPYxBolTqe1shfd5Ufn1TpEbI6HFoeUUOLPGGV5Wo39AT6kQBZ6aeiAGFBc3jrGsAOczU3he3YulzRlUJvttIo6SEOj5KeYkOv7v_2x7lUyQL23nwAszi5Ppnj-B185TnfW2sJoAbA6ZfiA-uwMTBHib5ZSMM2uFhr5i00YvIZy0mBYcuSK8h-yPgx4WtPv640cLgCSkz86HYonfFGoTS4CpO6gyFPyty-K24MDCAPxTeSzQuSk26auOBZswysArp8JXHUJjltdOj7A_gB5slnTxGff6AiHXb7k0vxNdpzvIwfA1V_RbFstngAhVjl2KxQp49iN9mkB06u4jwdmmqjwXj8zXWSfXbqoaB4w4qG0lJD4q4z6flHnaJxYwLUQtjYookg9keObnpPguubQUoUFhMCWvA5-xul-xGWn6egGvNRTeMu6g2DG78";
const META_ACCOUNT_ID = "YOUR_METAAPI_ACCOUNT_ID_HERE";

// 📁 PATHS
const textMemoryPath = path.join(__dirname, "data", "memory.json");
const marketMemoryPath = path.join(__dirname, "data", "market_memory.json");

// Ensure data directory exists
if (!fs.existsSync(path.join(__dirname, "data"))) {
    fs.mkdirSync(path.join(__dirname, "data"));
}

class PKA_DataFeeder {
    constructor() {
        console.log("👁️ [PKA SENSES] Feeder Core Online.");
        
        // Ensure Market Memory File exists
        if (!fs.existsSync(marketMemoryPath)) {
            fs.writeFileSync(marketMemoryPath, JSON.stringify({ history: [] }, null, 2));
        }
    }

    // =========================================================
    // 🧹 1. HYPER-CLEANUP (Tumhara Purana Text Cleaner Upgraded)
    // =========================================================
    cleanKnowledgeBase() {
        console.log("🧹 [FEEDER] Running Knowledge Base Cleanup...");
        try {
            if (!fs.existsSync(textMemoryPath)) return console.log("⚠️ memory.json not found. Skipping.");
            
            let rawData = fs.readFileSync(textMemoryPath, 'utf8');
            let textToProcess = rawData;

            try {
                const parsed = JSON.parse(rawData);
                if (parsed.history && parsed.history[0]) {
                    textToProcess = parsed.history[0].text || JSON.stringify(parsed);
                }
            } catch (e) {
                // Not JSON, treat as raw text
            }

            // HTML & Junk Cleaning (Tumhari original regex)
            let cleanData = textToProcess
                .replace(/<[^>]*>/g, ' ')
                .replace(/\[[^\]]*\]/g, ' ')
                .replace(/\b(display|block|font|size|width|margin)\b/gi, ' ')
                .replace(/\s+/g, ' ')
                .trim();

            const jsonData = {
                history: [{
                    text: cleanData,
                    timestamp: new Date().toISOString(),
                    type: "deep_knowledge_injection"
                }]
            };

            fs.writeFileSync(textMemoryPath, JSON.stringify(jsonData, null, 2));
            console.log("🚀 [SYSTEM_HEALED] Text Knowledge Base Sanitized & Saved!");

        } catch (e) {
            console.error("❌ Critical Knowledge Error: " + e.message);
        }
    }

    // =========================================================
    // 📡 2. LIVE MARKET INJECTION (New God-Mode Power)
    // =========================================================
    async fetchAndStoreMarketData() {
        console.log(`\n📡 [FEEDER] Pulling Global Market Snapshot...`);
        let snapshot = {
            timestamp: new Date().toISOString(),
            crypto: {},
            forex: {},
            stocks: {}
        };

        // 🪙 CRYPTO DATA (Binance + CMC)
        try {
            const binanceRes = await axios.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
            snapshot.crypto = {
                asset: "BTC/USDT",
                price: parseFloat(binanceRes.data.lastPrice),
                change: parseFloat(binanceRes.data.priceChangePercent)
            };
        } catch (e) { snapshot.crypto = { error: "Binance Offline" }; }

        // 🌍 FOREX DATA (Exness via MetaAPI)
        try {
            if(META_ACCOUNT_ID && META_API_TOKEN && META_ACCOUNT_ID !== "YOUR_METAAPI_ACCOUNT_ID_HERE") {
                const url = `https://mt-client-api-v1.london.agiliumtrade.ai/users/current/accounts/${META_ACCOUNT_ID}/symbols/EURUSD/current-price`;
                const metaRes = await axios.get(url, { headers: { 'auth-token': META_API_TOKEN } });
                snapshot.forex = { asset: "EUR/USD", price: metaRes.data.bid };
            } else {
                snapshot.forex = { status: "Awaiting MetaAPI Keys" };
            }
        } catch (e) { snapshot.forex = { error: "MetaAPI Offline" }; }

        // 📈 STOCK DATA (Public Fallback / Indian Market Placeholder)
        // Yahan PKA automatically random simulate karega jab tak Angel One connect nahi hota
        snapshot.stocks = {
            asset: "NIFTY_50",
            status: "Simulated_Until_Angel_Auth",
            trend: Math.random() > 0.5 ? "UP" : "DOWN",
            volatility: (Math.random() * 2).toFixed(2)
        };

        // 💾 SAVE TO PKA's LONG-TERM MARKET MEMORY
        try {
            let memory = JSON.parse(fs.readFileSync(marketMemoryPath, 'utf8'));
            
            // Limit array to last 1000 snapshots to prevent phone lag
            if (memory.history.length > 1000) memory.history.shift(); 
            
            memory.history.push(snapshot);
            fs.writeFileSync(marketMemoryPath, JSON.stringify(memory, null, 2));
            
            console.log(`🧠 [FEEDER SUCCESS] Market Snapshot injected into PKA's memory.`);
        } catch (e) {
            console.error("❌ Memory Save Error:", e.message);
        }
    }

    // =========================================================
    // ⚙️ 3. AUTONOMOUS FEEDER LOOP
    // =========================================================
    start() {
        console.log("🔄 Starting Autonomous Feeder Loop...");
        
        // Start me ek baar clean up run karega
        this.cleanKnowledgeBase();
        
        // Har 5 minute (300,000 ms) mein market ka data khichega
        this.fetchAndStoreMarketData();
        setInterval(() => {
            this.fetchAndStoreMarketData();
        }, 300000); 
    }
}

// 🚀 IGNITION
const feeder = new PKA_DataFeeder();
// Agar direct run kiya jaye (node feeder.js)
if (require.main === module) {
    feeder.start();
}

module.exports = feeder;
