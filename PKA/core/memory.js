// =====================================================================
// 🧠 PKA COGNITIVE MEMORY CORE : TIER-1 AGI (V3.0 HYPER-UPGRADE)
// =====================================================================

const fs = require("fs");
const path = require("path");

const filePath = path.join(__dirname, "..", "data", "memory.json");

/**
 * Memory ko initialize karna agar file exist nahi karti.
 * Isse AI crash nahi hoga pehli baar run hone par.
 */
function init() {
    if (!fs.existsSync(filePath)) {
        // Ensure "data" directory exists
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // AGI UPGRADE: Created Short-Term & Long-Term Memory
        fs.writeFileSync(filePath, JSON.stringify({
            history: [],        // Short-Term Memory (Last 50)
            longTerm: [],       // Permanent Core Beliefs & Rules
            stats: { memoriesProcessed: 0 }
        }, null, 2));
    }
}

/**
 * Memory load karna (Parsing error handling ke saath).
 */
function load() {
    init();
    try {
        const data = fs.readFileSync(filePath, "utf-8");
        let parsedData = JSON.parse(data);

        // Backward Compatibility for older state files
        if (!parsedData.longTerm) parsedData.longTerm = [];
        if (!parsedData.stats) parsedData.stats = { memoriesProcessed: 0 };

        return parsedData;
    } catch (error) {
        console.error("❌ [CRITICAL] Memory Load Error:", error);
        return { history: [], longTerm: [], stats: { memoriesProcessed: 0 } };
    }
}

/**
 * Data ko secure tarike se file me write karna
 */
function save(data) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

/**
 * AGI UPGRADE: Text ko scan karke uski importance nikalna
 */
function analyzeImportance(text) {
    // Original keywords
    const keywords = ["profit", "loss", "trade", "buy", "sell"];
    let score = 0;

    keywords.forEach(kw => {
        if (text.toLowerCase().includes(kw)) score += 10;
    });

    // 🟢 V3 UPGRADE: Deep Contextual Scoring for Self-Coding & Forex
    const codeKeywords = ["function", "error", "bug", "syntax", "api", "node", "server", "loop", "sandbox", "crash", "compile", "script"];
    const forexKeywords = ["margin", "leverage", "stop loss", "take profit", "bullish", "bearish", "volatility", "pips", "liquidation", "market"];
    const evolveKeywords = ["evolve", "mutate", "genetic", "iq", "intelligence", "learn", "insight", "upgrade"];

    const lowerText = text.toLowerCase();

    // Trading aur coding rules ko highest priority deni hai taaki wo long-term me jayen
    codeKeywords.forEach(kw => { if (lowerText.includes(kw)) score += 15; });
    forexKeywords.forEach(kw => { if (lowerText.includes(kw)) score += 20; });
    evolveKeywords.forEach(kw => { if (lowerText.includes(kw)) score += 25; });

    return score;
}

/**
 * Naya memory node add karna (With Consolidation Engine).
 */
function add(roleOrObject, textValue) {
    // AGI Fix: Handle both original text args AND new object args
    let role = typeof roleOrObject === "object" ? roleOrObject.role : roleOrObject;
    let text = typeof roleOrObject === "object" ? roleOrObject.text : textValue;

    if (!text) return;

    const data = load();
    const importanceScore = analyzeImportance(text);

    // 🟢 V3 UPGRADE: Auto-Tagging System (Categorize memory)
    let category = "general_chat";
    if (importanceScore >= 15) {
        if (text.toLowerCase().includes("function") || text.toLowerCase().includes("error")) category = "code_memory";
        else if (text.toLowerCase().includes("profit") || text.toLowerCase().includes("trade") || text.toLowerCase().includes("margin")) category = "trade_rule";
        else category = "evolution_insight";
    }

    // Create Neural Memory Node
    const memoryNode = {
        id: `MEM-${Date.now()}`,
        role: role,
        text: text,
        importance: importanceScore,
        category: category, 
        time: new Date().toLocaleString() // Readable time
    };

    data.history.push(memoryNode);
    data.stats.memoriesProcessed++;

    // 🧠 AGI Optimization: Memory ko bahut bada hone se bachana
    if (data.history.length > 50) {
        // Puraani memory nikalna
        const overflowMemories = data.history.slice(0, data.history.length - 50);

        // Jo last 50 hain, unhe waise hi rakhna
        data.history = data.history.slice(-50);

        // 🧬 Memory Consolidation: Agar purani memory kaam ki hai, toh LongTerm me daalo
        overflowMemories.forEach(mem => {
            if (mem.importance >= 10) {
                data.longTerm.push(mem);
                console.log(`🌌 [MEMORY CONSOLIDATED] High-Value Intel Saved: [${mem.category.toUpperCase()}]`);
            }
        });
    }

    // Long-term memory storage limit (prevents infinite growth)
    if (data.longTerm.length > 500) {
        data.longTerm = data.longTerm.slice(-500);
    }

    save(data);
}

/**
 * Brain ke liye context nikalna (Last 5 conversation turns).
 */
function getContext(limit = 5) {
    const data = load();
    const recentContext = data.history.slice(-limit);

    // Brain ko clean string format pass karna
    return recentContext.map(mem => `${mem.role.toUpperCase()}: ${mem.text}`).join("\n");
}

/**
 * AGI NEW FEATURE: Long-Term Memory (LTM) Retrieval
 */
function getCoreBeliefs(limit = 5) {
    const data = load();
    if (data.longTerm.length === 0) return "No long-term memories formed yet.";

    const coreMemories = data.longTerm.slice(-limit);
    return coreMemories.map(mem => mem.text).join(" | ");
}

// =========================================================
// 🟢 V3 EXCLUSIVE UPGRADES FOR SELF-EVOLVING/TRADING AGI
// =========================================================

/**
 * @description Smart Context Retrieval (Pseudo-RAG). PKA sirf current baat se judi purani baatein yaad karega.
 */
function getRelevantBeliefs(queryText, limit = 5) {
    const data = load();
    if (data.longTerm.length === 0) return getCoreBeliefs(limit); 

    const queryWords = queryText.toLowerCase().split(/\s+/);

    // Har memory ko score do ki wo current baat se kitni match karti hai
    let scoredMemories = data.longTerm.map(mem => {
        let matchScore = 0;
        const memText = mem.text.toLowerCase();
        queryWords.forEach(w => {
            if (w.length > 4 && memText.includes(w)) matchScore++;
        });
        // High importance memories ko priority do
        return { ...mem, finalScore: matchScore + (mem.importance * 0.1) };
    });

    // Best matches filter karo
    let relevant = scoredMemories.filter(m => m.finalScore > 0).sort((a, b) => b.finalScore - a.finalScore);

    // Agar kuch specific na mile, toh general latest baatein dikhao
    if (relevant.length === 0) return getCoreBeliefs(limit);

    return relevant.slice(0, limit).map(mem => `[${mem.category.toUpperCase()}]: ${mem.text}`).join(" | ");
}

/**
 * @description Direct injection method. Jab brain.js naya code ya trading rule banaye, toh bina wait kiye sidha Permanent Memory me lock kar do.
 */
function injectSkill(skillText, category = "hardcoded_skill") {
    const data = load();
    const memoryNode = {
        id: `SKILL-${Date.now()}`,
        role: "system",
        text: skillText,
        importance: 999, // God-tier importance so it never deletes
        category: category,
        time: new Date().toLocaleString()
    };
    data.longTerm.push(memoryNode);
    console.log(`⚡ [SKILL INJECTED] Permanent Node Created in DNA: ${category.toUpperCase()}`);
    save(data);
}

// Module exports update karke naye functions expose kar diye gaye hain
module.exports = { add, load, getContext, getCoreBeliefs, getRelevantBeliefs, injectSkill };
