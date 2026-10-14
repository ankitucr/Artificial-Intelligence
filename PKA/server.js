const express = require("express");
const fsPromises = require("fs").promises;
const path = require("path");
const analyze = require("tradingview-technical-analysis");

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

const ROOT = process.cwd();
const FILES = { memory: path.join(ROOT, "data", "memory.json") };

// 🎯 [GOLD ONLY DICTIONARY] - Pika sirf in words ko pehchanega
const GOLD_WORDS = ["xauusd", "gold", "sona", "xau", "yellow metal", "gold spot"];

// 🎯 [API: SIRF XAUUSD KE LIYE]
app.post("/api/sync", async (req, res) => {
    // Agar user ne kuch nahi dala, toh default 'XAUUSD' le lega
    let symbol = req.body.symbol ? req.body.symbol.toLowerCase().trim() : "xauusd";

    // Agar word dictionary mein nahi hai, toh bhi forcefully XAUUSD par hi jayega
    if (!GOLD_WORDS.includes(symbol)) {
        console.log(`\x1b[33m[INFO] Unknown word '${symbol}', defaulting to XAUUSD.\x1b[0m`);
    }

    // TradingView par alag-alag sources try karne ka logic (agar ek fail ho toh dusra)
    const sourcesToTry = ["OANDA:XAUUSD", "TVC:GOLD", "FOREXCOM:XAUUSD"];
    let liveData = null;

    for (let target of sourcesToTry) {
        try {
            console.log(`\x1b[36m[FETCH] Trying ${target}...\x1b[0m`);
            const tv = await analyze([target], ['15m']);
            
            if (tv && tv[target] && tv[target].indicators && tv[target].indicators['15m']) {
                const ind = tv[target].indicators['15m'];
                const sig = tv[target].signals['15m'];
                
                liveData = {
                    symbol: "GOLD (XAUUSD)",
                    price: ind.close.toFixed(2),
                    signal: sig["Recommend.All"] || "NEUTRAL",
                    source: target
                };
                console.log(`\x1b[32m[SUCCESS] Data mil gaya ${target} se!\x1b[0m`);
                break; // Data mil gaya toh loop rok do
            }
        } catch (e) {
            console.log(`\x1b[31m[FAIL] ${target} block ho gaya ya fail hua.\x1b[0m`);
        }
    }

    if (liveData) {
        res.json({ status: "success", data: liveData });
    } else {
        res.status(500).json({ status: "failed", msg: "TradingView ne saare Gold sources block kar diye hain." });
    }
});

// 🧠 [BASIC CHAT ENGINE]
app.post("/chat", async (req, res) => {
    const userMsg = req.body.message ? req.body.message.toLowerCase() : "";
    let reply = "";

    // Pika abhi sirf rules par chal raha hai (If-Else)
    if (userMsg.includes("hello") || userMsg.includes("hi")) {
        reply = "Hello Ankit! Main Pika hoon. Main abhi sirf Gold (XAUUSD) ko track kar raha hoon. Aap kaise ho?";
    } else if (userMsg.includes("gold") || userMsg.includes("market") || userMsg.includes("xauusd")) {
        reply = "Main background mein Gold ko monitor kar raha hoon. Dashboard par check karo!";
    } else if (userMsg.includes("ankit") || userMsg.includes("creator")) {
        reply = "Aap mere creator ho, Ankit. Main abhi thoda simple hoon, par seekh raha hoon.";
    } else {
        reply = "Main abhi ek Gen-AI nahi bana hoon, isliye sab kuch nahi samajh sakta. Par main aapke liye Gold track kar raha hoon!";
    }

    res.json({ reply });
});

app.listen(3000, () => {
    console.log("\x1b[38;5;46mPKA OMNI-CORE V19.2 : GOLD-ONLY MODE ACTIVE\x1b[0m");
});
