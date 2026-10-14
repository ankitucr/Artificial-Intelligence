// =====================================================================
// 💪 PKA BROKER API : ANTI-CRASH & SELF-HEALING VERSION [FINAL GOD-MODE]
// 100% API-FREE | Autonomous Paper Trading | Dynamic PnL Math Engine
// =====================================================================

const fs = require("fs");
const path = require("path");

const portfolioPath = path.join(__dirname, "..", "runtime", "portfolio.json");

class PKABrokerAPI {
    constructor() {
        console.log("💪 [BROKER_API] Core Synchronized. API-Free Broker Ready.");
        this.initPortfolio();
    }

    initPortfolio() {
        // Ensure directory exists
        const dir = path.dirname(portfolioPath);
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

        if (!fs.existsSync(portfolioPath)) {
            const initialData = { 
                balance: 100000.00, 
                marginUsed: 0.00, 
                totalPnL: 0.00, 
                winRate: 0, 
                tradesWon: 0, 
                tradesLost: 0, 
                positions: [] 
            };
            fs.writeFileSync(portfolioPath, JSON.stringify(initialData, null, 2));
        }
        this.portfolio = JSON.parse(fs.readFileSync(portfolioPath, 'utf8'));
    }

    savePortfolio() { 
        fs.writeFileSync(portfolioPath, JSON.stringify(this.portfolio, null, 2)); 
    }

    // =========================================================
    // ⚡ 1. ORDER EXECUTION (Safety Guarded)
    // =========================================================
    async executeTrade(action, asset, type = "MARKET", leverage = 1, amount = 1000) {
        // 🛡️ THE ANTI-CRASH GUARD: Verify inputs before execution
        if (!action || !asset) {
            console.log("⚠️ [PKA_GUARD] Corrupt Order Data Received. Skipping Pulse...");
            return { success: false };
        }

        const safeAction = String(action).toUpperCase();
        const safeAsset = String(asset).toUpperCase();

        console.log(`\n⚡ [BROKER PUNCH] Initiating ${safeAction} Order for ${safeAsset} (Lev: ${leverage}x)...`);

        const marginRequired = parseFloat(amount) / parseFloat(leverage);
        
        if (this.portfolio.balance < marginRequired) {
            console.log("❌ [REJECTED] Insufficient Virtual Balance!");
            return { success: false };
        }

        // Create Neural Position Object
        const position = {
            id: `TRD-${Date.now()}`, 
            action: safeAction, 
            asset: safeAsset,
            leverage: parseFloat(leverage), 
            margin: marginRequired,
            status: "OPEN", 
            timestamp: new Date().toISOString()
        };

        this.portfolio.balance -= marginRequired;
        this.portfolio.marginUsed += marginRequired;
        this.portfolio.positions.push(position);
        this.savePortfolio();

        console.log(`✅ [ORDER FILLED] ID: ${position.id} | Margin Locked: $${marginRequired.toFixed(2)}`);
        return { success: true, trade: position };
    }

    // =========================================================
    // 🎯 2. RISK MANAGER & PNL CALCULATOR
    // =========================================================
    manageOpenPositions(marketData) {
        if (!marketData || !marketData.data) return { closedTrades: 0 };

        let closedCount = 0;
        let updatedPositions = [];

        // Flatten market data for easy access
        const livePrices = { ...marketData.data.crypto, ...marketData.data.stocks };

        this.portfolio.positions.forEach(pos => {
            if (pos.status !== "OPEN") {
                updatedPositions.push(pos);
                return;
            }

            const liveSignal = livePrices[pos.asset];
            if (!liveSignal || !liveSignal.recommendation) {
                updatedPositions.push(pos);
                return;
            }

            let shouldClose = false;
            let pnl = 0; // Simulated PnL
            let outcome = "DRAW";

            // 🧠 Signal Reversal Logic (Dynamic SL/TP based on TradingView)
            if (pos.action === "BUY" && liveSignal.recommendation.includes("STRONG_SELL")) {
                shouldClose = true;
                pnl = -(pos.margin * 0.2); // 20% simulated loss on trend reversal
                outcome = "LOSS";
            } 
            else if (pos.action === "SELL" && liveSignal.recommendation.includes("STRONG_BUY")) {
                shouldClose = true;
                pnl = -(pos.margin * 0.2); // 20% simulated loss
                outcome = "LOSS";
            }
            // Take Profit Condition
            else if (pos.action === "BUY" && liveSignal.recommendation === "STRONG_BUY") {
                // If it's strongly in our favor, simulate taking a quick 30% profit
                if (Math.random() > 0.7) { 
                    shouldClose = true;
                    pnl = (pos.margin * 0.3);
                    outcome = "WIN";
                }
            }
            else if (pos.action === "SELL" && liveSignal.recommendation === "STRONG_SELL") {
                if (Math.random() > 0.7) { 
                    shouldClose = true;
                    pnl = (pos.margin * 0.3);
                    outcome = "WIN";
                }
            }

            if (shouldClose) {
                console.log(`🔔 [TRADE CLOSED] ${pos.asset} | Outcome: ${outcome} | PnL: $${pnl.toFixed(2)}`);
                
                // Math Updates
                this.portfolio.balance += pos.margin; // Unlock margin
                this.portfolio.marginUsed -= pos.margin;
                this.portfolio.balance += pnl; // Add/Subtract profit or loss
                this.portfolio.totalPnL += pnl;
                
                if (outcome === "WIN") this.portfolio.tradesWon++;
                if (outcome === "LOSS") this.portfolio.tradesLost++;

                const totalTrades = this.portfolio.tradesWon + this.portfolio.tradesLost;
                this.portfolio.winRate = ((this.portfolio.tradesWon / totalTrades) * 100).toFixed(2);
                
                closedCount++;
            } else {
                updatedPositions.push(pos);
            }
        });

        if (closedCount > 0) {
            this.portfolio.positions = updatedPositions;
            this.savePortfolio();
        }

        return { closedTrades: closedCount };
    }
}

module.exports = new PKABrokerAPI();
