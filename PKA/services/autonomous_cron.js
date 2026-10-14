// =====================================================================
// ❤️ PKA AUTONOMOUS CRON : THE HEARTBEAT & NEURAL DECISION PULSE (V3)
// 100% API-FREE | TradingView Live Sync | Autonomous Paper Trading
// =====================================================================

const fs = require('fs');
const path = require('path');
const analyze = require("tradingview-technical-analysis"); // 📈 Live TV Signals

// 🧠 Connect to PKA Core
let brain; try { brain = require("../core/brain"); } catch(e){}
let memory; try { memory = require("../core/memory"); } catch(e){}

const PORTFOLIO_PATH = path.join(__dirname, "..", "runtime", "portfolio.json");

class AutonomousHeartbeat {
    constructor() {
        console.log("\x1b[35m%s\x1b[0m", "❤️ [CRON ENGINE] God-Mode Neural Heartbeat Started...");
        this.isRunning = false;
        this.interval = null;
        this.failedAttempts = 0;
        this.pulseCount = 0;

        // Ensure Portfolio Exists
        const runtimeDir = path.dirname(PORTFOLIO_PATH);
        if (!fs.existsSync(runtimeDir)) fs.mkdirSync(runtimeDir, { recursive: true });
        if (!fs.existsSync(PORTFOLIO_PATH)) {
            fs.writeFileSync(PORTFOLIO_PATH, JSON.stringify({ balance: 100000, marginUsed: 0, positions: [] }, null, 2));
        }
    }

    // =========================================================
    // 📊 THE NEURAL CYCLE (Live Portfolio Management)
    // =========================================================
    async runCycle() {
        if (this.isRunning) return;
        this.isRunning = true;

        this.pulseCount++;
        console.log(`\n\x1b[36m%s\x1b[0m`, `⏳ [PULSE ${this.pulseCount}] Waking up PKA for Portfolio Audit...`);

        try {
            let portfolio = JSON.parse(fs.readFileSync(PORTFOLIO_PATH, 'utf8'));
            
            if (!portfolio.positions || portfolio.positions.length === 0) {
                console.log("💤 [CRON] No open positions. System resting.");
            } else {
                let closedTrades = 0;
                let activeAssets = [...new Set(portfolio.positions.map(p => `BINANCE:${p.asset.toUpperCase()}`))]; // Assuming Crypto for now

                // STEP 1: Fetch Live TV Signals for all open positions
                console.log(`📡 Fetching live TradingView data for active trades: ${activeAssets.join(", ")}`);
                const tvResults = await analyze(activeAssets, ['15m', '1d']);

                // STEP 2: Evaluate and Manage Positions
                let updatedPositions = [];

                for (let trade of portfolio.positions) {
                    let ticker = `BINANCE:${trade.asset.toUpperCase()}`;
                    let tvData = tvResults[ticker];

                    let shouldClose = false;
                    let closeReason = "";

                    if (tvData && tvData.signals) {
                        const signal15m = tvData.signals['15m']["Recommend.All"];
                        const signal1d = tvData.signals['1d']["Recommend.All"];

                        // 🧠 AI Logic: If we are LONG (BUY) but market turns STRONG_SELL -> Panic Close!
                        if (trade.action === "BUY" && (signal15m.includes("STRONG_SELL") || signal1d.includes("STRONG_SELL"))) {
                            shouldClose = true;
                            closeReason = "Market turned Bearish (STRONG_SELL detected)";
                        }
                        // If we are SHORT (SELL) but market turns STRONG_BUY -> Panic Close!
                        else if (trade.action === "SELL" && (signal15m.includes("STRONG_BUY") || signal1d.includes("STRONG_BUY"))) {
                            shouldClose = true;
                            closeReason = "Market turned Bullish (STRONG_BUY detected)";
                        }
                    }

                    if (shouldClose) {
                        console.log(`🔔 \x1b[31m[TRADE CLOSED] Executed exit for ${trade.asset} | Reason: ${closeReason}\x1b[0m`);
                        portfolio.balance += trade.margin; // Refund margin (Simplified paper trading math)
                        portfolio.marginUsed -= trade.margin;
                        closedTrades++;

                        // Inject learning into memory
                        if (memory && memory.add) {
                            memory.add("system", `Closed trade for ${trade.asset} because ${closeReason}`);
                        }
                    } else {
                        updatedPositions.push(trade); // Keep open
                    }
                }

                // Save Updated Portfolio
                portfolio.positions = updatedPositions;
                fs.writeFileSync(PORTFOLIO_PATH, JSON.stringify(portfolio, null, 2));

                if (closedTrades === 0) console.log("✅ [CRON] All neural positions are stable.");
            }

            this.failedAttempts = 0;

            // =========================================================
            // 🟢 AI SENTIMENT CHECK (PKA's Intuition via Web & LTM)
            // =========================================================
            if (this.pulseCount % 5 === 0) {
                console.log("🤖 [AI_PULSE] Triggering deep systemic health check...");
                
                if (brain && brain.process) {
                    // Triggering brain to think about market risks. It will use DuckDuckGo automatically!
                    await brain.process("Analyze global market Black Swan risk today");
                }
                
                if (memory && memory.getRelevantBeliefs) {
                    const beliefs = memory.getRelevantBeliefs("risk crash black swan", 1);
                    console.log(`📡 [PKA INTUITION]: ${beliefs !== "No long-term memories formed yet." ? beliefs : "Market seems normal."}`);
                }
            }

        } catch (error) {
            this.failedAttempts++;
            console.error(`\x1b[31m%s\x1b[0m`, `❌ [CRON WARNING] Heartbeat cycle failed: ${error.message}`);

            if (this.failedAttempts >= 3) {
                console.log(`\x1b[41m%s\x1b[0m`, `🛑 [CRITICAL] Multiple Failures. Initiating Self-Healing Cooldown...`);
                this.stop();
                setTimeout(() => this.start(60000), 120000); // Resume after 2 mins
            }
        } finally {
            this.isRunning = false;
        }
    }

    // =========================================================
    // 🚀 IGNITION (Start/Stop Control)
    // =========================================================
    start(intervalMs = 60000) {
        if (this.interval) clearInterval(this.interval);
        console.log(`⏱️ [CRON] Heartbeat set to pulse every ${intervalMs / 1000} seconds.`);

        this.runCycle(); // Run immediately on start
        this.interval = setInterval(() => this.runCycle(), intervalMs);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            console.log("⏸️ [CRON] Heartbeat paused.");
        }
    }
}

module.exports = new AutonomousHeartbeat();
